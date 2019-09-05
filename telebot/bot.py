import logging
import textwrap
import traceback
from functools import wraps
from typing import Callable

import googlemaps
import telegram as tg
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as T
from telegram.ext import (
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    CallbackQueryHandler,
    Updater,
    Filters,
)

import telebot.util as util
from appliances.models import Appliance
from appointments.models import Appointment
from gea_bot import settings
from pin_codes.models import PinCode, TimeSlot

updater = Updater(token=settings.TELEGRAM_API_TOKEN)
dispatcher = updater.dispatcher

HELP = T(
    textwrap.dedent(
        """
        Here is how you can use me:
            
        ↯ /help  
            Show this help.
        
        ↯ /book  
            Book a new Appointment.
        
        ↯ /list  
            List all previous Appointments.
        
        ↯ /check `<Tracking no.>`  
            Check the details for an Appointment.
        
        ↯ /cancel `<Tracking no.>`  
            Cancel an appointment.
                
        ↯ /schedule `<Tracking no.>`
            Reschedule an appointment.          
        
        ↯ /abort 
            Abort an ongoing conversation.
        """
    )
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)


def show_help(_, up: tg.Update):
    up.effective_message.reply_text(text=HELP, parse_mode="Markdown")


dispatcher.add_handler(CommandHandler("help", show_help))


def abort(_, up: tg.Update):
    up.effective_message.reply_text("Aborted!")
    return ConversationHandler.END


ABORT = CommandHandler("abort", abort)


@util.ensure_db_cleanup
def start(_, up: tg.Update):
    user = util.get_user(up)

    if user.phone_number and user.email:
        up.effective_message.reply_text(f"Welcome back {user.first_name}!")
        show_help(_, up)

        return ConversationHandler.END

    up.effective_message.reply_text(
        T(f"Welcome {user.first_name}!\nLet's get you started.")
    )
    util.request_phone_number(
        up, T("First, could you please provide me your Phone Number?")
    )

    return recv_phone_number.__name__


@util.ensure_db_cleanup
def recv_phone_number(_, up: tg.Update, chat_data: dict):
    message: tg.Message = up.effective_message
    user = util.get_user(up)

    try:
        user.phone_number = message.contact.phone_number
    except AttributeError:
        user.phone_number = message.text
    try:
        user.clean_fields()
    except ValidationError:
        util.request_phone_number(
            up,
            T(
                "You entered an invalid Phone Number.\n"
                "Please enter a valid Phone Number."
            ),
        )

        return recv_phone_number.__name__

    chat_data["user"] = user
    up.effective_message.reply_text(
        text=T(
            "Thanks for the Phone Number.\n"
            "One last thing, can you please provide me with your Email Address?"
        ),
        reply_markup=tg.replykeyboardremove.ReplyKeyboardRemove(),
    )

    return recv_email.__name__


@util.ensure_db_cleanup
def recv_email(bot, up: tg.Update, chat_data):
    user = chat_data["user"]
    user.email = up.effective_message.text

    try:
        user.clean_fields()
    except ValidationError:
        up.effective_message.reply_text(
            T(
                "You entered an invalid Email Address.\n"
                "Please enter a valid Email Address."
            )
        )

        return recv_email.__name__

    user.save()
    up.effective_message.reply_text(T("Thanks for the email. You're all set-up now."))
    show_help(bot, up)

    return ConversationHandler.END


dispatcher.add_handler(
    ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            recv_phone_number.__name__: [
                MessageHandler(Filters.contact, recv_phone_number, pass_chat_data=True),
                MessageHandler(Filters.text, recv_phone_number, pass_chat_data=True),
            ],
            recv_email.__name__: [
                MessageHandler(Filters.text, recv_email, pass_chat_data=True)
            ],
        },
        fallbacks=[ABORT, CommandHandler("start", start)],
    )
)


@util.login_required
def book(_, up: tg.Update):
    up.effective_message.reply_text(
        T(
            "Alright, let's book an Appointment.\n\n"
            "First, enter the serial number of your Appliance:\n\n"
            "(Case insensitive)"
        )
    )

    return recv_serial_number.__name__


@util.login_required
def recv_serial_number(_, up: tg.Update, chat_data):
    serial_number = up.effective_message.text.strip()

    try:
        appliance = Appliance.objects.get(serial_number__iexact=serial_number)

        chat_data["appointment"] = Appointment(
            appliance=appliance,
            user=util.get_user(up),
            tracking_number=Appointment.gen_tracking_number(),
        )
        up.effective_message.reply_text(
            T(
                "Checks out!\n"
                "Next, provide an address for this service appointment.\n\n"
                "You can also share your location, using the attach (📎) button."
            )
        )

        return recv_location.__name__
    except Appliance.DoesNotExist:
        up.effective_message.reply_text(
            T(
                "You entered an invalid serial number.\n"
                "Please enter a valid serial number."
            )
        )

        return recv_serial_number.__name__


