import secrets
from functools import wraps
from typing import Tuple, Dict, Callable

import googlemaps
import telegram as tg
from django import db
from django.utils.translation import gettext as T
from telegram.ext import ConversationHandler

from gea_bot import settings
from pin_codes.models import PinCode
from users.models import CustomUser

gmaps = googlemaps.Client(key=settings.GOOGLE_MAPS_API_TOKEN)


def reverse_geocode(coordinates: Dict[str, float]) -> Tuple[str, str, PinCode]:
    details = gmaps.reverse_geocode(
        (coordinates["latitude"], coordinates["longitude"])
    )[0]
    pin_code = [
        i["long_name"]
        for i in details["address_components"]
        if "postal_code" in i["types"]
    ][0]

    return details["formatted_address"], details["place_id"], pin_code


def get_user(up: tg.Update) -> CustomUser:
    user_detail = up.effective_user
    try:
        user = CustomUser.objects.get(username=str(user_detail.id))
    except CustomUser.DoesNotExist:
        user = CustomUser(
            first_name=user_detail.first_name,
            last_name=user_detail.last_name,
            username=str(user_detail.id)
        )
        user.save()
    if not user.password:
        user.set_unusable_password()
    return user


def login_required(fn):
    @wraps(fn)
    @ensure_db_cleanup
    def wrapper(bot, up: tg.Update, *args, **kwargs):
        user_detail = up.effective_user
        try:
            user = CustomUser.objects.get(username=str(user_detail.id))
        except CustomUser.DoesNotExist:
            pass
        else:
            if user.phone_number and user.email:
                return fn(bot, up, *args, **kwargs)

        up.effective_message.reply_text(
            T("You aren't registered with us!\nType in /start to register.")
        )
        return ConversationHandler.END

    return wrapper


def request_phone_number(up: tg.Update, text: str) -> tg.Message:
    keyboard_markup = [
        [tg.KeyboardButton(text=T("Share Contact"), request_contact=True)]
    ]
    reply_markup = tg.ReplyKeyboardMarkup(keyboard_markup)

    return up.effective_message.reply_text(text=text, reply_markup=reply_markup)


def get_pretty_time_slot(weekday_id, time_slot):
    return T(f"{PinCode.WEEKDAY_CHOICES_DICT[weekday_id]}, {time_slot}")


def get_time_slot_keyboard(
    pin_code: PinCode, callback_pattern: str = ""
) -> tg.InlineKeyboardMarkup:
    return tg.InlineKeyboardMarkup(
        [
            [
                tg.InlineKeyboardButton(
                    get_pretty_time_slot(weekday_id, time_slot),
                    callback_data=f"{callback_pattern}{weekday_id}:{time_slot.pk}",
                )
            ]
            for weekday_id in pin_code.working_days
            for time_slot in pin_code.time_slots.all()
        ]
    )


def ensure_db_cleanup(fn: Callable):
    """Ensures that database connection is correctly cleaned up."""

    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        finally:
            db.connection.close()

    return wrapper
