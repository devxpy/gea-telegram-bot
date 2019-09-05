from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext as _

from . import models

# an href template for opening a link in a new tab
NEW_LINK_HREF_TEMPLATE = (
    '<a href="{}" target="_blank" style="font-size: large; border: 1px solid;">⬈</a>'
)


@admin.register(models.Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    fields = (
        "appliance",
        "user",
        "address",
        "get_location_href",
        "pin_code",
        "weekday",
        "time_slot",
        "reason",
        "created_at",
        "tracking_number",
        "is_cancelled",
        "status",
    )
    list_display = (
        "__str__",
        "appliance",
        "user",
        "pin_code",
        "created_at",
        "is_cancelled",
        "status",
    )
    list_filter = ("pin_code__pin_code", "created_at")

    ordering = ("-created_at",)
    readonly_fields = ("created_at", "get_location_href")

    def get_location_href(self, obj) -> str:
        """Returns the html href tag for viewing the location of this user on Google Maps."""

        if obj.place_id:
            return format_html(
                NEW_LINK_HREF_TEMPLATE,
                f"https://www.google.com/maps/place/?q=place_id:{obj.place_id}",
            )
        else:
            return "---"

    get_location_href.short_description = _("Google Maps")