@util.login_required
def recv_location(_, up: tg.Update, chat_data: dict):
    coordinates = up.effective_message.location
    appointment = chat_data["appointment"]

    if coordinates is None:
        address = up.effective_message.text.strip()
        appointment.address = address

        up.effective_message.reply_text(
            T("Please enter the pin code for this address.")
        )

        return recv_pincode.__name__

    progress_msg: tg.Message = up.effective_message.reply_text("Retrieving address...")

    try:
        address, place_id, pin_code = util.reverse_geocode(coordinates)
    except (IndexError, KeyError):
        progress_msg.edit_text("Invalid location!\nPlease enter a valid location.")
        return recv_location.__name__
    except googlemaps.exceptions.Timeout as e:
        traceback.print_exc()
        up.effective_message.reply_text(
            T(
                "Sorry, but I couldn't fetch your location.\n"
                "Can you please enter your Address manually?"
            )
        )
        return recv_location.__name__

    try:
        pin_code = PinCode.objects.get(pin_code=pin_code)
    except PinCode.DoesNotExist:
        progress_msg.edit_text(
            T(
                f"We don't have any technicians available at this pin code ({pin_code})!\n"
                "Sorry for the inconvenience."
            )
        )
        return ConversationHandler.END

    appointment.address = address
    appointment.pin_code = pin_code
    appointment.place_id = place_id

    progress_msg.edit_text(f"Please enter the reason for this service appointment.")

    return recv_reason.__name__


@util.login_required
def recv_pincode(_, up: tg.Update, chat_data: dict):
    pin_code = up.effective_message.text.strip()

    try:
        pin_code = PinCode.objects.get(pin_code=pin_code)
    except PinCode.DoesNotExist:
        up.effective_message.reply_text(
            T(
                f"We don't have any technicians available at this Pin Code!\n"
                "Sorry for the inconvenience."
            )
        )
        return ConversationHandler.END

    appointment = chat_data["appointment"]
    appointment.pin_code = pin_code

    up.effective_message.reply_text(
        f"Please enter the reason for this service appointment."
    )

    return recv_reason.__name__


@util.login_required
def recv_reason(_, up: tg.Update, chat_data):
    appointment = chat_data["appointment"]
    appointment.reason = up.effective_message.text.strip()

    up.effective_message.reply_text(
        T(f"Please choose a time slot for this booking."),
        reply_markup=util.get_time_slot_keyboard(appointment.pin_code),
    )

    return recv_time_slot.__name__


@util.login_required
def recv_time_slot(_, up: tg.Update, chat_data: dict):
    query: tg.CallbackQuery = up.callback_query

    weekday_id, time_slot_pk = query.data.split(":")

    appointment = chat_data["appointment"]
    appointment.weekday = weekday_id
    appointment.time_slot = TimeSlot.objects.get(pk=time_slot_pk)

    try:
        appointment.validate_time_slot()
        appointment.validate_weekday()
    except ValidationError:
        try:
            up.effective_message.edit_text(
                T(
                    "You entered an invalid time slot.\n"
                    "Please choose a valid time slot."
                ),
                reply_markup=util.get_time_slot_keyboard(appointment.pin_code),
            )
        except tg.error.BadRequest:
            query.answer()

        return recv_time_slot.__name__

    appointment.save()

    reply_markup = tg.InlineKeyboardMarkup(
        [
            [
                tg.InlineKeyboardButton(
                    text=T("Cancel"),
                    callback_data=f"{hyperlink.__name__}{cancel.__name__}:{appointment.pk}",
                ),
                tg.InlineKeyboardButton(
                    text=T("Check details"),
                    callback_data=f"{hyperlink.__name__}{check.__name__}:{appointment.pk}",
                ),
                tg.InlineKeyboardButton(
                    text=T("Reschedule"),
                    callback_data=f"{hyperlink.__name__}{schedule.__name__}:{appointment.pk}",
                ),
            ]
        ]
    )

    up.effective_message.reply_text(
        T(
            f"Appointment scheduled for {util.get_pretty_time_slot(appointment.weekday, appointment.time_slot)}.\n\n"
            f"Tracking No. for this appointment:\n\n"
            f"`{appointment.tracking_number}`\n\n"
            f"(Long press to copy)"
        ),
        parse_mode="Markdown",
        reply_markup=reply_markup,
    )

    return ConversationHandler.END


