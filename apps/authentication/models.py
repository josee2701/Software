"""
Modelos de usuario

Este módulo crea los modelos de usuario personalizados para autenticarse en la aplicación. Sigue
el modelo AbstractUser y mantiene las clases vacías para permitir que los campos por defecto se
añadan automáticamente.

Para una referencia completa sobre la autenticación de usuarios en Django, ver
https://docs.djangoproject.com/en/4.0/topics/auth/
"""

from django.contrib.auth.models import AbstractUser
from django.core.validators import FileExtensionValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    """
    Define el modelo de usuario personalizado para la aplicación. Si se añaden campos que deben
    ser rellenados al momento del registro del usuario.
    """

    class Alam(models.TextChoices):
        CENTRAL = _("Central"), _("Central")
        CLIENT = _("Client"), _("Client")

    # Hacer que el email sea obligatorio y único
    email = models.EmailField(_("email address"), blank=False, null=False)
    first_name = models.CharField(
        max_length=150, verbose_name=_("first name"), blank=False
    )
    company = models.ForeignKey(
        "whitelabel.Company",
        on_delete=models.CASCADE,
        blank=False,
        null=True,
        verbose_name=_("company"),
    )
    companies_to_monitor = models.ManyToManyField(
        to="whitelabel.Company",
        related_name="companies_to_monitor",
        related_query_name="companies_to_monitor",
        db_table="authentication_user_companies_to_monitor",
        blank=True,
        verbose_name=_("companies to monitor"),
    )
    vehicles_to_monitor = models.ManyToManyField(
        to="realtime.Vehicle",
        related_name="vehicles_to_monitor",
        related_query_name="vehicles_to_monitor",
        db_table="authentication_user_vehicles_to_monitor",
        blank=True,
        verbose_name=_("vehicles to monitor"),
    )
    group_vehicles = models.ManyToManyField(
        to="realtime.VehicleGroup",
        related_name="group_vehicles",
        related_query_name="group_vehicles",
        db_table="authentication_user_group_vehicles",
        blank=True,
        verbose_name=_("group vehicles"),
    )
    alarm = models.CharField(
        max_length=15,
        choices=Alam.choices,
        default=Alam.CENTRAL,
        verbose_name=_("alarm"),
    )
    user_permissions = models.ManyToManyField(
        "auth.Permission",
        verbose_name="user permissions",
        blank=True,
        related_name="user_set",
    )
    profile_picture = models.ImageField(
        upload_to="Perfil/",  # Define la carpeta donde se almacenarán las imágenes
        validators=[FileExtensionValidator(["png", "jpg", "jpeg"])],
        null=True,
        blank=True,
        verbose_name=_("Profile Picture"),
    )
    last_updated = models.DateTimeField(
        verbose_name=_("last updated"), null=True, default=timezone.now
    )
    modified_by = models.ForeignKey(
        "authentication.User",
        on_delete=models.SET_NULL,  # Usamos SET_NULL para manejar la eliminación de usuarios
        verbose_name=_("modified by"),
        related_name="modified_user",
        null=True,
        blank=True,  # Hacemos que el campo sea opcional
    )

    created_by = models.ForeignKey(
        "authentication.User",
        on_delete=models.SET_NULL,  # Usamos SET_NULL para manejar la eliminación de usuarios
        verbose_name=_("created by"),
        related_name="created_user",
        null=True,
        blank=True,  # Hacemos que el campo sea opcional
    )
    process_type = models.ForeignKey(
        "whitelabel.Process",
        on_delete=models.CASCADE,
        verbose_name=_("process_type"),
        null=True,
        blank=False,
    )
    visible = models.BooleanField(_("visible"), default=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    def deactivate_user(self):
        if not self.is_active:
            # Si ya está desactivado, no hacer nada
            return
        timestamp = timezone.now().strftime("%Y%m%d%H%M%S")
        self.username = f"{self.username}_deactivated_{timestamp}"
        self.is_active = False
        self.save()


class LoggedInUser(models.Model):
    """
    Modelo para almacenar la lista de usuarios conectados. En el módulo de señales se agregan y
    eliminan los usuarios de acuerdo a las sesiones activas.

    Esta implementación solo permite una sesión activa por usuario. Si en un futuro se quiere
    aumentar el número de sesiones, cambie la relación OneToOneField por OneToMany e implemente
    la limpieza de sesiones en el middleware.
    """

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="logged_in_user",
        verbose_name=_("user"),
    )
    session_key = models.CharField(
        max_length=33, blank=True, verbose_name=_("session key")
    )
