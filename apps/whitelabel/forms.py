import pycountry
from any_imagefield.models import AnyImageField
from django import forms
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from apps.whitelabel.models import Company, CompanyTypeMap, MapType, Module, Theme

from .models import Attachment, Comment, Message, Process, Ticket

# Import the list of countries from pycountry
countries = list(map(Company.from_pycountry, pycountry.countries))


class MyCheckboxSelectMultiple(forms.CheckboxSelectMultiple):
    def render(self, name, value, attrs=None, renderer=None):
        attrs = attrs or {}
        attrs["class"] = "form-check form-switch"
        rendered = super().render(name, value, attrs, renderer)
        return rendered.replace('class="', 'class="form-check-input ')


class DistributionCompanyForm(forms.ModelForm):
    """
    # Un formulario que se utiliza para crear una nueva empresa.

    """

    modules = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all(),
        widget=MyCheckboxSelectMultiple(),
    )

    type_map = forms.ModelMultipleChoiceField(
        queryset=MapType.objects.all(),
        widget=MyCheckboxSelectMultiple(),
    )

    key_map = forms.CharField(required=False)

    class Meta:
        model = Company
        fields = (
            "nit",
            "company_name",
            "legal_representative",
            "address",
            "country",
            "city",
            "phone_number",
            "signed_contract",
            "consultant",
            "seller",
            "type_map",
            "modules",
            "actived",
            "key_map",
            "coin",
        )
        labels = {
            "nit": _("Nit"),
            "company_name": _("Company Name"),
            "legal_representative": _("Legal Representative"),
            "address": _("Address"),
            "country": _("Country"),
            "city": _("City"),
            "phone_number": _("Phone Number"),
            "signed_contract": _("Signed Contract"),
            "consultant": _("Consultant"),
            "seller": _("Seller"),
            "type_map": _("Type Map"),
            "modules": _("Modules"),
            "actived": _("Actived"),
            "key_map": _("Key Map"),
            "coin": _("Coin"),
        }
        widgets = {
            "nit": forms.TextInput(attrs={
                "class": "form-control",
                "autocomplete": "off"
            }),
            "company_name": forms.TextInput(attrs={
                "class": "form-control",
                "autocomplete": "off"
            }),
            "legal_representative": forms.TextInput(attrs={
                "class": "form-control",
                "autocomplete": "off"
            }),
            "address": forms.TextInput(attrs={
                "class": "form-control",
                "autocomplete": "off"
            }),
            "country": forms.Select(choices=countries, attrs={
                "class": "form-control",
                "autocomplete": "off"
            }),
            "city": forms.TextInput(attrs={
                "class": "form-control",
                "autocomplete": "off"
            }),
            "phone_number": forms.NumberInput(attrs={
                "class": "form-control",
                "min": 10,
                "autocomplete": "off"
            }),
            "signed_contract": forms.CheckboxInput(attrs={
                "class": "form-check-input"
            }),
            "consultant": forms.TextInput(attrs={
                "class": "form-control",
                "autocomplete": "off"
            }),
            "seller": forms.TextInput(attrs={
                "class": "form-control",
                "autocomplete": "off"
            }),
            "actived": forms.CheckboxInput(attrs={
                "class": "form-check-input"
            }),
            "coin": forms.Select(attrs={
                "class": "form-control",
                "autocomplete": "off"
            }),
        }


    def __init__(self, *args, **kwargs):
        self.provider_id = kwargs.pop(
            "provider_id", None
        )  # Extrae provider_id y lo elimina de kwargs
        super().__init__(*args, **kwargs)

    def clean_nit(self):
        nit = self.cleaned_data.get("nit")
        provider = self.cleaned_data.get("provider_id")
        if (
            nit == 1
            and self.provider_id == None
            or Company.objects.filter(nit=nit, provider=provider, visible=True)
            .exclude(pk=self.instance.pk)
            .exists()
        ):
            raise ValidationError(_("A company with this NIT already exists."))
        # Ahora también verifica el provider_id junto con el nit
        elif (
            self.provider_id
            and Company.objects.filter(nit=nit, provider=self.provider_id, visible=True)
            .exclude(pk=self.instance.pk)
            .exists()
        ):
            raise ValidationError(_("A company with this NIT already exists."))
        return nit


