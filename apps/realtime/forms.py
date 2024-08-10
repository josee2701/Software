import os

from azure.storage.blob import BlobServiceClient
from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from apps.whitelabel.forms import MyCheckboxSelectMultiple

from .apis import get_user_vehicles
from .models import (
    DataPlan,
    Device,
    Geozones,
    Io_items_report,
    Sending_Commands,
    SimCard,
    Vehicle,
    VehicleGroup,
)


class MyCheckboxSelectMultiple(forms.CheckboxSelectMultiple):
    def render(self, name, value, attrs=None, renderer=None):
        attrs = attrs or {}
        attrs["class"] = "form-check form-switch"
        rendered = super().render(name, value, attrs, renderer)
        return rendered.replace('class="', 'class="form-check-input ')


class DataPlanForm(forms.ModelForm):
    """
    Formulario de planes de datos que utiliza la clase ModelForm de Django. La clase Meta
    especifica el modelo y campos, y se usan widgets para personalizar el formulario
    """

    class Meta:
        model = DataPlan
        fields = ["name", "coin", "price", "company", "operator"]
        widgets = {
            "name": forms.TextInput(
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
            "company": forms.Select(
                attrs={
                    "class": "form-control",
                    "autocomplete": "off",  
                }
            ),
            "operator": forms.Select(
                attrs={
                    "class": "form-control",
                    "autocomplete": "off",  
                }
            ),
        }


class SimcardForm(forms.ModelForm):
    """
    Formulario de simcard que utiliza la clase ModelForm de Django. La clase Meta especifica el
    modelo y campos, y se usan widgets para personalizar el formulario"""

    class Meta:
        model = SimCard
        fields = [
            "serial_number",
            "phone_number",
            "is_active",
            "activate_date",
            "iz_az_simcard",
            "data_plan",
            "company",
        ]
        widgets = {
            "serial_number": forms.TextInput(
                attrs={
                    "class": "form-control form-control-lg",
                    "aria-label": ".form-control-lg example",
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
            "is_active": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input",
                    "autocomplete": "off",  
                }
            ),
            "activate_date": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                    "autocomplete": "off",  
                }
            ),
            "iz_az_simcard": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input",
                    "autocomplete": "off",  
                }
            ),
            "data_plan": forms.Select(
                attrs={
                    "class": "form-control",
                    "autocomplete": "off",  
                }
            ),
            "company": forms.Select(
                attrs={
                    "class": "form-control",
                    "autocomplete": "off",  
                }
            ),
        }

    def clean(self):
        cleaned_data = super().clean()
        phone_number = cleaned_data.get("phone_number")
        serial_number = cleaned_data.get("serial_number")

        if self.instance.pk is None:
        # Validar duplicados solo si estamos creando un nuevo registro
            if phone_number:
                duplicate_phone_count = SimCard.objects.filter(
                    phone_number=phone_number, visible=True
                ).count()
                if duplicate_phone_count > 0:
                    raise ValidationError(
                        {"phone_number": _("This phone number is already in use.")}
                    )

            if serial_number:
                duplicate_serial_count = SimCard.objects.filter(
                    serial_number=serial_number, visible=True
                ).count()
                if duplicate_serial_count > 0:
                    raise ValidationError(
                        {"serial_number": _("This serial number is already in use.")}
                    )

        # if self._state.adding:  # Se verifica si el objeto está siendo creado
        #     duplicate_phone_count = SimCard.objects.filter(phone_number=phone_number,
        # visible=False).count()
        #     if duplicate_phone_count >= 5:
        #         raise ValidationError({"phone_number": _("No se permite duplicar el mismo número
        # de teléfono más de 5 veces.")})

        #     duplicate_serial_count = SimCard.objects.filter(serial_number=serial_number,
        # visible=False).count()
        #     if duplicate_serial_count >= 5:
        #         raise ValidationError({"serial_number": _("No se permite duplicar el mismo
        # número de serie más de 5 veces.")})


