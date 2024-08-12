# apps/powerbi/urls.py

from django.urls import path

from .views import GroupsView, ReportEmbedView, ReportsInGroupView, ReportUserView

urlpatterns = [
    path(
        "report/<str:workspace_id>/<str:report_id>/",
        ReportEmbedView.as_view(),
        name="embedreport",
    ),
    path("reportuser/<str:user_id>/", ReportUserView.as_view(), name="reportuser"),
    path("groups/", GroupsView.as_view(), name="groups"),
    path(
        "groups/<str:group_id>/reports/",
        ReportsInGroupView.as_view(),
        name="reports_in_group",
    ),
]
