"""
Este módulo define las rutas URL para las vistas relacionadas con eventos y alarmas en la
aplicación Django.
Se incluyen rutas para listar, añadir, actualizar y eliminar eventos predeterminados y eventos
personalizados por usuario.

Para obtener una referencia detallada sobre cómo trabajar con django.urls, puede visitar la
documentación oficial:
https://docs.djangoproject.com/en/4.0/ref/urls/
"""

from django.urls import include, path

from . import views  # Importación de las vistas del mismo módulo

app_name = "events"  # Nombre de la aplicación para el espacio de nombres de URL

urlpatterns = [
    # Rutas para eventos predeterminados
    path(
        "list_events_predefined/",
        views.ListEventsView.as_view(),
        name="list_events_predefined",
    ),
    path("add/", views.AddEventsView.as_view(), name="add_events"),
    path("update/<int:pk>/", views.UpdateEventsView.as_view(), name="update_events"),
    path("delete/<int:pk>/", views.DeleteEventsView.as_view(), name="delete_events"),
    # Rutas para eventos personalizados de usuario
    path(
        "personalized/",
        include(
            [
                path(
                    "", views.ListUserEventsTemplate.as_view(), name="list_user_events"
                ),
                path(
                    "add_user_events/",
                    views.AddUserEventsView.as_view(),
                    name="add_user_events",
                ),
                path(
                    "update_user_events/<int:pk>/",
                    views.UpdateUserEventsViews.as_view(),
                    name="update_user_events",
                ),
                path(
                    "delete_user_events/<int:pk>/",
                    views.DeleteUserEventsView.as_view(),
                    name="delete_user_events",
                ),
            ]
        ),
    ),
]
