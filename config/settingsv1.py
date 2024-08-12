"""
Configuración principal del proyecto Django.

Para una lista completa sobre los valores de configuración, consulta:
https://docs.djangoproject.com/en/4.0/ref/settings/

Para una lista de chequeo para despliegue en producción, consulta:
https://docs.djangoproject.com/en/4.0/howto/deployment/checklist/
"""

import os
from urllib.parse import urlparse

import environ
from django.utils.translation import gettext_lazy as _

# Inicializa las variables de entorno
# -----------------------------------------------------------------
# Carga automáticamente el archivo .env y establece las variables de entorno.
env = environ.Env()
environ.Env.read_env()

# Configuración básica
# -----------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(__file__))  # Directorio base del proyecto
APPS_DIR = os.path.join(BASE_DIR, "apps")  # Directorio donde se encuentran las aplicaciones

SECRET_KEY = os.environ.get("SECRET_KEY")  # Clave secreta para la seguridad de Django
DEBUG = env.bool("DEBUG", default=False)  # Modo de depuración
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=[])  # Hosts permitidos para el despliegue

# Aplicaciones instaladas
# -----------------------------------------------------------------
# Aplicaciones locales, de Django, y de terceros organizadas por grupos.
LOCAL_APPS = [
    "apps.authentication",  # Modelo de usuario personalizado
    "apps.log",
    "apps.checkpoints",
    "apps.events",
    "apps.socketmap",
    "apps.realtime",
    "apps.whitelabel",
    "apps.powerbi",
]

DJANGO_APPS = [
    "modeltranslation",  # Traducción de modelos
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.sites",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.forms",
]

THIRD_PARTY_APPS = [
    "colorfield",
    "crispy_forms",
    "crispy_bootstrap5",
    "guardian",
    "django_extensions",
    "rest_framework",
    "rosetta",  # Interfaz de traducción
    "storages",  # Soporte para almacenamiento en la nube
    "any_imagefield",  # Campo de imagen versátil
    "django_filters",  # Filtros de Django para REST Framework
    "channels",  # Soporte para WebSockets
    "channels_redis",  # Backend de Channels para Redis
    "corsheaders",  # Soporte para CORS
]

INSTALLED_APPS = LOCAL_APPS + DJANGO_APPS + THIRD_PARTY_APPS

# Configuración de middleware
# -----------------------------------------------------------------
# Middleware manejan solicitudes y respuestas en Django.
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",  # Manejo de CORS
    "django.middleware.locale.LocaleMiddleware",  # Gestión de idioma
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "apps.authentication.middleware.ExpireSessionOnBrowserCloseMiddleware",
    "apps.authentication.middleware.SingleSessionPerUserMiddleware",
    "apps.authentication.middleware.ManejoUsuarioNoExistenteMiddleware",
    "middleware.htmx_middleware.HTMXMiddleware",  # Soporte para HTMX
]

# Configuración de URL y WSGI/ASGI
# -----------------------------------------------------------------
# Define cómo Django maneja las solicitudes de URL.
ROOT_URLCONF = "config.urls"
ASGI_APPLICATION = "config.asgi.application"  # ASGI para manejo de WebSockets
# WSGI_APPLICATION = "config.wsgi.application"  # Habilitar solo si usas WSGI en lugar de ASGI

# Configuración de templates
# -----------------------------------------------------------------
# Configura la carga y renderizado de plantillas.
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(APPS_DIR, "templates")],  # Directorio de plantillas
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.template.context_processors.media",
                "django.template.context_processors.csrf",
                "django.template.context_processors.static",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.i18n",  # Procesador para internacionalización
            ],
            "libraries": {
                "staticfiles": "django.templatetags.static",  # Carga de archivos estáticos
            },
        },
    }
]

# Configuración de bases de datos
# -----------------------------------------------------------------
# Configuración de la base de datos. Soporta múltiples backends.
DATABASES = {
    "default": {
        "ENGINE": env("SQLSERVER_ENGINE", default="django.db.backends.sqlite3"),
        "NAME": os.path.join(BASE_DIR, "db.sqlite3"),
        "HOST": env("SQLSERVER_SERVER", default=""),
        "USER": env("SQLSERVER_USER", default=""),
        "PASSWORD": env("SQLSERVER_PASSWORD", default=""),
        "PORT": env("SQLSERVER_PORT", default=""),
        "OPTIONS": {"driver": "ODBC Driver 18 for SQL Server"},
    }
}

# Configuración de Redis y Channels
# -----------------------------------------------------------------
# Configuración para manejar WebSockets usando Redis.
REDIS_URL = env("REDIS_URL", default="redis://localhost:6379")
parsed_url = urlparse(REDIS_URL)

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {"hosts": [(parsed_url.hostname, parsed_url.port)]},
    },
}

# Configuración de idioma e internacionalización
# -----------------------------------------------------------------
# Soporte para múltiples idiomas y localización.
LANGUAGE_CODE = "en"
LANGUAGES = [
    ("en", _("English")),
    ("es", _("Spanish")),
    ("it", _("Italian")),
]

LOCALE_PATHS = [os.path.join(BASE_DIR, "locale")]  # Directorio de archivos de localización

