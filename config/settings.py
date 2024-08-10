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

env = environ.Env()
# Leer .env
environ.Env.read_env()

from django.utils.translation import gettext_lazy as _

# Configuración central
# -----------------------------------------------------------------
# https://docs.djangoproject.com/en/4.0/ref/settings/#core-settings


# Estable los directorios de la aplicación
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
APPS_DIR = os.path.join(BASE_DIR, "apps")

# Toma las variables de entorno desde el archivo .env
# environ.Env.read_env(os.path.join(BASE_DIR, ".env"))

# Emite la excepción establecida en ImproperlyConfigured si SECRET_KEY no se encuentra en .env
SECRET_KEY = os.environ.get("SECRET_KEY")

# False si DEBUG no está en .env (de acuerdo a cast anterior)
DEBUG = str(os.environ.get("DEBUG")) == "1"

ENV_ALLOWED_HOST = os.environ.get("ENV_ALLOWED_HOST")
ALLOWED_HOSTS = []
if ENV_ALLOWED_HOST:
    ALLOWED_HOSTS = [ENV_ALLOWED_HOST]

# Definición de la aplicación
# -------------------------------

LOCAL_APPS = [
    "apps.authentication",  # Must be above `django.contrib.auth` because has a custom User model.
    "apps.api",
    "apps.checkpoints",
    "apps.events",
    "apps.socketmap",
    "apps.realtime",
    "apps.whitelabel",
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

THIRD_PARHY_APPS = [
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

INSTALLED_APPS = LOCAL_APPS + DJANGO_APPS + THIRD_PARHY_APPS

# DATE_INPUT_FORMATS = ["%B %d, %Y"]


# Django REST Framework
# ----------------------------------------------------------
# https://www.django-rest-framework.org/api-guide/settings/
# *** Queda pendiente hacer las configuraciones de seguridad CORS que sugiere el libro "Django
# for APIs" p. 50. ***

REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "rest_framework.schemas.coreapi.AutoSchema",
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.AllowAny",
    ],
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    # 'DEFAULT_AUTHENTICATION_CLASSES': [
    #     'rest_framework.authentication.SessionAuthentication',
    # ],
}


# -- Middleware
# https://docs.djangoproject.com/en/4.0/ref/settings/#middleware

# NOTA: el orden de los middlewares importa, por favor no lo cambie a menos que esté seguro de
# la implementación que está llevando a cabo.

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    # Habilita la configuración de multi-idiomas de la aplicación
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # Habilita la validación de sesión única por usuario
    "apps.authentication.middleware.SingleSessionPerUserMiddleware",
    "apps.authentication.middleware.ManejoUsuarioNoExistenteMiddleware",
]

CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",  # Agrega la URL de tu aplicación React en desarrollo
    # Otras URL permitidas pueden ir aquí
]

ROOT_URLCONF = "config.urls"

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

CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"

CRISPY_TEMPLATE_PACK = "bootstrap5"

CRISPY_CLASS_CONVERTERS = {"textinput": "textinput inputtext"}

FORM_RENDERER = "django.forms.renderers.DjangoTemplates"
ASGI_APPLICATION = "config.asgi.application"

# WSGI_APPLICATION = "config.wsgi.application"


# -- Bases de datos
# https://docs.djangoproject.com/en/4.0/ref/settings/#databases


DATABASES = {
    # SQL Server
    # "default": {
    #     "ENGINE": env("SQLSERVER_ENGINE"),
    #     "HOST": env("SQLSERVER_SERVER"),
    #     "NAME": env("SQLSERVER_NAME"),
    #     "USER": env("SQLSERVER_USER"),
    #     "PASSWORD": env("SQLSERVER_PASSWORD"),
    #     "PORT": env("SQLSERVER_PORT"),
    #     "OPTIONS": {
    #         "driver": "ODBC Driver 18 for SQL Server",
    #     },
    # },
    # SQLite configuración
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
DB_IS_AVAIL = all(
    [
        DB_ENGINE,
        DB_HOST,
        DB_NAME,
        DB_USER,
        DB_PASSWORD,
        DB_PORT,
    ]
)

if DB_IS_AVAIL:
    DATABASES = {
        # SQL Server
        "default": {
            "ENGINE": DB_ENGINE,
            "HOST": DB_HOST,
            "NAME": DB_NAME,
            "USER": DB_USER,
            "PASSWORD": DB_PASSWORD,
            "PORT": DB_PORT,
            "OPTIONS": {
                "driver": "ODBC Driver 18 for SQL Server",
            },
        },
    }


DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# -- Redis
# https://github.com/redis/redis-om-python
# https://docs.djangoproject.com/en/4.0/topics/cache/#redis

# REDIS_URL = env("REDIS_URL")

REDIS_HOST = os.environ.get("REDIS_HOST")

REDIS_PORT = os.environ.get("REDIS_PORT")

REDIS_DB = os.environ.get("REDIS_DB")

REDIS_URL = "redis://redis-cip:6379"
parsed_url = urlparse(REDIS_URL)

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [("redis-cip", 6379)],
        },
    },
}


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


# -- Lenguajes, internationalización y localización
# https://docs.djangoproject.com/en/4.0/topics/i18n/

LANGUAGE_CODE = "en-us"  # O el código de idioma correspondiente


LANGUAGES = [
    ("en", _("English")),
    ("es", _("Spanish")),
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

USE_TZ = (
    False  # False, si presenta problemas el driver de conección a SQL Server. Más info:
)
# https://docs.microsoft.com/en-us/samples/azure-samples/azure-sql-db-django/azure-sql-db-django/


# Autenticaciones
# --------------------------------------------------------
# https://docs.djangoproject.com/en/4.0/ref/settings/#auth

SITE_ID = 1

AUTH_USER_MODEL = "authentication.User"

LOGIN_URL = "login"

LOGIN_REDIRECT_URL = "main"

LOGOUT_REDIRECT_URL = "index"


# Validación de contraseñas
# https://docs.djangoproject.com/en/4.1/ref/settings/#auth-password-validators

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
    # Object-Permissions Level con django-guardian
    "guardian.backends.ObjectPermissionBackend",
)


# -- Sesiones
# https://docs.djangoproject.com/en/4.0/ref/settings/#sessions

SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# Archivos Static (CSS, JavaScript, Images)
# ---------------------------------------------------------
# https://docs.djangoproject.com/en/4.0/howto/static-files/
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

# Configuración del servicio de email (Gmail)
EMAIL_BACKEND = env(
    "EMAIL_BACKEND", default="django.core.mail.backends.smtp.EmailBackend"
)
EMAIL_HOST = env("EMAIL_HOST", default="smtp.gmail.com")
EMAIL_HOST_USER = env("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD")
EMAIL_PORT = env.int("EMAIL_PORT", default=25)
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=True)

# Configuracion para la paginacion
DEFAULT_PAGINATION = 10
