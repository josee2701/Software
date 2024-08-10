from datetime import timedelta

import pytz
from django import forms
from django.db.models import Q
from django.forms import BaseInlineFormSet, inlineformset_factory
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.events.models import Event
from apps.realtime.apis import get_user_companies
from apps.realtime.models import Device
from apps.whitelabel.models import Company

from .models import (Advanced_Analytical, CompanyScoreSetup, Driver,
                     DriverAnalytic, ItemScore, ItemScoreSetup)


class DriverForm(forms.ModelForm):
    """
    Formulario asociado a la creación de conductores, así como la edición de su
    información por parte de los usuarios distribuidores.
    """

    password = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "class": "form-control form-control-lg",
                "aria-label": ".form-control-lg example",
                "style": "padding-block-start: 11px; padding-block-end: 5px;",
                "autocomplete": "off",
            }
        ),
        required=False,  # Hacer que el campo no sea obligatorio
    )

    class Meta:
        model = Driver
        fields = [
            "company",
            "personal_identification_number",
            "first_name",
            "last_name",
            "address",
            "phone_number",
            "password",
            "date_joined",
            "is_active",
        ]
        widgets = {
            "company": forms.Select(
                attrs={
                    "class": "form-control",
                    "autocomplete": "off",
                }
            ),
            "personal_identification_number": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "autocomplete": "off",
                }
            ),
            "first_name": forms.TextInput(
                attrs={
                    "class": "form-control form-control-lg",
                    "aria-label": ".form-control-lg example",
                    "style": "padding-block-start: 11px; padding-block-end: 5px;",
                    "autocomplete": "off",
                }
            ),
            "last_name": forms.TextInput(
                attrs={
                    "class": "form-control form-control-lg",
                    "aria-label": ".form-control-lg example",
                    "style": "padding-block-start: 11px; padding-block-end: 5px;",
                    "autocomplete": "off",
                }
            ),
            "address": forms.TextInput(
                attrs={
                    "class": "form-control form-control-lg",
                    "aria-label": ".form-control-lg example",
                    "style": "padding-block-start: 11px; padding-block-end: 5px;",
                    "autocomplete": "off",
                }
            ),
            "phone_number": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "type": "number",
                    "autocomplete": "off",
                }
            ),
            "date_joined": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                    "autocomplete": "off",
                }
            ),
            "is_active": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input",
                    "autocomplete": "off",
                }
            ),
        }

    def clean_personal_identification_number(self):
        personal_id = self.cleaned_data["personal_identification_number"]

        # Verificar si ya existe un conductor con la misma identificación personal
        if Driver.objects.filter(
            personal_identification_number=personal_id, visible=True
        ).exists():
            # Si es una actualización y el valor ha cambiado
            if isinstance(self.instance, Driver) and self.instance.pk is not None:
                if personal_id != self.instance.personal_identification_number:
                    raise forms.ValidationError(
                        _("Driver with this Personal ID already exists.")
                    )
            else:  # Si es una creación
                raise forms.ValidationError(
                    _("Driver with this Personal ID already exists.")
                )

        return personal_id


class DriverAnalyticForm(forms.ModelForm):
    """
    Formulario asociado a la asignación de un conductor a un vehículo dado. Permite además la
    edición de las opciones configuradas.
    """

    class Meta:
        model = DriverAnalytic
        fields = [
            "vehicle",
            "date_joined",
            "date_leaving",
        ]
        widgets = {
            "vehicle": forms.Select(
                attrs={
                    "class": "form-control",
                    "autocomplete": "off",
                }
            ),
            "date_joined": forms.DateTimeInput(
                attrs={
                    "type": "datetime-local",
                    "class": "form-control",
                    "autocomplete": "off",
                }
            ),
            "date_leaving": forms.DateTimeInput(
                attrs={
                    "type": "datetime-local",
                    "class": "form-control",
                    "autocomplete": "off",
                }
            ),
        }

    def clean_date_joined(self):
        date_joined = self.cleaned_data.get("date_joined")
        if date_joined is not None:
            try:
                if date_joined.astimezone(pytz.utc) <= (
                    timezone.now() - timedelta(minutes=302)
                ).astimezone(pytz.utc):
                    raise forms.ValidationError(_("Date joined can't be in the past"))
            except Exception:
                raise forms.ValidationError(_("Invalid date format for date joined"))
        return date_joined

    def clean_date_leaving(self):
        date_joined = self.cleaned_data.get("date_joined")
        date_leaving = self.cleaned_data.get("date_leaving")

        if date_joined is not None and date_leaving is not None:
            try:
                if date_leaving.astimezone(pytz.utc) < date_joined.astimezone(pytz.utc):
                    raise forms.ValidationError(
                        _("Date leaving must be in the future of date joined!")
                    )
            except Exception:
                raise forms.ValidationError(_("Invalid date format for dates"))

        return date_leaving


