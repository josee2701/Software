from django.contrib import admin

from .models import (
    CompanyScoreSetup,
    Driver,
    DriverAnalytic,
    FatigueControl,
    ItemScore,
    ItemScoreSetup,
)

models = [ItemScore, CompanyScoreSetup, FatigueControl]


class DriverAdmin(admin.ModelAdmin):
    list_display = ("first_name", "last_name", "company", "is_active")
    search_fields = ("last_name", "first_name")
    list_filter = ("company", "is_active")


class DriverAnalyticAdmin(admin.ModelAdmin):
    list_display = ("driver", "vehicle")
    search_fields = ("driver",)
    list_filter = ("driver",)


class ItemScoreSetupAdmin(admin.ModelAdmin):
    list_display = ("item", "company_score")
    search_fields = ("item",)
    list_filter = ("item",)


admin.site.register(Driver, DriverAdmin)
admin.site.register(DriverAnalytic, DriverAnalyticAdmin)
admin.site.register(ItemScoreSetup, ItemScoreSetupAdmin)
admin.site.register(models)
