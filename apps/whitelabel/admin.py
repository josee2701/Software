"""
Módulo de registro de los modelos de marca blanca en el panel de administración.

Este módulo extiende (registra) los modelos y sus formularios para ser gestionados desde el sitio
de administración.

Para obtener todos los detalles sobre la ampliación de un modelo en Django, consulte
https://docs.djangoproject.com/en/4.0/topics/auth/customizing/#extending-the-existing-user-model
"""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import Company, MapType, Module, Process, Theme, Ticket

models = [Theme, MapType, Ticket, Process]


class CompanyAdmin(admin.ModelAdmin):
    list_display = ("nit", "company_name", "provider", "actived", "visible")
    search_fields = ("company_name",)
    list_filter = ("provider", "actived", "visible")


class ModuleAdmin(admin.ModelAdmin):
    list_display = ("company", "group")
    search_fields = ("company",)
    list_filter = ("group",)


admin.site.register(Company, CompanyAdmin)
admin.site.register(Module, ModuleAdmin)
admin.site.register(models)
