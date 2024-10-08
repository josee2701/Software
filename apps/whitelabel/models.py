""" Modelos asociados al módulo de marca blanca.

Este módulo crea los modelos de la base de datos utilizados para crear empresas, crear y asignar
servicios y crear y asignar simcards (junto con sus planes de datos).

Para una mayor referencia sobre la creación de modelos en Django, consulte
https://docs.djangoproject.com/en/4.1/topics/db/models/
"""

import base64
import os

import pycountry
from colorfield.fields import ColorField
from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.db import models
from django.utils.translation import gettext_lazy as _


class Theme(models.Model):
    """
    Define el modelo para los temas de personalización de las empresas. Tabla `whitelabe_theme`.
    """

    company = models.ForeignKey(
        "Company", on_delete=models.CASCADE, verbose_name=_("Company")
    )
    button_color = ColorField(
        format="hex",
        default="#3E5EF8",
        blank=True,
        null=True,
        verbose_name=_("button color"),
    )
    lock_screen_image = models.ImageField(
        upload_to="uploads/",
        validators=[FileExtensionValidator(["png", "jpg", "jpeg"])],
        blank=True,
        null=True,
        default="backgrounds/login-1.png",
        verbose_name=_("lock screen image"),
    )
    sidebar_image = models.ImageField(
        upload_to="uploads/",
        validators=[FileExtensionValidator(["png", "jpg", "jpeg"])],
        blank=True,
        null=True,
        default="backgrounds/sidebar-1.jpg",
        verbose_name=_("sidebar image"),
    )
    sidebar_color = ColorField(
        default="#000000",
        blank=True,
        null=True,
        verbose_name=_("sidebar color"),
    )
    opacity = models.CharField(
        max_length=3,
        verbose_name=_("opacity"),
        default="80",
    )

    def save(self, *args, **kwargs):
        company_id = self.company_id
        # Eliminar imágenes antiguas si se están actualizando
        if self.pk:
            old_instance = Theme.objects.get(pk=self.pk)
            # Eliminar sidebar_image si es diferente y pertenece a la misma compañía
            if self.sidebar_image and old_instance.sidebar_image != self.sidebar_image:
                if old_instance.company_id == company_id:
                    old_instance.sidebar_image.delete(save=False)
            # Eliminar lock_screen_image si es diferente y pertenece a la misma compañía
            if self.lock_screen_image and old_instance.lock_screen_image != self.lock_screen_image:
                if old_instance.company_id == company_id:
                    old_instance.lock_screen_image.delete(save=False)

        super().save(*args, **kwargs)


    class Meta:
        verbose_name_plural = _("themes")


class Module(models.Model):
    """
    Define el modelo para la creación de empresas. Tabla `whitelabel_company`.
    """

    company = models.ForeignKey(
        "Company", on_delete=models.CASCADE, verbose_name=_("Company")
    )
    group = models.ForeignKey(Group, on_delete=models.CASCADE, verbose_name=_("Group"))
    price = models.DecimalField(default=0, max_digits=10, decimal_places=2)

    class Meta:
        verbose_name_plural = _("modules")

    def __str__(self):
        return self.group.name


class MapType(models.Model):
    """
    Define el modelo para la creación de empresas. Tabla `whitelabel_company`.
    """

    name = models.CharField(max_length=60, blank=False, verbose_name=_("name"))

    class Meta:
        verbose_name_plural = _("map types")

    def __str__(self):
        return self.name


