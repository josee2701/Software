from django.urls import include, path

from apps.checkpoints.sql import fetch_all_confidatasem

from . import views
from .api import (ExportDataDriver, ExportDataScoreDriver, SearchDataSem,
                  SearchDrivers, SearchScores, events_by_company,
                  events_person_by_company, export_report, user_by_company,
                  vehicles_by_company)

app_name = "checkpoints"

urlpatterns = [
    # Conductores y su manejo
    path(
        "drivers/",
        include(
            [
                path("", views.ListDriverTemplate.as_view(), name="list_drivers"),
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
                path("drivers-user", SearchDrivers.as_view(), name="user_driver"),
                path("export-drivers", ExportDataDriver.as_view(), name="export_drivers"),
            ]
        ),
    ),
    # Calificación de conductores
    path(
        "driver/",
        include(
            [
                path(
                    "list_score_configuration/",
                    views.ListScoreCompanyTemplate.as_view(),
                    name="list_score_configuration",
                ),
                path(
                    "score_configuration/<int:pk>",
                    views.ScoreConfigurationView.as_view(),
                    name="score_configuration",
                ),
                path("scores-user", SearchScores.as_view(), name="user_scores"),
                path("export-scores", ExportDataScoreDriver.as_view(), name="export_scores"),
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
                path("avldat", export_report, name="avldat"),
                
            ]
        ),
    ),
    path(
        "powerbi/",
        include(
            [
                path(
                    "DataSeM",
                    views.Advanced_AnalyticalView.as_view(),
                    name="DataSeM",
                ),
                path(
                    "Confi_DataSeM",
                    views.DataSemConfigurationList.as_view(),
                    name="Config_DataSeM",
                ),
                path(
                    "DataSeM/Add",
                    views.AddDataSemConfiguration.as_view(),
                    name="AddDataSeM",
                ),
                path(
                    "DataSeM/Update/<int:pk>/",
                    views.UpdateDataSemConfiguration.as_view(),
                    name="UpdateDataSeM",
                ),
                path(
                    "DataSeM/Delete/<int:pk>/",
                    views.DeleteDataSemConfiguration.as_view(),
                    name="DeleteDataSeM",
                ),
                path("search_datasem", SearchDataSem.as_view(), name="search_datasem"),
                path("user_company/<int:company_id>/", user_by_company , name="list_user"),
            ]
        ),
    ),
]
