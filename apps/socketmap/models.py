from django.db import models


# Create your models here.
class Realtrackiot(models.Model):
    # No necesitas definir permisos en la clase Meta para los permisos básicos
    class Meta:
        verbose_name_plural = "realtrackiot"


class Widget(models.Model):
    # Asumiendo que "i" es un identificador único para cada widget, puedes usar un CharField.
    id = models.CharField(
        primary_key=True, max_length=255, unique=True, verbose_name="ID"
    )

    # Los campos "x", "y", "w" (width), "h" (height) pueden ser enteros.
    x = models.IntegerField(verbose_name="X Position")
    y = models.IntegerField(verbose_name="Y Position")
    w = models.IntegerField(verbose_name="Width")
    h = models.IntegerField(verbose_name="Height")

    COMPONENT_TYPES = (
        ("InformationWidget", "Information Widget"),
        # Agrega más tipos aquí según sea necesario
    )
    componentType = models.CharField(
        max_length=50, choices=COMPONENT_TYPES, verbose_name="Component Type"
    )

    class Meta:
        verbose_name_plural = "Widgets"  # Esto define el nombre plural del modelo en la interfaz de administración.

    def __str__(self):
        return f"Widget {self.id} - {self.componentType}"