class CompanyTypeMap(models.Model):
    """
    Modelo que representa la relación entre una empresa y un tipo de mapa.
    """

    company = models.ForeignKey(
        "Company", on_delete=models.CASCADE, verbose_name=_("Company")
    )
    map_type = models.ForeignKey(
        "MapType", on_delete=models.CASCADE, verbose_name=_("Map type")
    )
    key_map = models.CharField(max_length=512, blank=False, verbose_name=_("key map"))

    class Meta:
        verbose_name_plural = _("company type maps")

    def __str__(self):
        """
        Devuelve el nombre del tipo de mapa.
        """
        return self.map_type.name

    def clean(self):
        """
        Realiza validaciones adicionales al limpiar los datos del modelo.
        """

        # Elimina espacios al inicio y al final de key_map
        self.key_map = self.key_map.strip()
        if not self.key_map:
            raise ValidationError(_("key map cannot be only spaces"))

    def save(self, *args, **kwargs):
        """
        Guarda el objeto en la base de datos.

        Encripta la clave antes de guardarla si no está ya encriptada.
        """
        if not self._is_encrypted(self.key_map):
            self.key_map = self.encrypt_key(self.key_map)
        super().save(*args, **kwargs)

    def encrypt_key(self, key):
        """
        Encripta una clave utilizando el algoritmo Fernet.

        Args:
            key (str): La clave a encriptar.

        Returns:
            str: La clave encriptada en formato base64.

        """
        # Inicializa el cifrado Fernet con la clave de encriptación
        cipher_suite = Fernet(settings.ENCRYPTION_KEY.encode())
        # Cifra la clave y la codifica en base64 para su almacenamiento
        encrypted_key = cipher_suite.encrypt(key.encode())
        return base64.urlsafe_b64encode(encrypted_key).decode()

    def decrypt_key(self, encrypted_key):
        """
        Desencripta una clave encriptada utilizando el algoritmo Fernet.

        Args:
            encrypted_key (str): La clave encriptada en formato base64.

        Returns:
            str: La clave desencriptada.

        """
        try:
            # Asegura que la cadena tenga el padding correcto para base64
            missing_padding = len(encrypted_key) % 4
            if missing_padding != 0:
                encrypted_key += "=" * (4 - missing_padding)
            # Inicializa el cifrado Fernet con la clave de encriptación
            cipher_suite = Fernet(settings.ENCRYPTION_KEY.encode())
            # Decodifica y desencripta la clave
            decrypted_key = cipher_suite.decrypt(
                base64.urlsafe_b64decode(encrypted_key)
            )
            return decrypted_key.decode()
        except InvalidToken:
            return encrypted_key

    def get_obscured_key(self):
        """
        Obtiene una versión parcialmente oculta de la clave.

        Returns:
            str: La clave parcialmente oculta.

        """
        try:
            decrypted_key = self.decrypt_key(self.key_map)
            return "*" * (len(decrypted_key) - 4) + decrypted_key[-4:]
        except InvalidToken:
            return self.key_map

    def _is_encrypted(self, key):
        """
        Verifica si una clave está encriptada.

        Args:
            key (str): La clave a verificar.

        Returns:
            bool: True si la clave está encriptada, False en caso contrario.

        """
        try:
            self.decrypt_key(key)
            return True
        except (InvalidToken, ValueError):
            return False


class Company(models.Model):
    """
    Define el modelo para la creación de empresas. Tabla `whitelabel_company`.
    """

    coin = models.ForeignKey("Coin", verbose_name=_("coin"), on_delete=models.CASCADE)
    nit = models.CharField(
        max_length=15,
        blank=False,
        verbose_name=_("nit"),
    )
    company_name = models.CharField(
        max_length=60, blank=False, verbose_name=_("Company name")
    )
    legal_representative = models.CharField(
        max_length=60, blank=False, verbose_name=_("legal representative")
    )
    address = models.CharField(max_length=60, blank=False, verbose_name=_("address"))
    country = models.CharField(
        max_length=100,
        blank=False,
        verbose_name=_("country"),
        choices=[(country.alpha_2, country.name) for country in pycountry.countries],
        default="Colombia",
    )
    city = models.CharField(max_length=60, blank=False, verbose_name=_("city"))
    phone_number = models.CharField(
        max_length=20, blank=True, verbose_name=_("phone number")
    )
    date_joined = models.DateField(auto_now_add=True, verbose_name=_("date joined"))
    last_updated = models.DateTimeField(
        auto_now=True,
        verbose_name=_("last updated"),
        null=True,
    )
    signed_contract = models.BooleanField(
        default=True, verbose_name=_("signed contract")
    )
    provider = models.ForeignKey(
        "self",
        related_name="customers",
        related_query_name="customer",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        verbose_name=_("provider"),
    )
    consultant = models.CharField(
        max_length=60, blank=True, verbose_name=_("consultant")
    )
    seller = models.CharField(max_length=60, blank=True, verbose_name=_("seller"))
    type_map = models.ManyToManyField(
        "MapType",
        through="CompanyTypeMap",
        verbose_name=_("type map"),
    )
    company_logo = models.ImageField(
        upload_to="uploads/",
        validators=[FileExtensionValidator(["png", "jpg"])],
        blank=True,
        null=True,
        verbose_name=_("company logo"),
    )
    modules = models.ManyToManyField(
        Group,
        blank=True,
        through="Module",
        related_name="modules",
        verbose_name=_("modules"),
    )
    actived = models.BooleanField(default=True, verbose_name=_("actived"))
    visible = models.BooleanField(default=True, verbose_name=_("visible"))
    modified_by = models.ForeignKey(
        "authentication.User",
        on_delete=models.CASCADE,
        verbose_name=_("modified by"),
        related_name="modified_companies",
        null=True,
    )

    created_by = models.ForeignKey(
        "authentication.User",
        on_delete=models.CASCADE,
        verbose_name=_("created by"),
        related_name="created_companies",
        null=True,
    )
    class Meta:
        verbose_name = _("Company")
        verbose_name_plural = _("Companies")

    def __str__(self):
        """
        La función __str__ es una función especial que se llama cuando imprime un objeto.

        La función __str__ es una función especial
        :return: El nombre Commercial del producto.
        """
        return self.company_name

    @classmethod
    def from_pycountry(cls, country):
        return cls(country=country.name)

    def __iter__(self):
        return iter((self.country,))

    def save(self, *args, **kwargs):
        """
        Guarda la instancia del modelo en la base de datos.

        Si la instancia de Company es nueva, su pk será None. En ese caso, se crea una nueva instancia de Process
        asociada a la compañía recién creada.

        :param args: Argumentos posicionales adicionales.
        :param kwargs: Argumentos de palabras clave adicionales.
        """
        # Si la instancia de Company es nueva, su pk será None
        is_new = self.pk is None
        super().save(*args, **kwargs)

        # Si la instancia de Company es nueva, crea una nueva instancia de Process
        if is_new:
            Process.objects.create(
                company=self, process_type="Admin", created_by_id=1, modified_by_id=1
            )


