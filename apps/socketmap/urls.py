from django.urls import path

from . import views

app_name = "socketmap"

urlpatterns = [
    path("maps/<int:company_id>/", views.getmapscompany, name="maps"),
    path(
        "getlastavl/<int:user_id>/", views.get_last_avl_as_json, name="getlastavlasjson"
    ),
    path("getalarmsuser/<int:user_id>/", views.get_alarms_user, name="getalarmsuser"),
    path("vehicle-history/", views.vehicle_history, name="vehicle_history"),
    path("device-commands/", views.get_device_commands, name="device-commands"),
    path("insert-command/", views.insert_sending_command, name="insert-command"),
    path(
        "update-insert-dashboard/",
        views.update_or_insert_company_dashboard,
        name="update-insert-dashboard",
    ),
    path(
        "get-company-dashboard/",
        views.get_company_dashboard,
        name="get-company-dashboard",
    ),
    path("update-alarm/", views.update_events_alarm, name="update-alarm"),
    path(
        "getcompaniesuser/<int:user_id>/",
        views.get_companies_user,
        name="getcompaniesuser",
    ),
    path("insert-geozone/", views.insert_geozone, name="insert-geozone"),
    path(
        "get-geozone-company/<int:company_id>/",
        views.get_geozone_company,
        name="get-geozone-company",
    ),
    path(
        "getvehiclemonitoring/<int:user_id>/",
        views.get_vehicle_monitoring,
        name="get-vehicle-monitoring",
    ),
]
