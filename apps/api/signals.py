# signals.py
from django.contrib.auth import get_user_model
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import (
    LogActividad,  # Asegúrate de ajustar la ruta de importación según tu estructura de proyecto
)

User = get_user_model()


def conectar_modelo_signals(model):
    @receiver(post_save, sender=model)
    def registrar_creacion_actualizacion(sender, instance, created, **kwargs):
        usuario = getattr(instance, "usuario", None) or User.objects.get(
            username="sistema"
        )  # Asume un usuario por defecto si no está definido
        accion = "Creado" if created else "Actualizado"
        LogActividad.objects.create(
            usuario=usuario,
            accion=accion,
            descripcion=f"{accion} en {sender.__name__} id {instance.pk}",
        )

    @receiver(post_delete, sender=model)
    def registrar_eliminacion(sender, instance, **kwargs):
        usuario = getattr(instance, "usuario", None) or User.objects.get(
            username="sistema"
        )
        LogActividad.objects.create(
            usuario=usuario,
            accion="Eliminado",
            descripcion=f"Eliminado {sender.__name__} id {instance.pk}",
        )
