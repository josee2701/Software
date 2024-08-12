""" Creación de un patrón de URL para las vistas de la creación de empresas.

Para una referencia completa sobre django.urls, consulte
https://docs.djangoproject.com/en/4.0/ref/urls/
"""

from django.urls import path

from apps.whitelabel.apis import (
    SearchCompany,
    SearchModule,
    SearchTicketsView,
    SearchTicketsViewOpen,
    list_proces_by_company,
    ExportDataCompany,
    ExportDataTicketsOpen,
    ExportDataTicketsHistoric,
    ExportDataModule,
)

from . import views
from .views import (
    ClosedTicketsView,
    CommentTicketView,
    CreateTicketView,
    DeleteProcessView,
    ListProcessAddView,
    ListTicketTemplate,
    UpdateProcessView,
    ViewTicketView,
)

# Creación de un patrón de URL para las vistas de creación de la empresa.
app_name = "companies"
urlpatterns = [
    # Creación de un patrón de URL para la vista Empresas.
    path("companies/", views.CompaniesView.as_view(), name="companies"),
    # Creación de un patrón de URL para la vista CreateCompanyView.
    path(
        "createDistributionCompany/",
        views.CreateDistributionCompanyView.as_view(),
        name="createDistributionCompany",
    ),
    path(
        "createCustomerAzCompany/",
        views.CreateCustomerAzCompanyView.as_view(),
        name="createCustomerAzCompany",
    ),
    path(
        "createCustomerCompany/",
        views.CreateCustomerCompanyView.as_view(),
        name="createCustomerCompany",
    ),
    path(
        "KeyMapView/<int:pk>/",
        views.KeyMapView.as_view(),
        name="KeyMapView",
    ),
    # Este es un patrón de URL para la vista UpdateCompanyView.
    path(
        "updateDistributionCompany/<int:pk>/",
        views.UpdateDistributionCompanyView.as_view(),
        name="updateDistributionCompany",
    ),
    path(
        "updateCustomerCompany/<int:pk>/",
        views.UpdateCustomerCompanyView.as_view(),
        name="UpdateCustomerCompanyView",
    ),
    path(
        "updateCompanyLogo/<int:pk>/",
        views.UpdateCompanyLogoView.as_view(),
        name="updateCompanyLogo",
    ),
    # Este es un patrón de URL para la vista DeleteCompanyView.
    path(
        "deleteCompany/<int:pk>/",
        views.DeleteCompanyView.as_view(),
        name="deleteCompany",
    ),
    path("process/", ListProcessAddView.as_view(), name="process"),
    path("updateProcess/<int:pk>/", UpdateProcessView.as_view(), name="updateProcess"),
    path("deleteProcess/<int:pk>/", DeleteProcessView.as_view(), name="deleteProcess"),
    path("theme/<int:pk>/", views.ThemeView.as_view(), name="theme"),
    path("module/", views.ModuleTemplateView.as_view(), name="module"),
    path(
        "updateModule/<int:pk>/",
        views.UpdateModuleView.as_view(),
        name="updateModule",
    ),
    path("tickets/", ListTicketTemplate.as_view(), name="main_ticket"),
    path("tickets/create/", CreateTicketView.as_view(), name="ticket_create"),
    path(
        "tickets/comment/<int:pk>/", CommentTicketView.as_view(), name="comment_ticket"
    ),
    path("tickets/view/<int:pk>/", ViewTicketView.as_view(), name="view_ticket"),
    path("tickets/closed/", ClosedTicketsView.as_view(), name="closed_tickets"),
    # Se realiza API para acceder a company
    path("process/<int:company_id>/", list_proces_by_company, name="process"),
    # API para traer info de tickets historicos + search
    path(
        "tickets/tickets-company-user",
        SearchTicketsView.as_view(),
        name="tickets_company_user",
    ),
    # API para traer info de tickets abiertos + search
    path("tickets/tickets-user", SearchTicketsViewOpen.as_view(), name="tickets_user"),
    path("company/company-user", SearchCompany.as_view(), name="company_user"),
    path("module/module-user", SearchModule.as_view(), name="module_user"),
    path("company/export-company", ExportDataCompany.as_view(), name="export_company"),
    path("tickets/export-tickets-open", ExportDataTicketsOpen.as_view(), name="export_tickets_open"),
    path("tickets/export-tickets-historic", ExportDataTicketsHistoric.as_view(), name="export_tickets_historic"),
    path("module/module-export", ExportDataModule.as_view(), name="module_export"),
]
