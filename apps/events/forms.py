from colorfield.widgets import ColorWidget
from django import forms
from django.utils.translation import gettext_lazy as _

from .models import Event, EventFeature


class EventUserForm(forms.ModelForm):
    """
    Formulario asociado a la creación y edición de los eventos por parte de la empresa cliente.
    Indica los campos a visualizar así como los estilos de cada uno.
    """

    class Meta:
        model = EventFeature
        fields = [
            "event",
            "alias",
            "company",
            "central_alarm",
            "user_alarm",
            "start_time",
            "end_time",
            "color",
            "email_alarm",
            "alarm_sound",
            "sound_priority",
            "type_alarm_sound",
        ]
        widgets = {
            "event": forms.Select(
                attrs={
                    "class": "form-control",
                    "autocomplete": "off",  
                }
            ),
            "alias": forms.TextInput(
                attrs={
                    "class": "form-control form-control-lg",
                    "aria-label": ".form-control-lg example",
                    "style": "padding-top: 11px; padding-bottom: 5px;",
                    "autocomplete": "off",  
                }
            ),
            "company": forms.Select(
                attrs={
                    "class": "form-control",
                    "autocomplete": "off",  
                }
            ),
            "central_alarm": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input",
                    "autocomplete": "off",  
                }
            ),
            "user_alarm": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input",
                    "autocomplete": "off",  
                }
            ),
            "email_alarm": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input",
                    "autocomplete": "off",  
                }
            ),
            "start_time": forms.TimeInput(
                attrs={
                    "class": "form-control",
                    "disabled": "disabled",
                    "type": "time",
                    "autocomplete": "off",  
                }
            ),
            "end_time": forms.TimeInput(
                attrs={
                    "class": "form-control",
                    "disabled": "disabled",
                    "type": "time",
                    "autocomplete": "off",  
                }
            ),
            "alarm_sound": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input",
                    "onclick": "activate(this)",
                    "autocomplete": "off",  
                }
            ),
            "sound_priority": forms.Select(
                attrs={
                    "class": "form-control",
                    "disabled": "enabled",
                    "autocomplete": "off",  
                }
            ),
            "type_alarm_sound": forms.Select(
                attrs={
                    "class": "form-control",
                    "disabled": "enabled",
                    "autocomplete": "off",  
                }
            ),
            "color": ColorWidget(
                attrs={
                    "class": "form-control",
                    "disabled": "enabled",
                    "autocomplete": "off",  
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["color"].widget = ColorWidget()
        self.fields["color"].widget.attrs["disabled"] = "disabled"

    def clean_alarm_sound(self):
        alarm_sound = self.cleaned_data.get("alarm_sound")
        if alarm_sound:
            self.fields["color"].widget.attrs.pop("disabled", None)
        else:
            self.fields["color"].widget.attrs["disabled"] = "disabled"
        return alarm_sound

    def clean_event(self):
        event = self.cleaned_data.get("event")
        try:
            if event is None:
                raise Exception
        except Exception:
            raise forms.ValidationError(_("You must select an event!!"))
        return event

    def clean_user_alarm(self):
        """
        Función que implementa la validación que impide enviar un formulario sin especificar
        un receptor de notificación. Eleva un ValidationError.
        """
        user_alarm = self.cleaned_data.get("user_alarm")
        return user_alarm

    def clean_end_time(self):
        end_time = self.cleaned_data.get("end_time")
        start_time = self.cleaned_data.get("start_time")
        try:
            if end_time is not None and start_time is not None:
                if end_time < start_time:
                    raise Exception
        except Exception:
            raise forms.ValidationError(
                _("The end time must be later than the start time")
            )
        return end_time


class EventForm(forms.ModelForm):
    """
    Formulario asociado a la creación y edición de los eventos predefinidospor parte de la
    AZ-Smart. Indica los campos a visualizar así como los estilos de cada uno.
    """

    class Meta:
        model = Event
        fields = ("name", "number")
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "number": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "type": "number",
                    "min": "1",
                    "max": "10000",
                    "autocomplete": "off",
                }
            ),
        }

    def clean_number(self):
        number = self.cleaned_data["number"]
        if Event.objects.filter(number=number).exists():
            raise forms.ValidationError(_("An event with this number already exists"))
        return number

    def clean_name(self):
        name = self.cleaned_data["name"]
        if Event.objects.filter(name=name).exists():
            raise forms.ValidationError(_("An event with this name already exists"))
        return name
