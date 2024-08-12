"""
Configuración principal del proyecto.

Generado con 'django-admin startproject' using Django 4.1.

Para una lista completa sobre los valores de configuración, consulte
https://docs.djangoproject.com/en/4.0/ref/settings/

Para una lista de chequeo para llevar el proyecto a producción, consulte
https://docs.djangoproject.com/en/4.0/howto/deployment/checklist/
"""

import os
from urllib.parse import urlparse

import environ
from django.utils.translation import gettext_lazy as _

# Inicializa las variables de entorno
env = environ.Env()
environ.Env.read_env()

# Configuración central
# -----------------------------------------------------------------

# Establece los directorios de la aplicación
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
APPS_DIR = os.path.join(BASE_DIR, "apps")

# Clave secreta para la seguridad de Django
SECRET_KEY = os.environ.get("SECRET_KEY")

# Clave de encriptación (si se usa en la aplicación)
ENCRYPTION_KEY = os.environ.get("ENCRYPTION_KEY")

# Modo de depuración (debe estar desactivado en producción)
DEBUG = os.getenv("DEBUG", "0") == "1"

# Hosts permitidos para el despliegue de la aplicación
# SECURITY WARNING: don't run with debug turned on in production!
ALLOWED_HOSTS = ['software-h42n.onrender.com', 'localhost', '127.0.0.1']

# Aplicaciones instaladas
# -----------------------------------------------------------------

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
    "modeltranslation",
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
    "rosetta",
    "storages",
    "any_imagefield",
    "django_filters",
    "channels",
    "channels_redis",
    "corsheaders",
]

INSTALLED_APPS = LOCAL_APPS + DJANGO_APPS + THIRD_PARTY_APPS

# Configuración de middleware
# -----------------------------------------------------------------

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "apps.authentication.middleware.ExpireSessionOnBrowserCloseMiddleware",
    "apps.authentication.middleware.SingleSessionPerUserMiddleware",
    "apps.authentication.middleware.ManejoUsuarioNoExistenteMiddleware",
]


# Configuración de URLs y aplicaciones
# -----------------------------------------------------------------

ROOT_URLCONF = "config.urls"
ASGI_APPLICATION = "config.asgi.application"
# WSGI_APPLICATION = "config.wsgi.application"

# Configuración de templates
# -----------------------------------------------------------------

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(APPS_DIR, "templates")],
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
                "django.template.context_processors.i18n",
            ],
            "libraries": {
                "staticfiles": "django.templatetags.static",
            },
        },
    }
]

# Configuración de Crispy Forms
# -----------------------------------------------------------------

CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"
CRISPY_CLASS_CONVERTERS = {"textinput": "textinput inputtext"}
FORM_RENDERER = "django.forms.renderers.DjangoTemplates"

# Configuración de bases de datos
# -----------------------------------------------------------------

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.path.join(BASE_DIR, "db.sqlite3"),
    },
}

DB_ENGINE = os.environ.get("SQLSERVER_ENGINE")
DB_HOST = os.environ.get("SQLSERVER_SERVER")
DB_NAME = os.environ.get("SQLSERVER_NAME")
DB_USER = os.environ.get("SQLSERVER_USER")
DB_PASSWORD = os.environ.get("SQLSERVER_PASSWORD")
DB_PORT = os.environ.get("SQLSERVER_PORT")
DB_IS_AVAIL = all([DB_ENGINE, DB_HOST, DB_NAME, DB_USER, DB_PASSWORD, DB_PORT])

if DB_IS_AVAIL:
    DATABASES = {
        "default": {
            "ENGINE": DB_ENGINE,
            "HOST": DB_HOST,
            "NAME": DB_NAME,
            "USER": DB_USER,
            "PASSWORD": DB_PASSWORD,
            "PORT": DB_PORT,
            
        },
    }

# Configuración de Redis para Channels
# -----------------------------------------------------------------

REDIS_URL = os.environ.get("REDIS_URL", "redis://redis-cip:6379")
parsed_url = urlparse(REDIS_URL)

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [("redis-cip", 6379)],
        },
    },
}

# Configuración de idioma e internacionalización
# -----------------------------------------------------------------

LANGUAGE_CODE = "en"

LANGUAGES = [
    ("en", _("English")),
    ("es", _("Spanish")),
    ("it", _("Italian")),
    # ("es-co", _("Spanish (Colombia)")),
    # ("es-mx", _("Spanish (Mexico)")),
    # ("es-es", _("Spanish (Spain)")),
]

LOCALE_PATHS = [
    os.path.join(BASE_DIR, "locale"),  # Ruta donde se encuentran las traducciones
]

TIME_ZONE = "America/Bogota"
USE_I18N = True
USE_L10N = True
USE_TZ = False  # False si presenta problemas el driver de conexión a SQL Server

