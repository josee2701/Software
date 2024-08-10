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
        verbose_name=_("sound type"),
        blank=True,
        null=True,
    )
    custom_alarm_sound = models.FileField(
        upload_to='custom_sounds/',
        verbose_name=_("custom_alarm_sound"),
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
    modified_by = models.ForeignKey(
        "authentication.User",
        on_delete=models.CASCADE,
        verbose_name=_("modified by"),
        default=1,
    )
    last_updated = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("last updated"),
        null=True,
    )
    visible = models.BooleanField(default=True, verbose_name=_("visible"))

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