class ItemForm(forms.ModelForm):
    class Meta:
        model = ItemScore
        fields = "__all__"


class CompanyScoreForm(forms.ModelForm):
    class Meta:
        model = CompanyScoreSetup
        fields = ["min_score", "max_score", "cotoff_date"]
        widgets = {
            "min_score": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "type": "number",
                    "min": "0",
                    "max": "999",
                    "autocomplete": "off",
                }
            ),
            "max_score": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "type": "number",
                    "min": "0.1",
                    "max": "1000",
                    "autocomplete": "off",
                }
            ),
            "cotoff_date": forms.Select(
                choices=[(day, day) for day in range(1, 32)],
                attrs={
                    "class": "form-control",
                    "autocomplete": "off",
                },
            ),
        }

    def clean_max_score(self):
        min_score = self.cleaned_data.get("min_score")
        max_score = self.cleaned_data.get("max_score")
        try:
            if min_score >= max_score:
                raise Exception
        except Exception:
            raise forms.ValidationError(
                _(
                    "The minimum score cannot be higher than or equal to the maximum score!"
                )
            )
        return max_score


class ItemScoreForm(forms.ModelForm):
    class Meta:
        model = ItemScoreSetup
        fields = [
            "points_item_score",
            "maximum_infractions",
            "subtract_points",
        ]
        widgets = {
            "points_item_score": forms.NumberInput(
                attrs={
                    "class": "form-control align-middle text-center text-sm",
                    "type": "number",
                    "disabled": "disabled",
                    "min": "0",
                    "max": "100",
                    "autocomplete": "off",
                }
            ),
            "maximum_infractions": forms.NumberInput(
                attrs={
                    "class": "form-control align-middle text-center text-sm",
                    "type": "number",
                    "disabled": "disabled",
                    "min": "0",
                    "max": "100",
                    "autocomplete": "off",
                }
            ),
            "subtract_points": forms.NumberInput(
                attrs={
                    "class": "form-control align-middle text-center text-sm",
                    "type": "number",
                    "disabled": "disabled",
                    "min": "0",
                    "max": "100",
                    "autocomplete": "off",
                }
            ),
        }


class BaseScoreFormset(BaseInlineFormSet):
    def clean(self):
        """
        Verifica que la suma de points de los items elegidos sea 100 en total
        """
        total = 0
        for form in self.forms:
            points = form.cleaned_data.get("points_item_score")
            if points is None:
                continue
            total = total + points
        if total > 100 or total < 100:
            raise forms.ValidationError(
                _(
                    "The sum of the points of the items to be rated must be equal to 100!"
                )
            )


ItemScoreFormsets = inlineformset_factory(
    CompanyScoreSetup,
    ItemScoreSetup,
    form=ItemScoreForm,
    extra=0,
    validate_max=True,
    validate_min=True,
    can_delete=False,
    formset=BaseScoreFormset,
)


class ReportDriverForm(forms.Form):
    company = forms.ModelChoiceField(
        queryset=Company.objects.filter(visible=True, actived=True),
        required=True,
        widget=forms.Select(attrs={"class": "form-control"}),
    )

    driver = forms.ModelMultipleChoiceField(
        queryset=Driver.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={"class": "form-check-start"}),
    )

    start_date = forms.DateField(
        widget=forms.DateInput(attrs={"class": "form-control", "type": "date"}),
        required=False,
    )

    end_date = forms.DateField(
        widget=forms.DateInput(attrs={"class": "form-control", "type": "date"}),
        required=False,
    )


