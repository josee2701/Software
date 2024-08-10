""" Creación de un patrón de URL para las vistas de la creación de empresas.

Para una referencia completa sobre django.urls, consulte
https://docs.djangoproject.com/en/4.0/ref/urls/
"""

from django.urls import path

from . import views
from .views import (
    ClienteListAPIView,
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
    path("moduleList/", views.ModuleView.as_view(), name="list_create_module"),
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
    path("api/clientes/", ClienteListAPIView.as_view(), name="api-clientes"),
]