# Configuración de autenticación
# -----------------------------------------------------------------

SITE_ID = 1
AUTH_USER_MODEL = "authentication.User"
LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "main"
LOGOUT_REDIRECT_URL = "index"

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {
            "min_length": 8,
        },
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

AUTHENTICATION_BACKENDS = (
    "django.contrib.auth.backends.ModelBackend",
    "guardian.backends.ObjectPermissionBackend",
)


# Configuración de archivos estáticos y media
# -----------------------------------------------------------------

STATICFILES_DIRS = [
    # os.path.join(BASE_DIR, "static"),
    os.path.join(APPS_DIR, "static"),
    os.path.join(APPS_DIR, "build", "static"),
]
MEDIA_ROOT = os.path.join(APPS_DIR, "media")
MEDIA_URL = "media/"
STATIC_URL = "static/"
# Archivos Static para producción
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
AZURE_ACCOUNT_NAME = os.environ.get("AZURE_ACCOUNT_NAME")
AZURE_BLOB_AVAIL = all([AZURE_ACCOUNT_NAME])
if AZURE_BLOB_AVAIL:
    AZURE_CUSTOM_DOMAIN = f"{AZURE_ACCOUNT_NAME}.blob.core.windows.net"
    AZURE_LOCATION = ""
    DEFAULT_FILE_STORAGE = "config.azureblob.AzureMediaStorage"
    STATICFILES_STORAGE = "config.azureblob.AzureStaticStorage"
    STATIC_LOCATION = "static"
    MEDIA_LOCATION = "media"
    STATIC_URL = f"https://{AZURE_CUSTOM_DOMAIN}/{STATIC_LOCATION}/"
    STATIC_ROOT = STATIC_URL
    MEDIA_URL = f"https://{AZURE_CUSTOM_DOMAIN}/{MEDIA_LOCATION}/"
    MEDIA_ROOT = MEDIA_URL
    AZURE_OVERWRITE_FILES = True
STATICFILES_DIRS = [
    os.path.join(APPS_DIR, "static"),
    os.path.join(APPS_DIR, "media"),
]
# STATIC_URL = "/app/static/"
# # Archivos Static para producción
STATICFILES_FINDERS = [
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
]
# -- Cache
# https://docs.djangoproject.com/en/4.0/topics/cache/#
# Configuración de CORS y CSRF
# -----------------------------------------------------------------

CORS_ALLOWED_ORIGINS = [
    "http://127.0.0.1",
    "http://localhost",
    "http://localhost:3000",
    "http://www.gpsmobile.pro",
    "http://*.gpsmobile.pro",
    "http://www.gpsmobile.pro",
    "https://gpsmobile.pro",
    "https://www.gpsmobile.pro",
    "https://*.gpsmobile.pro",
    "https://software-h42n.onrender.com",
]

CSRF_TRUSTED_ORIGINS = [
    "http://127.0.0.1",
    "http://localhost",
    "http://localhost:3000",
    "http://www.gpsmobile.pro",
    "http://*.gpsmobile.pro",
    "http://www.gpsmobile.pro",
    "https://gpsmobile.pro",
    "https://www.gpsmobile.pro",
    "https://*.gpsmobile.pro",
    "https://software-h42n.onrender.com",
]


CSRF_COOKIE_SECURE = True if not DEBUG else False
SESSION_COOKIE_SECURE = True if not DEBUG else False


# # Dominio de la cookie CSRF
# CSRF_COOKIE_DOMAIN = 'gpsmobile.pro'

# SESSION_COOKIE_DOMAIN = 'gpsmobile.pro' # Reemplaza con tu dominio real

# Configuración de sesiones
# -----------------------------------------------------------------
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# Asegúrate de que las cookies CSRF y de sesión estén configuradas adecuadamente
CSRF_USE_SESSIONS = True

# Configuración de Django REST Framework
# -----------------------------------------------------------------

REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "rest_framework.schemas.coreapi.AutoSchema",
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.AllowAny",
    ],
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
}

# Configuración del servicio de email
# -----------------------------------------------------------------

# Configuración del servicio de email (Gmail)
EMAIL_BACKEND = env('EMAIL_BACKEND', default='django.core.mail.backends.smtp.EmailBackend')
EMAIL_HOST = env('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_HOST_USER = env('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD')
EMAIL_PORT = env.int('EMAIL_PORT', default=587)
EMAIL_USE_TLS = env.bool('EMAIL_USE_TLS', default=True)

# Configuración de paginación
# -----------------------------------------------------------------

DEFAULT_PAGINATION = 10

# Configuración de logging
# -----------------------------------------------------------------

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "loggers": {
        "channels": {
            "handlers": ["console"],
            "level": "DEBUG",
        },
    },
}

# Configuración del campo por defecto para modelos
# -----------------------------------------------------------------

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
