from django.contrib import admin

from pin_codes.models import TimeSlot, PinCode


@admin.register(TimeSlot)
class TimeSlotAdmin(admin.ModelAdmin):
    pass


@admin.register(PinCode)
class PinCodeAdmin(admin.ModelAdmin):
    pass
