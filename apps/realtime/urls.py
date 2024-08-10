from django.urls import include, path

from . import views
from .apis import (
    AvailableDevicesAPI,
    AvailableSimCardsAPI,
    get_commands,
    get_company_id_items_report,
    get_data_plans,
)

app_name = "realtime"

urlpatterns = [
    # Configuración y reportes
    path(
        "configuration-report/",
        views.ConfigurationReportView.as_view(),
        name="add_configuration_report",
    ),
    # Otras URLs
    path("get-instance-data/", get_company_id_items_report, name="get_instance_data"),
    path(
        "configuration-report/update/<int:company_id>/",
        views.UpdateConfigurationReportView.as_view(),
        name="update_configuration_report",
    ),
    # Dispositivos
    path(
        "devices/",
        include(
            [
                path("", views.ListDeviceTemplate.as_view(), name="devices"),
                path("add_device", views.AddDeviceView.as_view(), name="add_device"),
                path(
                    "update_device/<str:pk>",
                    views.UpdateDeviceView.as_view(),
                    name="update_device",
                ),
                path(
                    "delete/<str:pk>",
                    views.DeleteDeviceView.as_view(),
                    name="delete_device",
                ),
                path(
                    "api/available-simcards/<int:company_id>/",
                    AvailableSimCardsAPI.as_view(),
                    name="available-simcards",
                ),
                path(
                    "api/available-simcards/<int:company_id>/<str:imei>/",
                    AvailableSimCardsAPI.as_view(),
                    name="available-simcards-edit",
                ),
            ]
        ),
    ),
    # Vehículos
    path(
        "vehicles/",
        include(
            [
                path("", views.ListVehicleTemplate.as_view(), name="vehicles"),
                # path(
                #     "list_vehicles_created",
                #     views.ListVehiclesView.as_view(),
                #     name="list_vehicles_created",
                # ),
                path("add_vehicle", views.AddVehicleView.as_view(), name="add_vehicle"),
                path(
                    "update_vehicle/<int:pk>",
                    views.UpdateVehicleView.as_view(),
                    name="update_vehicle",
                ),
                path(
                    "delete/<int:pk>",
                    views.DeleteVehicleView.as_view(),
                    name="delete_vehicle",
                ),
                path(
                    "api/available-devices/<int:company_id>/",
                    AvailableDevicesAPI.as_view(),
                    name="available-devices",
                ),
                path(
                    "api/available-devices/<int:company_id>/<int:vehicle_id>/",
                    AvailableDevicesAPI.as_view(),
                    name="available-devices-edit",
                ),
            ]
        ),
    ),
    # Grupos de vehículos
    path(
        "group_vehicles/",
        include(
            [
                path(
                    "", views.ListVehicleGroupTemplate.as_view(), name="group_vehicles"
                ),
                path(
                    "list_group_vehicles_created",
                    views.ListVehiclesGroupView.as_view(),
                    name="list_group_vehicles_created",
                ),
                path(
                    "add_group",
                    views.AddVehicleGroupView.as_view(),
                    name="add_group_vehicle",
                ),
                path(
                    "update_group/<int:pk>",
                    views.UpdateVehicleGroupView.as_view(),
                    name="update_group_vehicle",
                ),
                path(
                    "delete_group/<int:pk>",
                    views.DeleteVehicleGroupView.as_view(),
                    name="delete_group_vehicle",
                ),
            ]
        ),
    ),
    # Simcards
    path(
        "simcards/",
        include(
            [
                path("", views.ListSimcardTemplate.as_view(), name="simcards"),
                path("add", views.AddSimcardView.as_view(), name="add_simcard"),
                path(
                    "update/<int:pk>",
                    views.UpdateSimcardView.as_view(),
                    name="update_simcard",
                ),
                path(
                    "delete/<int:pk>",
                    views.DeleteSimcardView.as_view(),
                    name="delete_simcard",
                ),
                path(
                    "api/data-plans/<int:company_id>/",
                    get_data_plans,
                    name="get_data_plans",
                ),
            ]
        ),
    ),
    # DataPlan
    path(
        "dataplan/",
        include(
            [
                path("", views.ListDataPlanTemplate.as_view(), name="dataplan"),
                path("add", views.AddDataPlanView.as_view(), name="add_data_plan"),
                path(
                    "update_plan/<int:pk>",
                    views.UpdateDataPlanView.as_view(),
                    name="update_data_plan",
                ),
                path(
                    "delete/<int:pk>",
                    views.DeleteDataPlanView.as_view(),
                    name="delete_data_plan",
                ),
            ]
        ),
    ),
    # Comandos
    path(
        "commands/",
        include(
            [
                path("", views.ListSendingCommandsTemplate.as_view(), name="commands"),
                path(
                    "add", views.AddSendingCommandsView.as_view(), name="add_Commands"
                ),
                path(
                    "response",
                    views.ListResponseCommandsTemplate.as_view(),
                    name="response_commands",
                ),
                path("get-commands/<str:imei>/", get_commands, name="get_commands"),
            ]
        ),
    ),
    # Geozonas
    path(
        "geozones/",
        include(
            [
                path("", views.ListGeozonesTemplate.as_view(), name="geozones"),
                path(
                    "list_geozone",
                    views.ListGeozonesView.as_view(),
                    name="list_geozone",
                ),
                path(
                    "add_geozones", views.AddGeozonesView.as_view(), name="add_geozones"
                ),
                path(
                    "update_geozones/<int:pk>",
                    views.UpdateGeozonesView.as_view(),
                    name="update_geozones",
                ),
                path(
                    "delete/<int:pk>",
                    views.DeleteGeozonesView.as_view(),
                    name="delete_geozones",
                ),
            ]
        ),
    ),
]
