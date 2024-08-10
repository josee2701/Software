"""
Serializador de prueba.
"""

from rest_framework import serializers

from apps.authentication.models import User


class AuthenticationSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("username", "is_superuser")