dispatcher.add_handler(
    ConversationHandler(
        entry_points=[CommandHandler("book", book)],
        states={
            recv_serial_number.__name__: [
                MessageHandler(Filters.text, recv_serial_number, pass_chat_data=True)
            ],
            recv_location.__name__: [
                MessageHandler(Filters.location, recv_location, pass_chat_data=True),
                MessageHandler(Filters.text, recv_location, pass_chat_data=True),
            ],
            recv_pincode.__name__: [
                MessageHandler(Filters.text, recv_pincode, pass_chat_data=True)
            ],
            recv_reason.__name__: [
                MessageHandler(Filters.text, recv_reason, pass_chat_data=True)
            ],
            recv_time_slot.__name__: [
                CallbackQueryHandler(recv_time_slot, pass_chat_data=True)
            ],
        },
        fallbacks=[ABORT, CommandHandler("book", book)],
    )
)


@util.login_required
def hyperlink(bot: tg.Bot, up: tg.Update, chat_data: dict):
    query: tg.CallbackQuery = up.callback_query
    fn_name, appointment_pk = query.data[len(hyperlink.__name__) :].split(":")

    try:
        fn = HYPERLINK_MAP[fn_name]
    except KeyError:
        up.effective_message.reply_text(T("Invalid Hyperlink!"))
    else:
        try:
            chat_data["appointment"] = Appointment.objects.get(
                pk=int(appointment_pk), is_cancelled=False
            )
        except Appointment.DoesNotExist:
            up.effective_message.reply_text(T("Invalid Appointment!"))
        else:
            fn(bot, up, chat_data)
        finally:
            query.answer()


dispatcher.add_handler(
    CallbackQueryHandler(hyperlink, pass_chat_data=True, pattern=hyperlink.__name__)
)


def show_list(_, up: tg.Update):
    appointments = util.get_user(up).appointment_set.exclude(is_cancelled=True)

    if not appointments.exists():
        up.effective_message.reply_text(
            T(
                "You haven't booked any appointments yet!\n"
                "Use /book to book a service appointment."
            )
        )
        return

    up.effective_message.reply_text(
        T("Here is a list of all your previous appointments.")
    )
    for appointment in appointments:
        reply_markup = tg.InlineKeyboardMarkup(
            [
                [
                    tg.InlineKeyboardButton(
                        text=T("Cancel"),
                        callback_data=f"{hyperlink.__name__}{cancel.__name__}:{appointment.pk}",
                    ),
                    tg.InlineKeyboardButton(
                        text=T("Check details"),
                        callback_data=f"{hyperlink.__name__}{check.__name__}:{appointment.pk}",
                    ),
                    tg.InlineKeyboardButton(
                        text=T("Reschedule"),
                        callback_data=f"{hyperlink.__name__}{schedule.__name__}:{appointment.pk}",
                    ),
                ]
            ]
        )

        up.effective_message.reply_text(
            text=appointment.short_detail_markup,
            reply_markup=reply_markup,
            parse_mode="Markdown",
        )


dispatcher.add_handler(CommandHandler("list", show_list))


def create_appointment_modification_command(fn: Callable):
    @wraps(fn)
    @util.login_required
    def wrapper(bot: tg.Bot, up: tg.Update, *args, **kwargs):
        chat_data = kwargs.pop("chat_data")
        cmd_args = kwargs.pop("args", None)

        if cmd_args is None:
            tracking_number = up.effective_message.text.strip()
        else:
            tracking_number = " ".join(cmd_args).strip()

        if not tracking_number:
            up.effective_message.reply_text(
                T("Please enter a tracking number:\n\n(Case insensitive)")
            )
            return fn.__name__

        try:
            chat_data["appointment"] = Appointment.objects.get(
                tracking_number__iexact=tracking_number, is_cancelled=False
            )
        except Appointment.DoesNotExist:
            up.effective_message.reply_text(
                T(
                    f"You entered an invalid tracking number.\n\n"
                    "Please enter a valid tracking number:"
                ),
                parse_mode="Markdown",
            )
            return fn.__name__
        else:
            return fn(bot, up, *args, **kwargs, chat_data=chat_data)

    return (
        CommandHandler(fn.__name__, wrapper, pass_args=True, pass_chat_data=True),
        MessageHandler(Filters.text, wrapper, pass_chat_data=True),
    )


@util.login_required
def schedule(_, up: tg.Update, chat_data: dict):
    appointment = chat_data["appointment"]

    up.effective_message.reply_text(
        T(f"Please choose the new time slot for this booking."),
        reply_markup=util.get_time_slot_keyboard(
            appointment.pin_code, callback_pattern=recv_new_time_slot.__name__
        ),
    )

    return ConversationHandler.END