class DeviceForm(forms.ModelForm):
    """Formulario de dispositivo que utiliza la clase ModelForm de Django. La clase Meta especifica
    el modelo y campos, y se usan widgets para personalizar el formulario."""

    class Meta:
        model = Device
        fields = [
            "imei",
            "simcard",
            "serial_number",
            "firmware",
            "is_active",
            "familymodel",
            "company",
        ]
        widgets = {
            "imei": forms.NumberInput(
                attrs={
                    "class": "form-control form-control-lg-md-2",
                    "aria-label": ".form-control-lg example",
                    "autocomplete": "off",  
                }
            ),
            "familymodel": forms.Select(
                attrs={
                    "class": "form-control",
                    "autocomplete": "off",  
                }
            ),
            "simcard": forms.Select(
                attrs={
                    "class": "form-control",
                    "autocomplete": "off",  
                }
            ),
            "serial_number": forms.TextInput(
                attrs={
                    "class": "form-control form-control-lg-md-2",
                    "aria-label": ".form-control-lg example",
                    "autocomplete": "off",  
                }
            ),
            "firmware": forms.TextInput(
                attrs={
                    "class": "form-control form-control-lg-md-2",
                    "aria-label": ".form-control-lg example",
                    "autocomplete": "off",  
                }
            ),
            "is_active": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input",
                    "autocomplete": "off",  
                }
            ),
            "company": forms.Select(
                attrs={
                    "class": "form-control",
                    "autocomplete": "off",  
                }
            ),
        }

    def clean(self):
        cleaned_data = super().clean()
        imei = cleaned_data.get("imei")

        # Busca un dispositivo existente con el mismo IMEI y donde visible sea False
        existing_device = Device.objects.filter(imei=imei, visible=False).first()
        if existing_device:
            existing_device.delete()  # Elimina el dispositivo existente si se encuentra
            return cleaned_data
        # Verificar si ya existe un conductor con la misma identificación personal
        if Device.objects.filter(imei=imei, visible=True).exists():
            # Si es una actualización y el valor ha cambiado
            if isinstance(self.instance, Device) and self.instance.pk is not None:
                if imei != self.instance.imei:
                    raise forms.ValidationError(
                        _("Device with this Imei already exists.")
                    )
            else:  # Si es una creación
                raise forms.ValidationError(_("Device with this Imei already exists."))

        return cleaned_data


def get_vehicle_icons(AZURE_CUSTOM_DOMAIN):
    try:
        # Intenta crear una instancia del cliente del servicio Blob con la URL de tu dominio personalizado de Azure.
        blob_service_client = BlobServiceClient(
            account_url=f"https://{AZURE_CUSTOM_DOMAIN}",
            credential=os.environ.get("AZURE_ACCOUNT_KEY"),
        )
    except Exception as e:
        print(f"Error al conectar con Azure Blob Storage: {e}")
        return []

    try:
        # Obtiene el cliente del contenedor utilizando la ubicación del medio especificada en tus settings.
        blob_container_client = blob_service_client.get_container_client(
            settings.MEDIA_LOCATION
        )
    except Exception as e:
        print(f"Error al obtener el cliente del contenedor: {e}")
        return []

    try:
        # Lista todos los blobs en el contenedor que comiencen con "Iconos_vehicles/"
        blobs_list = blob_container_client.list_blobs(
            name_starts_with="Iconos_vehicles/"
        )
        images = [f"{settings.MEDIA_URL}{blob.name}" for blob in blobs_list]
    except Exception as e:
        print(f"Error al listar blobs en el contenedor: {e}")
        return []

    return images


