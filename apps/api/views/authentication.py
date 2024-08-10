"""
Vistas de autenticación en API (Prueba)

Referencia completa sobre las vistas, consulte
https://docs.djangoproject.com/en/4.0/ref/class-based-views/base/
"""

from rest_framework import generics

from apps.api.serializers.authentication import AuthenticationSerializer
from apps.authentication.models import User


class AuthenticationApiView(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = AuthenticationSerializer
