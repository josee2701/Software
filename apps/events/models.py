import os

from azure.storage.blob import BlobServiceClient
from colorfield.fields import ColorField
from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class EventFeature(models.Model):
    """
    Modelo de la tabla event_feautures. Dado un evento predefinido se almacenan las
    características específicadas por el usuario de cada empresa cliente.
    """

    PRIORITY_SOUNDS_CHOICES = [
        ("Low", _("Low")),
        ("Medium", _("Medium")),
        ("High", _("High")),
    ]

    # Configurar las credenciales de acceso a Azure Blob Storage
    AZURE_ACCOUNT_NAME = os.environ.get("AZURE_ACCOUNT_NAME")
    AZURE_ACCOUNT_KEY = os.environ.get("AZURE_ACCOUNT_KEY")
    AZURE_CONTAINER_NAME = "alarm_sounds"  # Nombre del contenedor de sonidos de alarma
    AZURE_CUSTOM_DOMAIN = f"{AZURE_ACCOUNT_NAME}.blob.core.windows.net"
    azure_blob_base_url = f"https://{AZURE_CUSTOM_DOMAIN }/{AZURE_CONTAINER_NAME}/"

    # Crear un cliente de servicio de blobs
    blob_service_client = BlobServiceClient(
        account_url=f"https://{AZURE_CUSTOM_DOMAIN}",
        credential=AZURE_ACCOUNT_KEY,
    )

    # Obtener una referencia al contenedor donde se almacenan los archivos de sonido de alarma
    blob_container_client = blob_service_client.get_container_client(
        settings.MEDIA_LOCATION
    )

    # Lista todos los blobs en el contenedor
    blobs_list = blob_container_client.list_blobs()

    # Filtra los blobs que corresponden a los sonidos de alarma
    alarm_sound_files = {
        blob.name.split("/")[-1].split(".")[
            0
        ]: f"{settings.MEDIA_URL.strip('/')}/{blob.name}"
        for blob in blobs_list
        if blob.name.endswith(".wav")
    }

    # Crear una lista de tuplas con el índice y la URL completa del archivo
    TYPE_ALARM_SOUNDS_CHOICES = [(url, name) for name, url in alarm_sound_files.items()]

    event = models.ForeignKey(
        "event", on_delete=models.CASCADE, verbose_name=_("event"), default=1
    )
    company = models.ForeignKey(
        "whitelabel.Company",
        on_delete=models.CASCADE,
        verbose_name=_("company"),
        null=True,
    )
    alias = models.CharField(
        max_length=30,
        verbose_name=_("Nombre Evento"),
    )
    central_alarm = models.BooleanField(
        default=False,
        verbose_name=_("Alarma Central"),
    )
    user_alarm = models.BooleanField(
        default=False,
        verbose_name=_("user notification"),
        null=True,
    )
    start_time = models.TimeField(
        verbose_name=_("start time"),
        blank=True,
        null=True,
    )
    end_time = models.TimeField(
        verbose_name=_("end time"),
        blank=True,
        null=True,
    )
    modified_by = models.ForeignKey(
        "authentication.User",
        on_delete=models.CASCADE,
        verbose_name=_("modified by"),
        null=True,
        default=1,
    )
    last_update = models.DateTimeField(
        verbose_name="last update",
        auto_now=True,
    )
    email_alarm = models.BooleanField(
        default=False,
        verbose_name=_("email notification"),
    )
    color = ColorField(
        blank=True,
        null=True,
        verbose_name=_("alarm color"),
    )
    alarm_sound = models.BooleanField(
        verbose_name="alarm",
    )
    sound_priority = models.CharField(
        max_length=6,
        choices=PRIORITY_SOUNDS_CHOICES,
        verbose_name=_("priority"),
        blank=True,
        null=True,
    )
    type_alarm_sound = models.CharField(
        max_length=255,
        choices=TYPE_ALARM_SOUNDS_CHOICES,
        verbose_name=_("sound type"),
        blank=True,
        null=True,
    )

    visible = models.BooleanField(default=True, verbose_name=_("visible"))

    def __str__(self):
        return f"ID Event predefined: {self.event} | Event: {self.alias}"