class VehicleForm(forms.ModelForm):
    """Formulario de vehículo que utiliza la clase ModelForm de Django. La clase Meta especifica
    el modelo y campos, y se usan widgets para personalizar el formulario."""

    icon = forms.ChoiceField(choices=[])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        AZURE_ACCOUNT_NAME = os.environ.get("AZURE_ACCOUNT_NAME")
        # Obtener las URLs de los iconos de Azure Blob Storage
        AZURE_CUSTOM_DOMAIN = f"{AZURE_ACCOUNT_NAME}.blob.core.windows.net"
        image_urls = get_vehicle_icons(AZURE_CUSTOM_DOMAIN)

        # Convertir las URLs en una lista de tuplas para que sean válidas como opciones de ChoiceField
        icon_choices = [(url, url.split("/")[-1]) for url in image_urls]
        self.fields["icon"].choices = icon_choices

    class Meta:
        model = Vehicle
        fields = [
            "license",
            "chassis",
            "cylinder_capacity",
            "km_per_gallon",
            "vehicle_type",
            "model",
            "brand",
            "engine_serial",
            "fuel_type",
            "max_speed_allowed",
            "insurance",
            "owner",
            "fuel_tank_capacity",
            "icon",
            "is_active",
            "color",
            "device",
            "line",
            "camara",
            "microphone",
            "remote_shutdown",
            "company",
            "capacity",
            "alias",
            "n_interno",
            "installation_date",
            "id",
        ]
        widgets = {
            "license": forms.TextInput(
                attrs={
                    "class": "form-control form-control-lg",
                    "aria-label": ".form-control-lg example",
                    "autocomplete": "off",
                }
            ),
            "chassis": forms.TextInput(
                attrs={
                    "class": "form-control form-control-lg",
                    "aria-label": ".form-control-lg example",
                    "autocomplete": "off",
                }
            ),
            "cylinder_capacity": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "type": "number",
                    "min": "1",
                    "autocomplete": "off",
                }
            ),
            "km_per_gallon": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "type": "number",
                    "min": "1",
                    "autocomplete": "off",
                }
            ),
            "vehicle_type": forms.TextInput(
                attrs={
                    "class": "form-control form-control-lg",
                    "aria-label": ".form-control-lg example",
                    "autocomplete": "off",
                }
            ),
            "model": forms.NumberInput(
                attrs={
                    "class": "form-control form-control-lg",
                    "aria-label": ".form-control-lg example",
                    "min": "0",
                    "max": "9999",
                    "step": "1",
                    "autocomplete": "off",
                }
            ),
            "brand": forms.TextInput(
                attrs={
                    "class": "form-control form-control-lg",
                    "aria-label": ".form-control-lg example",
                    "autocomplete": "off",
                }
            ),
            "engine_serial": forms.TextInput(
                attrs={
                    "class": "form-control form-control-lg",
                    "aria-label": ".form-control-lg example",
                    "autocomplete": "off",
                }
            ),
            "fuel_type": forms.Select(
                attrs={
                    "class": "form-control form-control-lg-md-1",
                    "autocomplete": "off",
                }
            ),
            "max_speed_allowed": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "type": "number",
                    "min": "1",
                    "autocomplete": "off",
                }
            ),
            "insurance": forms.TextInput(
                attrs={
                    "class": "form-control form-control-lg",
                    "aria-label": ".form-control-lg example",
                    "autocomplete": "off",
                }
            ),
            "owner": forms.TextInput(
                attrs={
                    "class": "form-control form-control-lg",
                    "aria-label": ".form-control-lg example",
                    "autocomplete": "off",
                }
            ),
            "fuel_tank_capacity": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "type": "number",
                    "autocomplete": "off",
                }
            ),
            "is_active": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input",
                }
            ),
            "color": forms.TextInput(
                attrs={
                    "class": "form-control form-control-lg",
                    "aria-label": ".form-control-lg example",
                    "autocomplete": "off",
                }
            ),
            "device": forms.Select(
                attrs={
                    "class": "form-control",
                }
            ),
            "line": forms.TextInput(
                attrs={
                    "class": "form-control form-control-lg",
                    "aria-label": ".form-control-lg example",
                    "autocomplete": "off",
                }
            ),
            "camara": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input",
                }
            ),
            "microphone": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input",
                }
            ),
            "remote_shutdown": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input",
                }
            ),
            "capacity": forms.TextInput(
                attrs={
                    "class": "form-control form-control-lg",
                    "aria-label": ".form-control-lg example",
                    "autocomplete": "off",
                }
            ),
            "installation_date": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                }
            ),
            "company": forms.Select(
                attrs={
                    "class": "form-control ",
                }
            ),
            "alias": forms.TextInput(
                attrs={
                    "class": "form-control form-control-lg",
                    "aria-label": ".form-control-lg example",
                    "autocomplete": "off",
                }
            ),
            "n_interno": forms.TextInput(
                attrs={
                    "class": "form-control form-control-lg-md-1",
                    "aria-label": ".form-control-lg example",
                    "autocomplete": "off",
                }
            ),
        }


