"""
Aplicación de reportería en tiempo real.

Módulo que define la configuración de la aplicación.
"""

from django.apps import AppConfig


class RealtimeConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.realtime"
    label = "realtime"
