from rest_framework import serializers

from .models import AVLData, Geozones, Vehicle


class VehicleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehicle
        fields = "__all__"


class GeozonesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Geozones
        fields = "__all__"


class AVLDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = AVLData
        fields = "__all__"
