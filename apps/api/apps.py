"""
Aplicación de API

Esta es la configuración de la aplicación API que es llamada al archivo de configuración global.
"""


from django.apps import AppConfig


class ApiConfig(AppConfig):
    """
    Define el nombre y etiqueta con las que identificará la aplicación en la configuración global.
    """

    # default_auto_field = 'django.db.models.BigAutoField'
    name = "apps.api"
    label = "api"
