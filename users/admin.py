from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from . import models


@admin.register(models.CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ("__str__", "phone_number", "email", "is_staff")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fieldsets[1][1]["fields"] += ("phone_number",)
