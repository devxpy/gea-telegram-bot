from django.contrib import admin

from . import models


@admin.register(models.ProductLine)
class ProductLineAdmin(admin.ModelAdmin):
    pass


@admin.register(models.Appliance)
class ApplianceAdmin(admin.ModelAdmin):
    list_display = ("serial_number", "model_number", "product_line")
    list_filter = ("product_line",)
