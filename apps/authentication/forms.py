"""
Formularios de autentificación de usuarios.

Este módulo asigna los formularios de autentificación de usuarios en las vistas de inicio, login,
cambio y restauración de contraseñas. El código se construye herendando su funcionalidad a partir
de las clases principales que suministra el componente `django.contrib.auth`, que incluyen la
validación de formularios, el manejo adecuado y seguro de las peticiones GET y POST, y las capas
de seguridad para la interacción de la información.

Obtiene el modelo del usuario mediante get_user_model() designado en la configuración principal de
la aplicación `settings`.

Para más detalles sobre el uso del sistema de autenticación de Django, consulte
https://docs.djangoproject.com/en/4.0/topics/auth/customizing/
https://docs.djangoproject.com/en/4.1/topics/forms/
"""

from any_imagefield.models import AnyImageField
from django import forms
from django.contrib.auth import get_user_model, password_validation
from django.contrib.auth.forms import (PasswordResetForm, SetPasswordForm,
                                       UserChangeForm, UserCreationForm)
from django.contrib.auth.models import Group, Permission
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from apps.realtime.models import Vehicle, VehicleGroup
from apps.whitelabel.models import Company

User = get_user_model()


class MyCheckboxSelectMultiple(forms.CheckboxSelectMultiple):
    def render(self, name, value, attrs=None, renderer=None):
        attrs = attrs or {}
        attrs["class"] = "form-check form-switch"
        rendered = super().render(name, value, attrs, renderer)
        return rendered.replace('class="', 'class="form-check-input ')


class MyInlineSelectMultiple(forms.CheckboxSelectMultiple):
    def render(self, name, value, attrs=None, renderer=None):
        attrs = attrs or {}
        attrs["class"] = "form-check form-check-inline"
        rendered = super().render(name, value, attrs, renderer)
        return rendered.replace('class="', 'class="form-check-input ')


class IndexForm_(forms.ModelForm):
    """
    Formulario usado para la validación del correo electrónico en la página de inicio `index`
    de la aplicación.
    """

    class Meta:
        """Define el campo email del modelo User como único a renderizar en el formulario."""

        model = User
        fields = ["email"]
        widgets = {
            "email": forms.EmailInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("user@email.com"),
                    "autofocus": True,
                    "autocomplete": "off",
                }
            ),
        }

    def clean_email(self):
        """
        Si la dirección de correo electrónico ingresada en el formulario no se encuentra en la base
        de datos, genera un error de validación.
        :return: La dirección de correo electrónico que se ingresó en el formulario.
        """
        form_email = self.cleaned_data["email"]

        try:
            # Verificar si el correo electrónico está registrado y activo
            user = User.objects.get(email=form_email)
            if not user.is_active:
                # Si el usuario no está activo, lanzar una excepción con un mensaje de advertencia
                msg = _("The email %(email)s is registered but not active.") % {
                    "email": form_email
                }
                raise forms.ValidationError(msg)
        except User.DoesNotExist:
            # Si el correo electrónico no está registrado en la aplicación, lanzar una excepción
            # con un mensaje de error
            msg = _("The email %(email)s is not registered in the application.") % {
                "email": form_email
            }
            raise forms.ValidationError(msg)

        return form_email


class LoginForm_(forms.ModelForm):
    """
    Formulario usado para la autentificación del usuario (una vez se ha verificado que el correo a
    través de la página de inicio).
    """

    class Meta:
        """Define el campo password del modelo User como único a renderizar en el formulario."""

        model = User
        fields = ["password"]
        widgets = {
            "password": forms.PasswordInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Password"),
                    "autofocus": True,
                    "required": True,
                    "autocomplete": "off",
                }
            ),
        }


class SetPasswordForm_(SetPasswordForm):
    """
    Formulario que habilita al usuario para establecer una nueva contraseña sin necesidad de
    escribir la anterior. Ideal para los casos de restauración de contraseña por olvido.
    """

    new_password1 = forms.CharField(
        label=_("New Password"),
        strip=False,
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "autocomplete": "off"}  # Cambiado a "off"
        ),
        help_text=password_validation.password_validators_help_text_html(),
    )
    new_password2 = forms.CharField(
        label=_("New password confirmation"),
        strip=False,
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "autocomplete": "off"}  # Cambiado a "off"
        ),
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(user, *args, **kwargs)


