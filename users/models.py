import phonenumbers
from django.contrib.auth.models import AbstractUser
from phonenumber_field.modelfields import PhoneNumberField


class CustomUser(AbstractUser):
    phone_number = PhoneNumberField(max_length=255, blank=True)

    def get_username(self):
        return (
            str(
                phonenumbers.format_number(
                    self.phone_number, phonenumbers.PhoneNumberFormat.INTERNATIONAL
                )
            )
            if self.phone_number
            else self.username
        )

    def __str__(self):
        return self.get_full_name() or self.get_username()
