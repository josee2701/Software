"""
Creación de un patrón de URLs para las vistas de autenticación.

Este modulo reescribe las vistas predeterminadas para la autenticación de Django definidas por
`django.contrib.auth`, conservando sus mismos patrones URLs.

Para una referencia completa sobre la autenticación de usuarios Django, consulte
https://docs.djangoproject.com/en/4.1/topics/auth/default/
"""

from django.urls import include, path

from .apis import SearchUser, list_proces_by_company, ExportDataUsers
from .views import (AddUserView, ClearEmailView, DeleteUser, IndexView_,
                    LoginView_, Main_, PasswordChangeDoneView_,
                    PasswordChangeView_, PasswordResetCompleteView_,
                    PasswordResetConfirmView_, PasswordResetDoneView_,
                    PasswordResetView_, PasswordUserView, PermissionUserView,
                    ProfileUserView, UpdatePermissionUser, UpdateUserView,
                    UserLisTemplate)

urlpatterns = [
    # Vista de inicio o bienvenida.
    path("clear_email/", ClearEmailView.as_view(), name="clear_email"),
    path("", IndexView_.as_view(), name="index"),
    # Vista principal a la cual se redirigen los usuarios autenticados.
    # path("main/", RedirectView.as_view(url=reverse_lazy("admin:index")), name="main"),
    path("main/", Main_.as_view(), name="main"),
    # Vista de autenticación. Reescribe la vista predeterminada de Django.
    path("login/", LoginView_.as_view(), name="login"),
    # Vista de cambio de contraseña. Reescribe la vista predeterminada...
    path("password_change/", PasswordChangeView_.as_view(), name="password_change"),
    # Vista de confirmación de cambio de contraseña. Reescribe la vista predeterminada...
    path(
        "password_change/done/",
        PasswordChangeDoneView_.as_view(),
        name="password_change_done",
    ),
    # Vista de solicitud de restauración de contraseñas. Reescribe la vista predeterminada...
    path("password_reset/", PasswordResetView_.as_view(), name="password_reset"),
    # Vista de confirmación de la solicitud de restauración de contraseñas. Reescribe...
    path(
        "password_reset/done/",
        PasswordResetDoneView_.as_view(),
        name="password_reset_done",
    ),
    # Vista de restauración de contraseñas. Reescribe la vista predeterminada...
    path(
        "reset/<uidb64>/<token>/",
        PasswordResetConfirmView_.as_view(),
        name="password_reset_confirm",
    ),
    # Vista de confirmación de restauración de contraseñas. Reescribe la vista predeterminada...
    path(
        "reset/done/",
        PasswordResetCompleteView_.as_view(),
        name="password_reset_complete",
    ),
    # Vista de confirmación para cambiar el idioma...
    path("i18n/", include("django.conf.urls.i18n")),
    # Vista del modulo de usuer...
    path(
        "users/",
        include(
            [
                path("", UserLisTemplate.as_view(), name="users"),
                path("AddUsers", AddUserView.as_view(), name="AddUsers"),
                path(
                    "UpdateUsers/<int:pk>/",
                    UpdateUserView.as_view(),
                    name="UpdateUsers",
                ),
                path(
                    "PermissionUsers/<int:pk>/",
                    PermissionUserView.as_view(),
                    name="PermissionUsers",
                ),
                path(
                    "UpdatePermissionUsers/<int:pk>/",
                    UpdatePermissionUser.as_view(),
                    name="UpdatePermissionUsers",
                ),
                path(
                    "DeleteUsers/<int:pk>/",
                    DeleteUser.as_view(),
                    name="DeleteUsers",
                ),
                path(
                    "process/<int:company_id>/<int:user_id>/", list_proces_by_company, name="process"
                ),
                # API para traer info de usuarios + search
                path("users-user", SearchUser.as_view(), name="users_user"),
                path("export-user", ExportDataUsers.as_view(), name="export_user"),

            ]
        ),
    ),
    path("profile/<int:pk>/", ProfileUserView.as_view(), name="Profile"),
    path("password/", PasswordUserView.as_view(), name="Password"),
    path("profile_user/<int:pk>/", ProfileUserView.as_view(), name="profile_user"),
]