class VehicleGroupForm(forms.ModelForm):
    """Formulario de vehículo que utiliza la clase ModelForm de Django. La clase Meta especifica
    el modelo y campos, y se usan widgets para personalizar el formulario."""

    vehicles = forms.ModelMultipleChoiceField(
        required=True,
        queryset=Vehicle.objects.filter(visible = True),
        widget=MyCheckboxSelectMultiple(),
        error_messages={
            'required': _("Please select an asset."),
        },
    )

    class Meta:
        model = VehicleGroup
        fields = ["name", "vehicles"]
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "form-control form-control-lg",
                    "aria-label": ".form-control-lg example",
                }
            ),
            "vehicles": forms.CheckboxSelectMultiple(
                attrs={
                    "class": "form-check-input",
                }
            ),
            
        }
    def clean_vehicles(self):
        vehicles = self.cleaned_data.get('vehicles')
        if not vehicles:
            raise forms.ValidationError(_("Please select an asset."))
        return vehicles

class SendingCommandsFrom(forms.ModelForm):
    class Meta:
        model = Sending_Commands
        fields = [
            "device",
            "command",
        ]
        widgets = {
            "device": forms.Select(
                attrs={
                    "class": "form-control",
                    "autocomplete": "off",  
                }
            ),
            "command": forms.Select(
                attrs={
                    "class": "form-control",
                    "autocomplete": "off",  
                }
            ),
        }

    def __init__(self, company_id=None, user=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        vehicles = get_user_vehicles(company_id, user)

        # Agregar una opción vacía al principio de la lista
        choices = [("", "---------")]
        choices += vehicles

        # Asignar las opciones al campo 'device'
        self.fields["device"].choices = choices

    def clean_device(self):
        device_id = self.cleaned_data.get("device")
        try:
            device = Device.objects.get(pk=device_id)
            return device
        except Device.DoesNotExist:
            raise forms.ValidationError("Device does not exist.")

    def clean(self):
        cleaned_data = super().clean()
        device = cleaned_data.get("device")
        if not device:
            raise forms.ValidationError("Please select a device.")
        return cleaned_data


class GeozonesForm(forms.ModelForm):
    class Meta:
        model = Geozones
        fields = [
            "name",
            "description",
            "company",
            "radius",
            "speed",
            "latitude",
            "longitude",
            "type_event",
            "alarma",
            "color",
            "color_edges",
            "shape_type",
        ]
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "autocomplete": "off",  
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "style": "height: 50px;",
                    "autocomplete": "off",  
                }
            ),
            "company": forms.Select(
                attrs={
                    "class": "form-control",
                    "autocomplete": "off",  
                }
            ),
            "radius": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "autocomplete": "off",  
                }
            ),
            "speed": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "autocomplete": "off",  
                }
            ),
            "latitude": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "autocomplete": "off",  
                }
            ),
            "longitude": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "autocomplete": "off",  
                }
            ),
            "color": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "type": "color",
                    "data-id": "color",
                    "autocomplete": "off",  
                }
            ),
            "type_event": forms.Select(
                attrs={
                    "class": "form-control",
                    "onchange": "showHide()",
                    "autocomplete": "off",  
                }
            ),
            "alarma": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input",
                    "autocomplete": "off",  
                }
            ),
            "shape_type": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "autocomplete": "off",  
                }
            ),
        }


class ConfigurationReport(forms.ModelForm):
    widgets = forms.MultipleChoiceField(
        widget=MyCheckboxSelectMultiple(), required=False
    )
    reports = forms.MultipleChoiceField(
        widget=MyCheckboxSelectMultiple(), required=False
    )

    class Meta:
        model = Io_items_report
        fields = ["reports", "widgets"]

    def __init__(self, company_id=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