class Coin(models.Model):
    name = models.CharField(_("name"), max_length=50)

    def __str__(self):
        return self.name


class Process(models.Model):
    process_type = models.CharField(max_length=200)
    company = models.ForeignKey(
        "Company",
        on_delete=models.CASCADE,
        verbose_name=_("Company"),
        null=True,
    )
    modified_by = models.ForeignKey(
        "authentication.User",
        on_delete=models.CASCADE,
        verbose_name=_("modified by"),
        related_name="modified_process",
        null=True,
    )

    created_by = models.ForeignKey(
        "authentication.User",
        on_delete=models.CASCADE,
        verbose_name=_("created by"),
        related_name="created_process",
        null=True,
    )
    visible = models.BooleanField(default=True, verbose_name=_("visible"))

    def __str__(self):
        return self.process_type


class Ticket(models.Model):
    PRIORITY_CHOICES = [
        ("Low", _("Low")),
        ("Medium", _("Medium")),
        ("High", _("High")),
    ]

    created_by = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        null=True,  # Permite que el campo sea nulo
        blank=True,  # Permite que el campo esté en blanco en los formularios
    )
    company = models.ForeignKey(
        "Company",
        on_delete=models.CASCADE,
        verbose_name=_("Company"),
        null=True,
    )
    subject = models.CharField(max_length=200)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES)

    assign_to = models.ForeignKey(
        "authentication.User",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="assigned_tickets",
    )
    status = models.BooleanField(default=True, verbose_name="Open")
    created_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True, verbose_name="closed at")
    last_comment = models.DateTimeField(auto_now=True)

    process_type = models.ForeignKey(
        Process,
        on_delete=models.CASCADE,
        verbose_name=_("process_type"),
        null=True,  # permite que el campo sea nulo
        blank=True,  # permite que el campo esté en blanco en los formularios
    )

    provider_company = models.ForeignKey(
        "Company",
        on_delete=models.CASCADE,
        related_name="provider_tickets",
        verbose_name=_("Provider Company"),
        null=True,
    )

    customer_company = models.ForeignKey(
        "Company",
        on_delete=models.CASCADE,
        related_name="customer_tickets",
        verbose_name=_("Customer Company"),
        null=True,
    )

    rating = models.IntegerField(null=True, verbose_name="rating")


class Message(models.Model):
    ticket = models.ForeignKey(
        Ticket, on_delete=models.CASCADE, related_name="messages"
    )
    user = models.ForeignKey(  # Campo para referenciar al usuario que creó el mensaje
        "authentication.User",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="messages",
    )

    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)


class Attachment(models.Model):
    ticket = models.ForeignKey(
        Ticket, on_delete=models.CASCADE, related_name="attachments"
    )
    file = models.FileField(
        upload_to="ticket_attachments/",
        null=True,
        blank=True,
        validators=[
            FileExtensionValidator(
                [
                    "pdf",
                    "docx",
                    "doc",
                    "txt",
                    "xlsx",
                    "xls",
                    "zip",
                    "exe",
                    "jpg",
                    "png",
                    "jpeg",
                    "msg",
                    "cfg",
                    "mp4",
                    "rar",
                    "xim",
                    "eml",
                    "xml",
                ]
            ),
        ],
    )
    created_at = models.DateTimeField(auto_now_add=True)
    message = models.ForeignKey(
        Message, on_delete=models.CASCADE, related_name="attachments"
    )


class Comment(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
