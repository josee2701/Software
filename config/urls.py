"""
Configuración de URLs.

La lista `urlpatterns` contiene las direcciones URL de las vistas. Para más detalles, consulte:
https://docs.djangoproject.com/en/4.1/topics/http/urls/
"""

from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import include, path

api = i18n_patterns(
    # Módulo de la API, endpoint principal.
    path("api/", include("apps.api.urls")),
)

apps = i18n_patterns(
    # Módulo personalizado de autenticación de usuarios.
    path("", include("apps.authentication.urls"), name="main"),
    # Métodos de autenticación de Django. El módulo `authentication` los reescribe.
    path("", include("django.contrib.auth.urls")),
    # Módulo de puntos de control (checkpoints).
    path("checkpoints/", include("apps.checkpoints.urls")),
    # Módulo de eventos
    path("events/", include("apps.events.urls")),
    # Módulo de reporte en tiempo real (realtime).
    path("realtime/", include("apps.realtime.urls")),
    # Módulo para la administración, personalización y creación de empresas (whitelabel).
    path("whitelabel/", include("apps.whitelabel.urls")),
    # Modulo de socketmap
    path("socketmap/", include("apps.socketmap.urls")),
)

django = i18n_patterns(
    # Sitio de administración de Django.
    path("admin/", admin.site.urls),
    # Librería de control de traducciones
    path("rosetta/", include("rosetta.urls")),
)


media = static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

static_files = static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)


urlpatterns = api + apps + django + media + static_files