class PasswordChangeForm_(SetPasswordForm_):
    """
    Formulario que permite a un usuario cambiar su contraseña introduciendo su antigua contraseña.
    """

    error_messages = {
        **SetPasswordForm_.error_messages,
        "password_incorrect": _(
            "Your old password was entered incorrectly. Please enter it again."
        ),
    }
    old_password = forms.CharField(
        strip=False,
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "autofocus": True, "autocomplete": False}
        ),
    )
    field_order = ["old_password", "new_password1", "new_password2"]

    def clean_old_password(self):
        """Verifica que la contraseña actual sea correcta."""
        old_password = self.cleaned_data["old_password"]
        if not self.user.check_password(old_password):
            raise ValidationError(
                self.error_messages["password_incorrect"],
                code="password_incorrect",
            )
        return old_password


class PasswordResetForm_(PasswordResetForm):
    """
    Formulario de solicitud de reestablecimiento de contraseña por correo electrónico. Verifica que
    el correo ingresado en el formulario se encuentre registrado en la aplicación, a continuación
    genera un token y envía un correo con el enlace para restaurar la contraseña.
    """

    email = forms.EmailField(
        label=_("Email"),
        max_length=128,
        widget=forms.EmailInput(
            attrs={
                "autocomplete": "email",
                "class": "form-control",
                "placeholder": _("user@email.com"),
                "autofocus": True,
            }
        ),
    )

    def send_mail(
        self,
        subject_template_name,
        email_template_name,
        context,
        from_email,
        to_email,
        html_email_template_name=None,
    ):
        """Envía un correo al usuario con el token que permite reestablecer la contraseña."""
        return super().send_mail(
            subject_template_name,
            email_template_name,
            context,
            from_email,
            to_email,
            html_email_template_name,
        )

    def get_users(self, email):
        """Verifica que el correo ingresado esté registrado en el aplicación."""
        return super().get_users(email)

    def save(
        self,
        domain_override=None,
        subject_template_name="registration/password_reset_subject.txt",
        email_template_name="registration/password_reset_email.html",
        use_https=False,
        token_generator=default_token_generator,
        from_email=None,
        request=None,
        html_email_template_name=None,
        extra_email_context=None,
    ):
        """Gerera el token y la plantilla de correo para enviar al usuario."""
        return super().save(
            domain_override,
            subject_template_name,
            email_template_name,
            use_https,
            token_generator,
            from_email,
            request,
            html_email_template_name,
            extra_email_context,
        )


class UserAdminCreationForm_(UserCreationForm):
    """
    Formulario usado para crear un nuevo usuario en la interfaz de administración.
    """

    error_messages = {**UserCreationForm.error_messages}

    class Meta:
        """Agrega los campos personalizados del model User en la interfaz de administración."""

        model = User
        fields = UserCreationForm.Meta.fields + (
            "company",
            "companies_to_monitor",
            "vehicles_to_monitor",
            "group_vehicles",
        )


class UserAdminChangeForm_(UserChangeForm):
    """
    Formulario usado en administración para cambiar la información y los permisos de un usuario.
    """

    class Meta:
        """Agrega los campos personalizados del model User en la interfaz de administración."""

        model = User
        fields = UserCreationForm.Meta.fields + (
            "company",
            "companies_to_monitor",
            "vehicles_to_monitor",
            "group_vehicles",
        )