class CompanyCustomerForm(forms.ModelForm):
    """
    # Un formulario que se utiliza para crear una nueva empresa.
    """

    modules = forms.ModelMultipleChoiceField(
        queryset=Group.objects.none(),  # Inicialmente vacío, se establecerá según el usuario
        widget=MyCheckboxSelectMultiple(),  # Asume que tienes un widget personalizado o usa el predeterminado
    )

    type_map = forms.ModelMultipleChoiceField(
        queryset=MapType.objects.none(),  # Inicialmente vacío, se establecerá según el usuario
        widget=MyCheckboxSelectMultiple(),  # Asume que tienes un widget personalizado o usa el predeterminado
    )

    key_map = forms.CharField(required=False)

    class Meta:
        model = Company
        fields = (
            "nit",
            "company_name",
            "legal_representative",
            "address",
            "country",
            "city",
            "phone_number",
            "signed_contract",
            "actived",
            "type_map",
            "modules",
            "key_map",
            "coin",
        )
        labels = {
            "nit": _("Nit"),
            "company_name": _("Company Name"),
            "legal_representative": _("Legal Representative"),
            "address": _("Address"),
            "country": _("Country"),
            "city": _("City"),
            "phone_number": _("Phone Number"),
            "signed_contract": _("Signed Contract"),
            "consultant": _("Consultant"),
            "seller": _("Seller"),
            "type_map": _("Type Map"),
            "modules": _("Modules"),
            "actived": _("Actived"),
            "key_map": _("Key Map"),
            "coin": _("Coin"),
        }
        widgets = {
            "nit": forms.TextInput(attrs={
                "class": "form-control",
                "autocomplete": "off"
            }),
            "company_name": forms.TextInput(attrs={
                "class": "form-control",
                "autocomplete": "off"
            }),
            "legal_representative": forms.TextInput(attrs={
                "class": "form-control",
                "autocomplete": "off"
            }),
            "address": forms.TextInput(attrs={
                "class": "form-control",
                "autocomplete": "off"
            }),
            "country": forms.Select(attrs={
                "class": "form-control",
                "autocomplete": "off"
            }),
            "city": forms.TextInput(attrs={
                "class": "form-control",
                "autocomplete": "off"
            }),
            "phone_number": forms.NumberInput(attrs={
                "class": "form-control",
                "min": 10,
                "autocomplete": "off"
            }),
            "signed_contract": forms.CheckboxInput(attrs={
                "class": "form-check-input"
            }),
            "actived": forms.CheckboxInput(attrs={
                "class": "form-check-input"
            }),
            "coin": forms.Select(attrs={
                "class": "form-control",
                "autocomplete": "off"
            }),
        }

    def __init__(self, *args, **kwargs):
        self.provider_id = kwargs.pop("provider_id", None)
        super().__init__(*args, **kwargs)

        if self.instance.pk:  # Comprobando si hay una instancia existente (edición)
            # Establecer queryset para incluir todos los módulos/mapas disponibles para el proveedor
            self.fields["type_map"].queryset = MapType.objects.filter(
                companytypemap__company_id=self.provider_id
            ).distinct()

            self.fields["modules"].queryset = Group.objects.filter(
                module__company_id=self.provider_id
            ).distinct()

            # Establecer los valores iniciales para seleccionar solo los activos
            self.fields[
                "type_map"
            ].initial = self.instance.type_map.filter().values_list("id", flat=True)

            self.fields["modules"].initial = self.instance.modules.values_list(
                "id", flat=True
            )

        else:  # Si no es una edición, es una creación
            if self.provider_id is not None:
                self.fields["type_map"].queryset = MapType.objects.filter(
                    companytypemap__company_id=self.provider_id
                ).distinct()

                self.fields["modules"].queryset = Group.objects.filter(
                    module__company_id=self.provider_id
                ).distinct()

    def clean_nit(self):
        nit = self.cleaned_data.get("nit")
        # Ahora también verifica el provider_id junto con el nit
        if (
            self.provider_id
            and Company.objects.filter(
                nit=nit,
                provider_id=self.provider_id,  # Asegúrate de que estás usando el campo correcto para 'provider'
                visible=True,
            )
            .exclude(pk=self.instance.pk)
            .exists()
        ):
            raise ValidationError(_("A company with this NIT already exists."))
        return nit


class CompanyLogoForm(forms.ModelForm):
    company_logo = AnyImageField()

    class Meta:
        model = Company
        fields = ("company_logo",)


class KeyMapForm(forms.ModelForm):
    class Meta:
        model = CompanyTypeMap
        fields = ["id", "key_map", "map_type"]
        widgets = {
            "id": forms.HiddenInput(),
            "map_type": forms.HiddenInput(),
            "key_map": forms.TextInput(attrs={
                "class": "form-control",
                "autocomplete": "off"
            }),
        }


class CompanyDeleteForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = ("visible",)


