from django.contrib import admin

from .models import (
    AVLData,
    Command_response,
    Commands,
    DataPlan,
    Device,
    FamilyModelUEC,
    Geozones,
    Io_items_report,
    Last_Avl,
    ModelUEC,
    Sending_Commands,
    SimCard,
    Vehicle,
    VehicleGroup,
)

models = [
    AVLData,
    ModelUEC,
    FamilyModelUEC,
    Sending_Commands,
    Commands,
    Geozones,
    Command_response,
    Last_Avl,
    Io_items_report,
]


class DataplanAdmin(admin.ModelAdmin):
    list_display = ("name", "company", "operator", "visible")
    search_fields = ("name",)
    list_filter = (
        "company",
        "visible",
        "operator",
    )


class SimCardAdmin(admin.ModelAdmin):
    list_display = ("serial_number", "company", "is_active", "iz_az_simcard", "visible")
    search_fields = ("serial_number",)
    list_filter = (
        "company",
        "visible",
        "is_active",
        "iz_az_simcard",
    )


class DeviceAdmin(admin.ModelAdmin):
    list_display = ("imei", "company", "is_active", "visible")
    search_fields = ("imei",)
    list_filter = (
        "company",
        "visible",
        "is_active",
    )


class VehicleAdmin(admin.ModelAdmin):
    list_display = ("license", "company", "visible")
    search_fields = ("license",)
    list_filter = (
        "company",
        "visible",
    )


class VehicleGroupAdmin(admin.ModelAdmin):
    list_display = ("name", "get_vehicle_names", "visible")
    search_fields = ("name",)
    list_filter = ("visible",)

    def get_vehicle_names(self, obj):
        return ", ".join([vehicle.license for vehicle in obj.vehicles.all()])

    get_vehicle_names.short_description = "Vehicles"


admin.site.register(DataPlan, DataplanAdmin)
admin.site.register(SimCard, SimCardAdmin)
admin.site.register(Device, DeviceAdmin)
admin.site.register(Vehicle, VehicleAdmin)
admin.site.register(VehicleGroup, VehicleGroupAdmin)
admin.site.register(models)
