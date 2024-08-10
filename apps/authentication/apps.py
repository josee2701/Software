"""
Aplicación de autenticación.

Módulo que define la configuración de la aplicación.
"""

from django.apps import AppConfig


class AuthenticationConfig(AppConfig):
    """
    Define el nombre y etiqueta con las que identificará la aplicación en la configuración
    global. Cuando la aplicación esté lista, importe el módulo de señales.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.authentication"
    label = "authentication"

    def ready(self):
        # Conecta implícitamente los manejadores de señales decorados con @receptor.
        from . import signals
