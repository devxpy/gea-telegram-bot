import json

from django import forms
from django.core import checks
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext as _


class TimeSlot(models.Model):
    start = models.TimeField()
    end = models.TimeField()

    class Meta:
        unique_together = (("start", "end"),)

    def __str__(self):
        return f"{self.start.strftime('%-I %p')} - {self.end.strftime('%-I %p')}"


class MultipleChoiceCharField(models.CharField):
    description = _("Stores multiple choices in a CharField")

    def __init__(self, min_choices=None, max_choices=None, *args, **kwargs):
        self.min_choices, self.max_choices = min_choices, max_choices

        kwargs["max_length"] = len(
            json.dumps([i[0] for i in kwargs.get("choices", ())])
        )

        super().__init__(*args, **kwargs)

        def validate_min_choices(value):
            if len(value) < self.min_choices:
                raise ValidationError(
                    _("You must select a minimum of %(num)s choices"),
                    params={"num": self.min_choices},
                    code="min_choices",
                )

        def validate_max_choices(value):
            if len(value) > self.max_choices:
                raise ValidationError(
                    _("You must select a maximum of %(num)s choices"),
                    params={"num": self.max_choices},
                    code="max_choices",
                )

        if self.min_choices is not None:
            self.validators.append(validate_min_choices)
        if self.max_choices is not None:
            self.validators.append(validate_max_choices)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()

        if self.min_choices is not None:
            kwargs["min_choices"] = self.min_choices
        if self.max_choices is not None:
            kwargs["max_choices"] = self.max_choices

        del kwargs["max_length"]

        return name, path, args, kwargs

    def check(self, **kwargs):
        return [*super().check(**kwargs), *self._check_defaults()]

    def _check_choices(self):
        if not self.choices:
            return [
                checks.Error(
                    "MultipleChoiceCharFields must define a 'choices' attribute.",
                    obj=self,
                    id="multiplechoicecharfield.E001",
                )
            ]
        return super()._check_choices()

    def _check_defaults(self):
        if isinstance(self.default, list) or isinstance(self.default, tuple):
            return []
        return [
            checks.Error(
                f"MultipleChoiceCharField 'default' must be 'list' or 'tuple', not {type(self.default)}.",
                obj=self,
                id="multiplechoicecharfield.E002",
            )
        ]

    def get_choices(self, include_blank=False, *args, **kwargs):
        return super().get_choices(include_blank=False, *args, **kwargs)

    def validate(self, value, _):
        if not self.editable:
            # Skip validation for non-editable fields.
            return
        if self.choices and value not in self.empty_values:
            for selected in value:
                for option_key, option_value in self.choices:
                    if isinstance(option_value, (list, tuple)):
                        # This is an optgroup, so look inside the group for
                        # options.
                        for optgroup_key, optgroup_value in option_value:
                            if selected == optgroup_key:
                                break
                    elif selected == option_key:
                        break
                else:
                    raise ValidationError(
                        self.error_messages["invalid_choice"],
                        code="invalid_choice",
                        params={"value": value},
                    )

        if value is None and not self.null:
            raise ValidationError(self.error_messages["null"], code="null")

        if not self.blank and value in self.empty_values:
            raise ValidationError(self.error_messages["blank"], code="blank")

    def from_db_value(self, value, expression, connection):
        if value is None:
            return value
        return json.loads(value)

    def _get_flatchoices(self):
        return super()._get_flatchoices()

    def to_python(self, value):
        if isinstance(value, list):
            return value

        if value is None:
            return value

        try:
            return json.loads(value)
        except json.JSONDecodeError as e:
            raise ValidationError(_(e))

    def get_prep_value(self, value):
        return json.dumps(value)

    def formfield(self, **kwargs):
        defaults = {
            "choices_form_class": forms.fields.TypedMultipleChoiceField,
            "coerce": str,
            "widget": forms.widgets.CheckboxSelectMultiple,
        }
        defaults.update(kwargs)

        return super().formfield(**defaults)

    def value_to_string(self, obj):
        value = self.value_from_object(obj)
        return self.get_prep_value(value)


class PinCode(models.Model):
    MON = "0"
    TUE = "1"
    WED = "2"
    THU = "3"
    FRI = "4"
    SAT = "5"
    SUN = "6"

    WEEKDAY_CHOICES = (
        (MON, _("Monday")),
        (TUE, _("Tuesday")),
        (WED, _("Wednesday")),
        (THU, _("Thursday")),
        (FRI, _("Friday")),
        (SAT, _("Saturday")),
        (SUN, _("Sunday")),
    )

    WEEKDAY_CHOICES_DICT = dict(WEEKDAY_CHOICES)

    pin_code = models.CharField(max_length=255, unique=True)
    time_slots = models.ManyToManyField(TimeSlot)

    working_days = MultipleChoiceCharField(
        choices=WEEKDAY_CHOICES, default=[MON, TUE, WED, THU, FRI]
    )

    def __str__(self):
        return self.pin_code