class ThemeForm(forms.ModelForm):
    # Formulario para asignar un tema a una empresa.

    button_color = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "type": "color",
                "data-id": "color",
                "name": "Background",
                "id": "color-picker-button",
                "style": "width: 100px; height: 100px;",
                "autocomplete": "off"
            }
        )
    )
    sidebar_color = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "type": "color",
                "data-id": "color",
                "name": "sidebar_color",
                "id": "color_sidebar",
                "style": "width: 100px; height: 100px;",
                "autocomplete": "off"
            }
        )
    )

    class Meta:
        model = Theme
        fields = [
            "button_color",
            "sidebar_color",
            "opacity",
            "sidebar_image",
            "lock_screen_image",
        ]
        labels = {
            "button_color": _("Button Color"),
            "sidebar_color": _("Sidebar Color"),
            "opacity": _("Opacity"),
            "sidebar_image": _("Sidebar Image"),
            "lock_screen_image": _("Lock Screen Image"),
        }


class Moduleform(forms.ModelForm):
    # Formulario para asignar permisos a una empresa.

    class Meta:
        model = Module
        fields = [
            "id",
            "group",
            "price",
        ]
        widgets = {
            "id": forms.HiddenInput(),
            "group": forms.HiddenInput(),
            "price": forms.NumberInput(attrs={
                "class": "form-control",
                "autocomplete": "off"
            }),
        }


class ProcessForm(forms.ModelForm):
    class Meta:
        model = Process
        fields = [
            "process_type",
            "company",
        ]
        widgets = {
            "process_type": forms.TextInput(attrs={
                "class": "form-control",
                "autocomplete": "off"  
            }),
            "company": forms.Select(attrs={
                "class": "form-control",
                "autocomplete": "off"  
            }),
        }


class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ["text"]
        widgets = {
            "text": forms.Textarea(
                attrs={
                    "class": "form-control",  # Esta clase es de Bootstrap
                    "rows": 3,
                    "placeholder": "Escribe tu comentario aquí...",  # Un ejemplo de placeholder
                    "style": "border: 1px solid #ced4da; border-radius: 0.25rem;",  # CSS personalizado
                    "autocomplete": "off"
                }
            ),
        }


class AttachmentForm(forms.ModelForm):
    file = forms.FileField(
        widget=forms.ClearableFileInput(attrs={"multiple": True}), required=False
    )

    class Meta:
        model = Attachment
        fields = ["file"]


class TicketForm(forms.ModelForm):
    priority = forms.ChoiceField(
        choices=[("High", "High"), ("Medium", "Medium"), ("Low", "Low")],
        widget=forms.Select(attrs={
            "class": "form-control",
            "autocomplete": "off"
        }),
    )
    provider_company = forms.ModelChoiceField(
        queryset=Company.objects.filter(visible = True, actived = True),
        required=False,
        label=_("Provider Company"),
        widget=forms.Select(attrs={
            "class": "form-control",
            "autocomplete": "off"
        }),
    )

    customer_company = forms.ModelChoiceField(
        queryset=Company.objects.filter(visible = True, actived = True),
        required=False,
        label=_("Customer Company"),
        widget=forms.Select(attrs={
            "class": "form-control",
            "autocomplete": "off"
        }),
    )
    process_type = forms.ModelChoiceField(
        queryset=Process.objects.none(),
        required=False,
        label=_("process_type"),
        widget=forms.Select(attrs={
            "class": "form-control",
            "autocomplete": "off"
        }),
    )

    class Meta:
        model = Ticket
        fields = [
            "subject",
            "priority",
            "process_type",
            "assign_to",
            "provider_company",
            "customer_company",
        ]

        widgets = {
            "subject": forms.TextInput(attrs={
                "class": "form-control",
                "autocomplete": "off"
            }),
            "assign_to": forms.Select(attrs={
                "class": "form-control",
                "autocomplete": "off"
            }),
        }

    def __init__(self, *args, **kwargs):
        company = kwargs.pop("company", None)
        company_tk = kwargs.pop("company_tk", None)
        process = kwargs.pop("process", None)

        super().__init__(*args, **kwargs)

        if company:
            self.fields["process_type"].queryset = Process.objects.filter(
                company=company
            )

        if company_tk and process:
            self.fields["assign_to"].queryset = process.user_set.filter(
                company=company_tk
            )

    def clean_process_type(self):
        process_type = self.cleaned_data.get("process_type")
        if not process_type:
            raise forms.ValidationError("Please select a process type.")
        return process_type


class CommentForm(forms.ModelForm):
    attachment = forms.FileField(required=False)  # Agrega un campo para cargar archivos

    class Meta:
        model = Comment  # Asegúrate de tener un modelo llamado Comment en tu aplicación
        fields = ["text"]  # Ajusta los campos según tus necesidades
        widgets = {
            "text": forms.Textarea(attrs={
                "class": "form-control", 
                "rows": 3,
                "autocomplete": "off"
            }),
        }


class CloseTicketForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = [
            "status"
        ]  # Asumiendo que 'status' es un campo booleano que indica si el ticket está abierto o cerrado
