"""
Asignación de las vistas a los endpoints de la API.

Para una referencia completa sobre django.urls, consulte
https://docs.djangoproject.com/en/4.0/ref/urls/
"""

from django.urls import path

from apps.api.views.authentication import AuthenticationApiView

urlpatterns = [
    path("", AuthenticationApiView.as_view()),  # Endpoint de prueba.
]
