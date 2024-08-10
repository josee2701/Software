"""
Administrador de Usuarios

Este módulo extiende (registra) los modelos y formularios de usuario (User) personalizados en el
UserAdmin existente.

Para más detalles sobre la extensión de modelos de Usuario, consulte:
https://docs.djangoproject.com/en/4.0/topics/auth/customizing/#extending-the-existing-user-model
"""

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import GroupAdmin, UserAdmin
from django.contrib.auth.forms import AdminPasswordChangeForm
from django.contrib.auth.models import Group
from django.utils.translation import gettext_lazy as _
from guardian.admin import GuardedModelAdmin
from guardian.shortcuts import get_objects_for_user

from .forms import UserAdminChangeForm_, UserAdminCreationForm_

User = get_user_model()


@admin.register(User)
class UserAdmin(UserAdmin, GuardedModelAdmin):
    """Registra el modelo de usuario con sus formularios de creación y edición."""

    model = User
    list_display = [
        "username",
        "first_name",
        "last_name",
        "email",
        "get_groups",
        "get_company",
        "is_active",
        "visible",
    ]
    ordering = ("first_name",)
    filter_horizontal = (
        "groups",
        "user_permissions",
        "companies_to_monitor",
        "vehicles_to_monitor",
    )
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (_("Personal info"), {"fields": (("first_name", "last_name"), "email")}),
        (
            _("Permissions"),
            {
                "fields": (
                    "visible",
                    "is_active",
                    ("is_staff", "is_superuser"),
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        (
            _("Functionalities"),
            {
                "fields": (
                    ("company"),
                    "companies_to_monitor",
                    "vehicles_to_monitor",
                ),
            },
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide", "extrapretty"),
                "fields": (
                    ("username", "email"),
                    ("first_name", "last_name"),
                    "company",
                    "password1",
                    "password2",
                ),
            },
        ),
    )
    form = UserAdminChangeForm_
    add_form = UserAdminCreationForm_
    change_password_form = AdminPasswordChangeForm

    @admin.display(description=_("groups"))
    def get_groups(self, obj):
        """Muestra los grupos (roles) que tiene asignado el usuario."""
        return " | ".join([str(g) for g in obj.groups.all()])

    @admin.display(description=_("company"))
    def get_company(self, obj):
        """Muestra la empresa a la que pertenece el usuario."""
        return obj.company

    def has_module_permission(self, request):
        """Verifica si el usuario tiene permisos a nivel de modelo."""
        if super().has_module_permission(request):
            return True
        return self.get_model_objects(request).exists()

    def get_queryset(self, request):
        """Devuelve los registros por modelo que tenga asignados el usuario."""
        if request.user.is_superuser:
            return super().get_queryset(request)
        return self.get_model_objects(request)

    def get_model_objects(self, request, action=None, klass=None):
        """Devuelte los permisos a nivel de modelo que tenga asignados el usuario."""
        opts, user = self.opts, request.user
        actions, klass = [action] if action else [], klass if klass else opts.model
        model_name = klass._meta.model_name
        perms = [f"{perm}_{model_name}" for perm in actions]

        return get_objects_for_user(user=user, perms=perms, klass=klass, any_perm=True)

    def has_permission(self, request, obj, action):
        """Verifica los permisos a nivel de objeto que tenga asignados el usuario."""
        opts = self.opts
        codename, app_label = f"{action}_{opts.model_name}", opts.app_label
        if obj:
            return request.user.has_perm(f"{app_label}.{codename}", obj)
        return self.get_model_objects(request).exists()

    def has_view_permission(self, request, obj=None):
        """Verifica los permisos de lectura que tenga el usuario."""
        return self.has_permission(request, obj, "view")

    def has_change_permission(self, request, obj=None):
        """Verifica los permisos de modificación que tenga el usuario."""
        return self.has_permission(request, obj, "change")

    def has_delete_permission(self, request, obj=None):
        """Verifica los permisos de eliminación que tenga el usuario."""
        return self.has_permission(request, obj, "delete")

    def get_form(self, request, obj=None, **kwargs):
        """Personaliza los campos del formulario a los que tiene acceso el usuario."""
        form = super().get_form(request, obj, **kwargs)
        is_superuser = request.user.is_superuser
        fields_to_disable = set()

        # Bloquea los siguientes campos para todo usuario no superusuario:
        if not is_superuser:
            fields_to_disable |= {"is_superuser", "is_active", "is_staff"}

        # Evita que los usuarios modifiquen su información excepto el `username`, `email`
        # `first_name` y `last_name`:
        if not is_superuser and obj is not None and obj == request.user:
            fields_to_disable |= {field for field in form.base_fields}
            for field in ["username", "email", "first_name", "last_name"]:
                fields_to_disable.discard(field)

        # Desabilita los campos en el formulario:
        for field in fields_to_disable:
            if field in form.base_fields:
                form.base_fields[field].disabled = True

        return form


# Anula el registro del modelo de grupo del sitio de administración.
admin.site.unregister(Group)


@admin.register(Group)
class GroupAdmin(GroupAdmin):
    """Registra de nuevo el modelo original de grupos (Group) en el sitio de Admin de Django,
    añadiendo una representación personalizada de los permisos asignados a cada grupo.
    """

    list_display = [
        "name",
        "list_permissions",
    ]  # Asegúrate de usar 'name', el campo estándar de Group.

    @admin.display(description=_("Permisos"))
    def list_permissions(self, obj):
        """Devuelve una cadena de texto que representa todos los permisos asignados a un grupo.

        :param obj: Instancia del modelo Group para el cual se enumeran los permisos.
        :return: Cadena de texto que representa los permisos asignados al grupo.
        """
        # Ajusta la consulta para mejorar la eficiencia y exactitud
        permissions = obj.permissions.prefetch_related("content_type").all()

        # Usa un diccionario para agrupar permisos por modelo
        permissions_by_model = {}
        for perm in permissions:
            action = perm.codename.split("_")[
                0
            ]  # Divide el codename para obtener la acción
            model = perm.content_type.model  # Obtiene el modelo del permiso

            # Traduce la acción a un alias más simple
            action_alias = {"add": "C", "change": "U", "delete": "D", "view": "R"}.get(
                action, action[0].upper()
            )

            if model in permissions_by_model:
                permissions_by_model[model].add(action_alias)
            else:
                permissions_by_model[model] = {action_alias}

        # Construye la cadena final de permisos
        permissions_str = " | ".join(
            f"{model.capitalize()}: {''.join(sorted(actions))}"
            for model, actions in permissions_by_model.items()
        )

        return permissions_str


# # Opcional: Crear una clase admin personalizada para Permission si necesitas personalización adicional
# class PermissionAdmin(admin.ModelAdmin):
#     search_fields = ['name', 'codename']  # Permitir búsqueda por nombre y codename
#     list_filter = ['content_type']  # Filtrar por tipo de contenido
#     list_display = ['name', 'codename', 'content_type']  # Mostrar estos campos en la lista

# # Registrar el modelo Permission con el admin de Django
# admin.site.register(Permission, PermissionAdmin)

# class GroupAdmin(TranslationAdmin):
#     pass

# admin.site.unregister(Group)
# admin.site.register(Group, GroupAdmin)