class UserCreationForm_(UserCreationForm):
    """
    Formulario usado para crear un nuevo usuario en la interfaz de usuario.
    """

    error_messages = {**UserCreationForm.error_messages}
    password1 = forms.CharField(
        label="Contraseña",
        required=True,
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "autocomplete": "off",
            }
        ),
    )
    password2 = forms.CharField(
        label="Contraseña",
        required=True,
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "autocomplete": "off",
            }
        ),
    )
    companies_to_monitor = forms.ModelMultipleChoiceField(
        required=False,
        queryset=Company.objects.filter(visible=True, actived=True),
        widget=MyCheckboxSelectMultiple(
            attrs={
                "class": "form-check-input",
                "autocomplete": "off",
            }
        ),
    )
    vehicles_to_monitor = forms.ModelMultipleChoiceField(
        required=False,
        queryset=Vehicle.objects.filter(visible=True),
        widget=MyCheckboxSelectMultiple(
            attrs={
                "class": "form-check-input",
                "autocomplete": "off",
            }
        ),
    )
    group_vehicles = forms.ModelMultipleChoiceField(
        required=False,
        queryset=VehicleGroup.objects.filter(visible=True),
        widget=MyCheckboxSelectMultiple(
            attrs={
                "class": "form-check-input",
                "autocomplete": "off",
            }
        ),
    )

    class Meta:
        """Agrega los campos personalizados del model User en la interfaz de usuario."""

        model = User
        fields = UserCreationForm.Meta.fields + (
            "email",
            "first_name",
            "last_name",
            "company",
            "companies_to_monitor",
            "vehicles_to_monitor",
            "alarm",
            "is_active",
            "group_vehicles",
            "process_type",
            "rol",
        )

        labels = {
            "email": _("Email"),
            "first_name": _("First name"),
            "last_name": _("Last name"),
            "company": _("Company"),
            "companies_to_monitor": _("Companies to monitor"),
            "vehicles_to_monitor": _("Vehicles to monitor"),
            "alarm": _("alarm"),
            "is_active": _("Active"),
            "group_vehicles": _("group vehicles"),
            "process_type": _("process_type"),
            "rol":_("rol")
        }
        widgets = {
            "username": forms.TextInput(
                attrs={
                    "autocomplete": "off",
                    "class": "form-control",
                }
            ),
            "email": forms.EmailInput(
                attrs={
                    "autocomplete": "off",
                    "class": "form-control",
                    "autofocus": True,
                }
            ),
            "first_name": forms.TextInput(
                attrs={
                    "autocomplete": "off",
                    "class": "form-control",
                }
            ),
            "last_name": forms.TextInput(
                attrs={
                    "autocomplete": "off",
                    "class": "form-control",
                }
            ),
            "company": forms.Select(
                attrs={
                    "autocomplete": "off",
                    "class": "form-control",
                }
            ),
            "companies_to_monitor": forms.SelectMultiple(
                attrs={
                    "autocomplete": "off",
                    "class": "form-control",
                }
            ),
            "group_vehicles": forms.SelectMultiple(
                attrs={
                    "autocomplete": "off",
                    "class": "form-control",
                }
            ),
            "vehicles_to_monitor": forms.SelectMultiple(
                attrs={
                    "autocomplete": "off",
                    "class": "form-control",
                }
            ),
            "alarm": forms.Select(
                attrs={
                    "autocomplete": "off",
                    "class": "form-control",
                }
            ),
            "is_active": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input",
                }
            ),
            "rol": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input",
                }
            ),
            "process_type": forms.Select(
                attrs={
                    "autocomplete": "off",
                    "class": "form-control",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["process_type"].required = True

    def clean_email(self):
        """
        Verifica si la dirección de correo electrónico ya está registrada en la base de datos.
        Si el correo electrónico ya existe, genera un error de validación.
        """
        email = self.cleaned_data.get("email")
        if User.objects.filter(email=email, visible=True).exists():
            raise ValidationError(_("A user with this email address already exists."))
        return email

    def clean_username(self):
        """
        Verifica si el nombre de usuario ya está registrado dentro de la misma compañía y es visible.
        Si el nombre de usuario ya existe, genera un error de validación.
        """
        username = self.cleaned_data.get("username")
        company = self.cleaned_data.get("company")
        if User.objects.filter(
            username=username, company=company, visible=True
        ).exists():
            raise ValidationError(
                _("A user with this username already exists in the selected company.")
            )
        return username


class UserChangeForm_(UserChangeForm):
    """
    Formulario usado en la interfaz de usuario para cambiar la información de un usuario.
    """

    companies_to_monitor = forms.ModelMultipleChoiceField(
        required=False,
        queryset=Company.objects.filter(visible=True, actived=True),
        widget=MyCheckboxSelectMultiple(
            attrs={
                "class": "form-check-input",
                "autocomplete": "off",
            }
        ),
    )
    vehicles_to_monitor = forms.ModelMultipleChoiceField(
        required=False,
        queryset=Vehicle.objects.filter(visible=True, is_active=True),
        widget=MyCheckboxSelectMultiple(
            attrs={
                "class": "form-check-input",
                "autocomplete": "off",
            }
        ),
    )
    group_vehicles = forms.ModelMultipleChoiceField(
        required=False,
        queryset=VehicleGroup.objects.all(),
        widget=MyCheckboxSelectMultiple(
            attrs={
                "class": "form-check-input",
                "autocomplete": "off",
            }
        ),
    )

    class Meta:
        """Agrega los campos personalizados del model User en la interfaz de usuario."""

        model = User
        fields = UserCreationForm.Meta.fields + (
            "first_name",
            "last_name",
            "company",
            "companies_to_monitor",
            "vehicles_to_monitor",
            "is_active",
            "alarm",
            "email",
            "group_vehicles",
            "process_type",
            "rol"
        )
        labels = {
            "email": _("Email"),
            "first_name": _("First name"),
            "last_name": _("Last name"),
            "company": _("Company"),
            "companies_to_monitor": _("Companies to monitor"),
            "vehicles_to_monitor": _("Vehicles to monitor"),
            "is_active": _("Active"),
            "alarm": _("alarm"),
            "group_vehicles": _("group vehicles"),
            "process_type": _("process_type"),
            "rol":_("rol")
        }
        widgets = {
            "username": forms.TextInput(
                attrs={
                    "autocomplete": "off",
                    "class": "form-control",
                }
            ),
            "email": forms.EmailInput(
                attrs={
                    "autocomplete": "off",
                    "class": "form-control",
                    "placeholder": _("Email"),
                    "autofocus": True,
                }
            ),
            "first_name": forms.TextInput(
                attrs={
                    "autocomplete": "off",
                    "class": "form-control",
                }
            ),
            "last_name": forms.TextInput(
                attrs={
                    "autocomplete": "off",
                    "class": "form-control",
                }
            ),
            "company": forms.Select(
                attrs={
                    "autocomplete": "off",
                    "class": "form-control",
                }
            ),
            "companies_to_monitor": forms.SelectMultiple(
                attrs={
                    "autocomplete": "off",
                    "class": "form-control",
                }
            ),
            "group_vehicles": forms.SelectMultiple(
                attrs={
                    "autocomplete": "off",
                    "class": "form-control",
                }
            ),
            "vehicles_to_monitor": forms.SelectMultiple(
                attrs={
                    "autocomplete": "off",
                    "class": "form-control",
                }
            ),
            "is_active": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input",
                }
            ),
            "alarm": forms.Select(
                attrs={
                    "autocomplete": "off",
                    "class": "form-control",
                }
            ),
            "rol": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input",
                }
            ),
            "process_type": forms.Select(
                attrs={
                    "autocomplete": "off",
                    "class": "form-control",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["process_type"].required = True  # Establecer como requerido


class PermissionForm(UserChangeForm):
    """
    Formulario para administrar los permisos de un usuario.

    Este formulario se utiliza para mostrar y editar los permisos de un usuario.
    Los permisos se pueden asignar a través de grupos o directamente al usuario.

    Atributos:
        groups (ModelMultipleChoiceField): Campo de selección múltiple para los grupos.
        user_permissions (ModelMultipleChoiceField): Campo de selección múltiple para los permisos.

    Meta:
        model (User): Modelo de usuario asociado al formulario.
        fields (tuple): Campos que se mostrarán en el formulario.
        labels (dict): Etiquetas personalizadas para los campos del formulario.
    """

    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all(),
        widget=MyCheckboxSelectMultiple(),
    )
    user_permissions = forms.ModelMultipleChoiceField(
        queryset=Permission.objects.all(),
        widget=MyInlineSelectMultiple(),
    )

    class Meta:
        """Agrega los campos personalizados del model User en la interfaz de usuario."""

        model = User
        fields = (
            "groups",
            "user_permissions",
        )
        labels = {
            "groups": _("Group"),
            "user_permissions": _("Permisssion"),
        }


class UserProfileForm(forms.ModelForm):
    profile_picture = AnyImageField()

    class Meta:
        model = User  # Obtiene el modelo de usuario personalizado
        fields = ("profile_picture",)