TIME_ZONE = "America/Bogota"
USE_I18N = True  # Activar internacionalización
USE_L10N = True  # Activar formatos locales
USE_TZ = True  # Activar soporte para zonas horarias

# Configuración de autenticación
# -----------------------------------------------------------------
# Configura cómo se manejan los usuarios y autenticación.
SITE_ID = 1
AUTH_USER_MODEL = "authentication.User"
LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "main"
LOGOUT_REDIRECT_URL = "index"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 8}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

AUTHENTICATION_BACKENDS = (
    "django.contrib.auth.backends.ModelBackend",
    "guardian.backends.ObjectPermissionBackend",  # Soporte para permisos a nivel de objeto
)

# Configuración de archivos estáticos y media
# -----------------------------------------------------------------
# Configuración para servir archivos estáticos y medios.

STATIC_URL = "/static/"  # URL para archivos estáticos en desarrollo
MEDIA_URL = "/media/"  # URL para archivos de media en desarrollo

if not DEBUG:
    AZURE_ACCOUNT_NAME = env("AZURE_ACCOUNT_NAME")
    AZURE_CUSTOM_DOMAIN = f"{AZURE_ACCOUNT_NAME}.blob.core.windows.net"
    STATIC_URL = f"https://{AZURE_CUSTOM_DOMAIN}/static/"
    MEDIA_URL = f"https://{AZURE_CUSTOM_DOMAIN}/media/"
    STATICFILES_STORAGE = "config.azureblob.AzureStaticStorage"
    DEFAULT_FILE_STORAGE = "config.azureblob.AzureMediaStorage"

STATICFILES_DIRS = [
    os.path.join(APPS_DIR, "static"),  # Directorio de archivos estáticos locales
]
MEDIA_ROOT = os.path.join(APPS_DIR, "media")  # Directorio para archivos de media

# Configuración de CORS y CSRF
# -----------------------------------------------------------------
# Configuración para permitir solicitudes de ciertos dominios.
CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS", default=[
    "http://127.0.0.1",
    "http://localhost",
    "http://localhost:3000",
    "http://www.gpsmobile.pro",
    "https://gpsmobile.pro",
])

CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[
    "http://127.0.0.1",
    "http://localhost",
    "http://localhost:3000",
    "http://www.gpsmobile.pro",
    "https://gpsmobile.pro",
])

CSRF_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_SECURE = not DEBUG

# Configuración de Django REST Framework
# -----------------------------------------------------------------
# Configuración del API REST para el proyecto.
REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "rest_framework.schemas.coreapi.AutoSchema",
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework.authentication.SessionAuthentication",  # Autenticación basada en sesiones
        "rest_framework.authentication.TokenAuthentication",  # Autenticación con tokens
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",  # Requiere autenticación para todas las vistas
    ),
    "DEFAULT_PARSER_CLASSES": (
        "rest_framework.parsers.JSONParser",  # Parser para JSON
        "rest_framework.parsers.FormParser",  # Parser para formularios
        "rest_framework.parsers.MultiPartParser",  # Parser para archivos
    ),
    "DEFAULT_RENDERER_CLASSES": (
        "rest_framework.renderers.JSONRenderer",  # Renderizador para JSON
        "rest_framework.renderers.BrowsableAPIRenderer",  # Renderizador navegable
    ),
    "DEFAULT_FILTER_BACKENDS": (
        "django_filters.rest_framework.DjangoFilterBackend",  # Soporte para filtros
    ),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 10,  # Tamaño de página para la paginación
}

# Configuración de almacenamiento en Azure (si aplicable)
# -----------------------------------------------------------------
if not DEBUG:
    AZURE_ACCOUNT_NAME = env("AZURE_ACCOUNT_NAME")
    AZURE_ACCOUNT_KEY = env("AZURE_ACCOUNT_KEY")
    AZURE_CONTAINER = env("AZURE_CONTAINER")
    
    DEFAULT_FILE_STORAGE = "storages.backends.azure_storage.AzureStorage"
    AZURE_CUSTOM_DOMAIN = f"{AZURE_ACCOUNT_NAME}.blob.core.windows.net"
    MEDIA_URL = f"https://{AZURE_CUSTOM_DOMAIN}/media/"
    STATICFILES_STORAGE = "storages.backends.azure_storage.AzureStaticStorage"
    STATIC_URL = f"https://{AZURE_CUSTOM_DOMAIN}/static/"

# Configuración de logging
# -----------------------------------------------------------------
# Configura cómo se manejan los logs en el proyecto.
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "INFO",
        },
        "myproject": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": True,
        },
    },
}

# Configuración adicional
# -----------------------------------------------------------------
# Cualquier otra configuración personalizada que necesites.
# Por ejemplo, si usas Django Extensions para herramientas de desarrollo:
SHELL_PLUS = "ipython"  # Para habilitar IPython en Django Extensions

# Información para correo:
#https://docs.djangoproject.com/es/5.0/ref/settings/#email-backend

EMAIL_BACKEND = env('EMAIL_BACKEND')
EMAIL_HOST = env('EMAIL_HOST')
EMAIL_PORT = int(env('EMAIL_PORT'))
EMAIL_USE_TLS = env('EMAIL_USE_TLS') == 'True'
EMAIL_USE_SSL = False
EMAIL_HOST_USER = env('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD')

# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
