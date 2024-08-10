from django.db import models
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

# En algún lugar central como ready() en apps.py o al final de models.py
from apps.events.models import Event, EventFeature
from apps.realtime.models import AVLData, Device, Io_items_report, Vehicle


class LogActividad(models.Model):
    usuario = models.ForeignKey("authentication.User", on_delete=models.CASCADE)
    accion = models.CharField(max_length=255)
    descripcion = models.TextField()
    fecha_hora = models.DateTimeField(auto_now_add=True)
    detalles_adicionales = models.TextField(blank=True, null=True)

    def __str__(self):
        return (
            f"{self.usuario} realizó una acción de '{self.accion}' el {self.fecha_hora}"
        )


modelos_a_monitorizar = [Event, EventFeature, AVLData, Device, Io_items_report, Vehicle]

# for modelo in modelos_a_monitorizar:
#     conectar_modelo_signals(modelo)
