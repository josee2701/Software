# ASGI config for config project.

import os
import pathlib

import dotenv
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from django.core.asgi import get_asgi_application
from django.urls import path

from apps.socketmap import consumers  # Importación optimizada

# Carga las variables de entorno desde el archivo .env ubicado en la raíz del proyecto
CURRENT_DIR = pathlib.Path(__file__).resolve().parent
BASE_DIR = CURRENT_DIR.parent
ENV_FILE_PATH = BASE_DIR / ".env"
dotenv.read_dotenv(str(ENV_FILE_PATH))

# Establece el módulo de configuración de Django para la aplicación ASGI
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

# Obtiene la aplicación ASGI de Django para manejar solicitudes HTTP
django_application = get_asgi_application()

# Define la aplicación ASGI con soporte para HTTP y WebSocket
application = ProtocolTypeRouter(
    {
        "http": django_application,  # Uso directo de django_application para HTTP
        # Configuración del manejador de WebSocket
        # Wrapped in AllowedHostsOriginValidator to ensure security on WebSocket connections
        "websocket": AuthMiddlewareStack(
            URLRouter(
                [
                    # Define la ruta para el consumidor WebSocket
                    path("ws/gps/", consumers.GPSConsumer.as_asgi()),
                ]
            )
        ),
    }
)
