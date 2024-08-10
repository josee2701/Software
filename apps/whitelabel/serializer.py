from django.db.models import Q, Sum
from rest_framework import serializers

from .models import Company, Module


class ClienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = "__all__"


class ModuleSerializer(serializers.ModelSerializer):
    group_name = serializers.CharField(source="group.name")

    class Meta:
        model = Module
        fields = ["group_name", "price"]


class CompanySerializer(serializers.ModelSerializer):
    modules = ModuleSerializer(many=True, read_only=True, source="module_set")
    total_price = serializers.SerializerMethodField()
    coin_name = serializers.CharField(source="coin.name")

    class Meta:
        model = Company
        fields = ["id", "company_name", "coin_name", "modules", "total_price"]

    def get_total_price(self, obj):
        total_price = (
            obj.module_set.aggregate(total_price=Sum("price"))["total_price"] or 0
        )
        return total_price