schedule_handler1, schedule_handler2 = create_appointment_modification_command(schedule)
dispatcher.add_handler(
    ConversationHandler(
        entry_points=[schedule_handler1],
        states={schedule.__name__: [schedule_handler2]},
        fallbacks=[ABORT, schedule_handler1],
    )
)


@util.login_required
def recv_new_time_slot(_, up: tg.Update, chat_data: dict):
    query: tg.CallbackQuery = up.callback_query

    weekday_id, time_slot_pk = query.data[len(recv_new_time_slot.__name__) :].split(":")

    appointment = chat_data["appointment"]
    appointment.weekday = weekday_id
    appointment.time_slot = TimeSlot.objects.get(pk=time_slot_pk)

    try:
        appointment.validate_time_slot()
        appointment.validate_weekday()
    except ValidationError:
        try:
            up.effective_message.edit_text(
                T(
                    "You entered an invalid Time slot.\n"
                    "Please choose a valid time slot."
                ),
                reply_markup=util.get_time_slot_keyboard(
                    appointment.pin_code, callback_pattern=recv_new_time_slot.__name__
                ),
            )
        except tg.error.BadRequest:
            query.answer()
    else:
        appointment.save()
        up.effective_message.edit_text(
            text=T(
                f"Appointment rescheduled for {util.get_pretty_time_slot(appointment.weekday, appointment.time_slot)}."
            )
        )


dispatcher.add_handler(
    CallbackQueryHandler(
        recv_new_time_slot, pass_chat_data=True, pattern=recv_new_time_slot.__name__
    )
)


def check(_: tg.Bot, up: tg.Update, chat_data: dict):
    appointment = chat_data["appointment"]

    reply_markup = tg.InlineKeyboardMarkup(
        [
            [
                tg.InlineKeyboardButton(
                    text="Cancel",
                    callback_data=f"{hyperlink.__name__}{cancel.__name__}:{appointment.pk}",
                ),
                tg.InlineKeyboardButton(
                    text=T("Reschedule"),
                    callback_data=f"{hyperlink.__name__}{schedule.__name__}:{appointment.pk}",
                ),
            ]
        ]
    )
    up.effective_message.reply_text(
        text=appointment.full_detail_markup,
        parse_mode="Markdown",
        reply_markup=reply_markup,
    )

    return ConversationHandler.END


check_handler1, check_handler2 = create_appointment_modification_command(check)
dispatcher.add_handler(
    ConversationHandler(
        entry_points=[check_handler1],
        states={check.__name__: [check_handler2]},
        fallbacks=[ABORT, check_handler1],
    )
)


@util.login_required
def cancel(_, up: tg.Update, __):
    keyboard = tg.InlineKeyboardMarkup(
        [
            [
                tg.InlineKeyboardButton(
                    T("Yes"), callback_data=f"{cancel_confirm.__name__}1"
                ),
                tg.InlineKeyboardButton(
                    T("No"), callback_data=f"{cancel_confirm.__name__}0"
                ),
            ]
        ]
    )
    up.effective_message.reply_text(
        text=T("Are you sure you want to cancel this appointment?"),
        reply_markup=keyboard,
    )

    return ConversationHandler.END


cancel_handler1, cancel_handler2 = create_appointment_modification_command(cancel)
dispatcher.add_handler(
    ConversationHandler(
        entry_points=[cancel_handler1],
        states={cancel.__name__: [cancel_handler2]},
        fallbacks=[ABORT, cancel_handler1],
    )
)


@util.login_required
def cancel_confirm(_, up: tg.Update, chat_data: dict):
    query: tg.CallbackQuery = up.callback_query

    confirmation = query.data[len(cancel_confirm.__name__) :]

    if bool(int(confirmation)):
        appointment = chat_data["appointment"]
        appointment.is_cancelled = True
        appointment.save()
        up.effective_message.edit_text(text=T("Okay, appointment cancelled."))
    else:
        up.effective_message.edit_text(text=T("Appointment cancellation Aborted!"))


dispatcher.add_handler(
    CallbackQueryHandler(
        cancel_confirm, pass_chat_data=True, pattern=cancel_confirm.__name__
    )
)

HYPERLINK_MAP = {
    check.__name__: check,
    cancel.__name__: cancel,
    schedule.__name__: schedule,
}


def nothing_to_abort(_, up: tg.Update):
    up.effective_message.reply_text("Nothing to abort.")


dispatcher.add_handler(CommandHandler("abort", nothing_to_abort))


def unknown(_, up: tg.Update):
    up.effective_message.reply_text(
        text=T("Sorry, I could not understand you.\n") + HELP, parse_mode="Markdown"
    )


dispatcher.add_handler(MessageHandler(Filters.command, unknown))
dispatcher.add_handler(MessageHandler(Filters.text, unknown))


def start_bot():
    updater.start_polling()
    # updater.idle()
