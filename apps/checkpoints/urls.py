from django.urls import include, path

from . import views
from .api import (
    events_by_company,
    events_person_by_company,
    export_report,
    vehicles_by_company,
)

app_name = "checkpoints"

urlpatterns = [
    # Conductores y su manejo
    path(
        "drivers/",
        include(
            [
                path("", views.ListDriverTemplate.as_view(), name="list_drivers"),
                path(
                    "list_drivers_company",
                    views.ListDriversView.as_view(),
                    name="list_drivers_company",
                ),
                path("add", views.AddDriverView.as_view(), name="add_driver"),
                path(
                    "update/<int:pk>",
                    views.UpdateDriverView.as_view(),
                    name="update_driver",
                ),
                path(
                    "delete/<int:pk>",
                    views.DeleteDriverView.as_view(),
                    name="delete_driver",
                ),
                path(
                    "assign_driver/<int:pk>",
                    views.AddAssignDriverView.as_view(),
                    name="assign_driver",
                ),
                path(
                    "update_assign/<int:pk>",
                    views.UpdateAssignDriverView.as_view(),
                    name="update_assign",
                ),
                path("assign/<int:pk>", views.BottonView.as_view(), name="button_view"),
                path(
                    "update_assing_vehicle/<int:pk>",
                    views.UpdateVehicleAssignView.as_view(),
                    name="update_vehicle_assign",
                ),
            ]
        ),
    ),
    # Calificación de conductores
    path(
        "driver/",
        include(
            [
                path(
                    "score_configuration/<int:pk>",
                    views.ScoreConfigurationView.as_view(),
                    name="score_configuration",
                ),
                path(
                    "list_score_configuration",
                    views.ListScoreCompanyTemplate.as_view(),
                    name="list_score_configuration",
                ),
                path(
                    "list_score_configuration_companies",
                    views.ListScoreCompaniesView.as_view(),
                    name="list_score_configuration_companies",
                ),
            ]
        ),
    ),
    # Reportes
    path(
        "reports/",
        include(
            [
                path("driver", views.ReporDriverView.as_view(), name="report_driver"),
                path("today/", views.ReportTodayView.as_view(), name="report_today"),
                # traer vehicle por compañia
                path(
                    "vehicles-by-company/<int:company_id>/",
                    vehicles_by_company,
                    name="vehicles_by_company",
                ),
                # traer eventos por compañia
                path(
                    "events-by-company/<int:company_id>/",
                    events_by_company,
                    name="events_by_company",
                ),
                path(
                    "events_person-by-company/<int:company_id>/",
                    events_person_by_company,
                    name="events_by_company",
                ),
                path("report-today/", views.ReportToday.as_view(), name="report"),
                path("avldat", export_report, name="avldat"),
                path(
                    "api/report-data/",
                    views.ReportDataAPIView.as_view(),
                    name="report-data-api",
                ),
            ]
        ),
    ),
]