class Event(models.Model):
    """
    Modelo de la tabla event. Los campos "number" y "name" identifican al evento bajo el
    código unificado de eventos predefinidos de AZ-Smart.
    """

    number = models.PositiveIntegerField(verbose_name=_("number"), unique=True)
    name = models.CharField(
        max_length=255,
        blank=False,
        verbose_name=_("name"),
    )
    # modified_by = models.ForeignKey(
    #     "authentication.User",
    #     on_delete=models.CASCADE,
    #     verbose_name=_("modified by"),
    #     default=1,
    # )
    last_updated = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("last updated"),
        null=True,
    )

    class Meta:
        ordering = ["number"]

    def __str__(self):
        return f"{self.number} Event: {self.name}"


class Alarm(models.Model):
    """
    Modelo de la tabla alarm. Los campos "number" y "name" identifican al evento bajo el
    código unificado de eventos predefinidos de AZ-Smart.
    """

    is_checked = models.BooleanField(
        default=False,
        null=True,
        verbose_name=_("check"),
    )
    company = models.ForeignKey(
        "whitelabel.Company",
        on_delete=models.CASCADE,
        verbose_name=_("company"),
        null=False,
    )
    device = models.ForeignKey(
        "realtime.Device",
        on_delete=models.CASCADE,
        blank=True,
        null=False,
        verbose_name=_("device"),
    )
    main_event = models.IntegerField(null=False, verbose_name=_("main event"))
    server_date = models.DateTimeField(null=False, verbose_name=_("server date"))
    signal_date = models.DateTimeField(
        null=False, auto_now_add=True, verbose_name=_("signal date")
    )
    odometer = models.FloatField(null=False, verbose_name=_("odometer"))
    latitude = models.FloatField(null=False, verbose_name=_("latitude"))
    longitude = models.FloatField(null=False, verbose_name=_("longitude"))
    calculated_speed = models.PositiveSmallIntegerField(
        null=False, verbose_name=_("calculated speed")
    )
    angle = models.PositiveSmallIntegerField(null=False, verbose_name=_("angle"))
    user = models.ForeignKey(
        "authentication.User",
        on_delete=models.CASCADE,
        verbose_name=_("user"),
        null=True,
        default=1,
        related_name="alarms",  # Nombre único para la consulta inversa
    )
    probability = models.DecimalField(
        max_digits=5, decimal_places=2, verbose_name=_("probability"), null=True
    )
    real_prediction = models.DecimalField(
        max_digits=5, decimal_places=2, verbose_name=_("real prediction"), null=True
    )
    real = models.BooleanField(default=False, verbose_name=_("real"), null=True)
    alarm_type = models.BooleanField(
        default=False,
        verbose_name=_("alarm type"),
        null=False,
    )

    last_update = models.DateTimeField(
        verbose_name="last update", auto_now=True, null=False
    )

    class Meta:
        ordering = ["server_date"]

    def __str__(self):
        return f"{self.company} Alarm: {self.main_event}"


# class UEC(models.Model):
#     """
#     Define el modelo para el código único de eventos (Unified Event Code - UEC). Normaliza el
#     número de eventos a cada uno de los elementos IO que arrojan los tipos de dispositivos. Tabla
#     `realtime_uec`.
#     """

#     # device_type = models.ForeignKey(
#     #     "DeviceType", on_delete=models.CASCADE, verbose_name=_("device type")
#     # )
#     familymodel = models.ForeignKey(
#         "realtime.FamilyModelUEC",
#         on_delete=models.CASCADE,
#         verbose_name=_("family model"),
#         default=1,
#     )
#     event_number = models.ForeignKey(
#         "Event", on_delete=models.CASCADE, verbose_name=_("event number")
#     )
#     io_element = models.CharField(verbose_name="IO element", max_length=25)

#     def __str__(self):
#         return f"{self.familymodel}: {self.event_number} --> {self.io_element}"