class ReportTodayForm(forms.Form):
    Company_id = forms.ModelChoiceField(
        queryset=Company.objects.filter(visible=True, actived=True),
        required=True,
        widget=forms.Select(
            attrs={"class": "form-control", "id": "id_company", "name": "Company_id"}
        ),
    )

    Imei = forms.ModelChoiceField(
        queryset=Device.objects.none(),
        required=True,
        widget=forms.Select(
            attrs={
                "class": "form-control",
                "id": "id_Imei",
                "name": "Imei",
                "disabled": "disabled",
            }
        ),
    )

    event = forms.ModelChoiceField(
        queryset=Event.objects.none(),
        required=False,
        widget=forms.Select(
            attrs={"class": "form-control", "id": "id_event", "disabled": "disabled"}
        ),
    )

    def get_initial_start_date():
        now = timezone.now()
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
        return start_of_day.strftime("%Y-%m-%dT%H:%M")

    def get_initial_end_date():
        now = timezone.now()
        end_of_day = now.replace(hour=23, minute=59, second=59, microsecond=999999)
        return end_of_day.strftime("%Y-%m-%dT%H:%M")

    FechaInicial = forms.DateTimeField(
        label="Start date",
        initial=get_initial_start_date,
        widget=forms.DateTimeInput(
            attrs={
                "class": "form-control",
                "type": "datetime-local",
                "name": "FechaInicial",
            }
        ),
        required=True,
    )

    FechaFinal = forms.DateTimeField(
        label="Ending date",
        initial=get_initial_end_date,
        widget=forms.DateTimeInput(
            attrs={
                "class": "form-control",
                "type": "datetime-local",
                "name": "FechaFinal",
            }
        ),
        required=True,
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields["Company_id"].queryset = self.get_companies(user)

    def get_companies(self, user):
        if user.company_id == 1:
            return Company.objects.filter(visible=True, actived=True)
        else:
            provider_company_ids = Company.objects.filter(
                provider_id=user.company_id
            ).values_list("id", flat=True)
            return Company.objects.filter(
                Q(id=user.company_id) | Q(provider_id=user.company_id), visible=True
            )

    def clean_Imei(self):
        imei = self.cleaned_data.get("Imei")
        if not imei:
            raise forms.ValidationError("Debe seleccionar un vehículo.")
        return imei

class DataSemConfigurationForm(forms.ModelForm):
    """
    Formulario de planes de datos que utiliza la clase ModelForm de Django.
    La clase Meta especifica el modelo y campos, y se usan widgets para personalizar el formulario.
    """
    
    company = forms.ModelChoiceField(
        queryset=Company.objects.none(),
        widget=forms.Select(attrs={
            "class": "form-control",
            "autocomplete": "off",
        }),
        required=True
    )
    class Meta:
        model = Advanced_Analytical
        fields = [
            'user', 'workspace', 'id_workspace', 'id_report', 'report', 'coin', 'price',
            'is_report','demo'
        ]
        widgets = {
            "user": forms.Select(
                attrs={
                    "class": "form-control",
                    "autocomplete": "off",
                }
            ),
            "coin": forms.Select(
                attrs={
                    "class": "form-control",
                    "autocomplete": "off",
                }
            ),
            "price": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "type": "number",
                    "autocomplete": "off",
                }
            ),
            "id_workspace": forms.Select(
                attrs={
                    "class": "form-control",
                    "autocomplete": "off",
                }
            ),
            "id_report": forms.Select(
                attrs={
                    "class": "form-control",
                    "autocomplete": "off",
                }
            ),
            "report": forms.Select(
                attrs={
                    "class": "form-control",
                    "autocomplete": "off",
                }
            ),
            "workspace": forms.Select(
                attrs={
                    "class": "form-control",
                    "autocomplete": "off",
                }
            ),
            "is_report": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input",
                    "autocomplete": "off",
                }
            ),
            "demo": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input",
                    "autocomplete": "off",
                }
            ),
        }
    