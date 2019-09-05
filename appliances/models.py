from django.db import models
from django.utils.translation import gettext as _


class ProductLine(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"<ProductLine {repr(self.name)}>"


class Appliance(models.Model):
    serial_number = models.CharField(max_length=255, unique=True)
    product_line = models.ForeignKey(ProductLine, on_delete=models.CASCADE)
    model_number = models.CharField(max_length=255)
    name = models.CharField(_("Appliance Name"), max_length=255)

    def __str__(self):
        return self.serial_number

    def __repr__(self):
        return f"<Appliance Serial no.: {repr(self.serial_number)} Product line:{repr(self.product_line.name)}>"
