import string
import textwrap
import secrets

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext as _

from appliances.models import Appliance
from pin_codes.models import PinCode, TimeSlot
from users.models import CustomUser


class Appointment(models.Model):
    appliance = models.ForeignKey(Appliance, on_delete=models.CASCADE)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)

    address = models.CharField(max_length=4096)
    place_id = models.CharField(
        null=True, blank=True, max_length=32, help_text=_("Google Maps Place ID")
    )

    pin_code = models.ForeignKey(PinCode, on_delete=models.CASCADE)
    weekday = models.CharField(max_length=8, choices=PinCode.WEEKDAY_CHOICES)
    time_slot = models.ForeignKey(TimeSlot, on_delete=models.CASCADE)

    reason = models.CharField(max_length=4096)
    created_at = models.DateTimeField(auto_now_add=True)
    tracking_number = models.CharField(max_length=255, unique=True)

    is_cancelled = models.BooleanField(default=False)
    status = models.CharField(max_length=4096, default="Pending")

    @classmethod
    def gen_tracking_number(cls):
        return "".join(secrets.choice(string.digits) for _ in range(10))

    def validate_time_slot(self):
        if self.time_slot not in self.pin_code.time_slots.all():
            raise ValidationError(_("Invalid Time Slot"), code="invalid_time_slot")

    def validate_weekday(self):
        if self.weekday not in self.pin_code.working_days:
            raise ValidationError(_("Invalid Week Day"), code="invalid_weekday")

    def clean_fields(self, exclude=None):
        super().clean_fields(exclude)

        if "time_slot" not in exclude:
            self.validate_time_slot()

        if "weekday" not in exclude:
            self.validate_time_slot()

    @property
    def short_detail_markup(self):
        return _(
            textwrap.dedent(
                f"""
                Appointment for {self.appliance.product_line.name}
                 
                Serial Number ➙ {self.appliance.serial_number}            
                Time Slot ➙ {PinCode.WEEKDAY_CHOICES_DICT[self.weekday]}, {self.time_slot}
                Tracking Number ➙ `{self.tracking_number}`            
                """
            )
        )

    @property
    def full_detail_markup(self):
        return _(
            textwrap.dedent(
                f"""
                Appointment for {self.appliance.product_line.name}
                
                Status ➙ {self.status}
                Time of booking ➙ {self.created_at.strftime("%a %B %d %Y %-I:%-M %p")}
                Serial No. ➙ {self.appliance.serial_number}
                Model No. ➙ {self.appliance.model_number}
                Pin Code ➙ {self.pin_code}
                Address ➙ {self.address}
                Time Slot ➙ {PinCode.WEEKDAY_CHOICES_DICT[self.weekday]}, {self.time_slot}
                Reason ➙ {self.reason}                
                Tracking No. ➙ `{self.tracking_number}`
                """
            )
        )

    def __str__(self):
        return f"Appointment for {self.user.first_name}'s {self.appliance.product_line}"
