"""
Vistas de autentificación.

Este módulo asigna las validaciones de correos y contraseñas en las páginas de inicio, login,
cambio y reestablecimiento de contraseñas. También define las redirecciones de URLs en caso de una
autentificación fallida o ingreso de información incorrecta en los formularios.

El código se construye herendando su funcionalidad a partir de las clases principales que
suministra el componente `django.contrib.auth`.

Referencia completa sobre las vistas y el sistema de autentificación de Django, consulte
https://docs.djangoproject.com/en/4.0/ref/class-based-views/base/
https://docs.djangoproject.com/en/4.0/topics/auth/customizing/
"""
from django.contrib.auth import (authenticate, get_user_model, login,
                                 update_session_auth_hash)
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import (LoginRequiredMixin,
                                        PermissionRequiredMixin)
from django.contrib.auth.models import Group, Permission
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.views import (PasswordChangeDoneView,
                                       PasswordChangeView,
                                       PasswordResetCompleteView,
                                       PasswordResetConfirmView,
                                       PasswordResetDoneView,
                                       PasswordResetView)
from django.db.models import Q
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views import View, generic
from django.views.decorators import cache, csrf
from django.views.decorators.cache import never_cache
from django.views.generic import TemplateView
from django.views.generic.edit import FormView

from apps.realtime.models import Vehicle, VehicleGroup
from apps.whitelabel.models import Company, Module, Process, Theme
from config.pagination import get_paginate_by

from .forms import (IndexForm_, LoginForm_, PasswordChangeForm_,
                    PasswordResetForm_, PermissionForm, SetPasswordForm_,
                    UserChangeForm_, UserCreationForm_, UserProfileForm)
from .sql import fetch_all_user

User = get_user_model()


class ClearEmailView(View):
    """
    Vista para limpiar el correo electrónico de la sesión y redirigir al usuario para que ingrese un nuevo correo.
    """

    def get(self, request, *args, **kwargs):
        if "email" in request.session:
            del request.session["email"]
        request.session.flush()
        return redirect("index")


class IndexView_(FormView):
    """
    Vista de inicio: valida que el único campo del formulario (email) exista en la aplicación.
    """

    template_name = "authentication/index.html"
    form_class = IndexForm_
    success_url = reverse_lazy("login")
    redirect_authenticated_user = True

    @method_decorator(csrf.csrf_protect)
    @method_decorator(cache.never_cache)
    def dispatch(self, request, *args, **kwargs):
        """
        Si el usuario está autentificado, redirígelo a la página principal `main`.

        :param request: El objeto de solicitud actual.
        :return: Se devuelve el método super().dispatch().
        """
        if self.redirect_authenticated_user and self.request.user.is_authenticated:
            return redirect("main")
        if self.request.session.get("email"):
            return redirect(self.success_url)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        """
        Método que se llama cuando el formulario es válido.

        :param form: El formulario que se envió
        :return: Se devuelve super().form_valid(formulario).
        """
        email = form.cleaned_data["email"]
        self.request.session["email"] = email
        return super().form_valid(form)


class LoginView_(FormView):
    """
    Vista que autentifica a un usuario en la aplicación.
    """

    template_name = "authentication/login.html"
    form_class = LoginForm_
    success_url = reverse_lazy("main")
    redirect_authenticated_user = True

    @method_decorator(csrf.csrf_protect)
    @method_decorator(cache.never_cache)
    def dispatch(self, request, *args, **kwargs):
        """
        Si el usuario está autenticado, rediríjalo a la vista principal `main`.
        Si el usuario no está autenticado y no tiene una sesión activa, rediríjalo a la página de inicio `index`.

        :param request: El objeto de solicitud actual
        :return: Se devuelve el método super().dispatch().
        """
        if self.redirect_authenticated_user and request.user.is_authenticated:
            return redirect(self.success_url)

        # Si no hay una sesión activa, redirige al usuario a la vista 'index'
        if not request.session.get("email"):
            return redirect("index")

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """
        Toma los datos del contexto del formulario y agrega el username, el first_name y el correo
        electrónico del usuario a los datos de contexto.
        :return: El contexto actualizado.
        """
        context = super().get_context_data(**kwargs)

        if self.request.session.get("email"):
            user = User.objects.get(email=self.request.session["email"])
            # Obtener el theme de la compañía del usuario
            company_theme = Theme.objects.filter(company_id=user.company_id).first()
            company_user = Company.objects.filter(id=user.company_id).first()
            # Obtener el theme del proveedor de la compañía del usuario
            if user.company.provider_id:
                provider_theme = Theme.objects.filter(
                    company_id=user.company.provider_id
                ).first()
                provider_theme1 = Theme.objects.filter(
                    company_id=user.company.provider_id
                )
                (
                    button_color,
                    lock_screen_image,
                    sidebar_image,
                    sidebar_color,
                    opacity,
                ) = provider_theme1.values_list(
                    "button_color",
                    "lock_screen_image",
                    "sidebar_image",
                    "sidebar_color",
                    "opacity",
                ).first()

                if not company_theme:
                    Theme.objects.create(company_id=user.company_id, button_color=button_color, lock_screen_image=lock_screen_image, sidebar_image=sidebar_image, sidebar_color=sidebar_color, opacity=opacity)
                # Verificar si la compañía existe y si no tiene un logo
                if company_user and not company_user.company_logo and user.company.provider_id:
                    # Buscar la compañía proveedora
                    company_provider = Company.objects.filter(id=user.company.provider_id).first()
                    
                    if company_provider:
                        # Asignar el logo del proveedor
                        company_user.company_logo = company_provider.company_logo
                        # Guardar los cambios en la base de datos
                        company_user.save()

                # Asignar el logo al contexto si es necesario
                context["company_logo"] = company_user.company_logo if company_user else None

            else:
                # Si no hay proveedor, obtener el theme de la misma compañía del usuario
                provider_theme = Theme.objects.filter(
                    company_id=user.company_id
                ).first()

            # Usar el theme del proveedor si está disponible, de lo contrario, usar el de la compañía del usuario
            theme = company_theme if company_theme else provider_theme

            self.request.session["username"] = user.username

            profile_picture = (
                user.profile_picture.url
                if user.profile_picture
                else "/static/Perfil/Perfil.png"
            )
            context.update(
                {
                    "username": user.username,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "email": user.email,
                    "theme": theme.lock_screen_image,
                    "profile_picture": profile_picture,
                    "color_theme": theme.button_color,
                }
            )
        return context

    def form_valid(self, form):
        """
        Si el usuario está autenticado, inicie sesión y rediríjalo a la URL correcta. De lo
        contrario, agregue un error al formulario y vuelva a procesarlo.

        :param form: El formulario que se diligenció.
        :return: El formulario validado.
        """
        username = self.request.session["username"]
        password = form.cleaned_data["password"]
        user = authenticate(username=username, password=password)

        if user is not None:
            login(self.request, user)
            self.request.session.set_expiry(
                0
            )  # Hace que la sesión caduque al cerrar el navegador
            return super().form_valid(form)
        else:
            msg = _("The password is incorrect. Please try again.")
            form.add_error("password", msg)
            return self.form_invalid(form)

    def form_invalid(self, form):
        """
        Si el formulario no es válido, vuelva a presentar el formulario con los errores.

        :param form: El formulario que se envió.
        :return: El formulario que está siendo devuelto.
        """
        return self.render_to_response(self.get_context_data(form=form))


class PasswordChangeView_(LoginRequiredMixin, PasswordChangeView):
    """
    Vista que permite el cambio de contraseña a un usuario autentificado. Cada uno de los métodos
    se ejecuta de acuerdo a la clase madre `PasswordChangeView` original de Django.
    """

    form_class = PasswordChangeForm_
    template_name = "authentication/password_change.html"

    @method_decorator(csrf.csrf_protect)
    @method_decorator(cache.never_cache)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get_form_kwargs(self):
        return super().get_form_kwargs()

    def form_valid(self, form):
        return super().form_valid(form)


class PasswordChangeDoneView_(LoginRequiredMixin, PasswordChangeDoneView):
    """Vista de confirmación de cambio de contraseña."""

    template_name = "authentication/password_change_done.html"

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)


class PasswordResetView_(PasswordResetView):
    """Vista que configura el envío de un correo para la restauración de contraseña."""

    email_template_name = "registration/password_reset_email.html"
    extra_email_context = None
    form_class = PasswordResetForm_
    from_email = None
    html_email_template_name = None
    subject_template_name = "registration/password_reset_subject.txt"
    success_url = reverse_lazy("password_reset_done")
    template_name = "authentication/password_reset_form.html"
    title = _("Password reset")
    token_generator = default_token_generator

    @method_decorator(csrf.csrf_protect)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def form_valid(self, form):
        return super().form_valid(form)


class PasswordResetDoneView_(PasswordResetDoneView):
    """Vista de confirmación del envío de correo para la restauración de contraseñas."""

    template_name = "authentication/password_reset_done.html"


class PasswordResetConfirmView_(PasswordResetConfirmView):
    """Vista que permite al usuario reestablecer una nueva contraseña."""

    form_class = SetPasswordForm_
    post_reset_login = False
    post_reset_login_backend = None
    reset_url_token = "set-password"
    template_name = "authentication/password_reset_confirm.html"
    token_generator = default_token_generator

    @method_decorator(cache.never_cache)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get_user(self, uidb64):
        return super().get_user(uidb64)

    def get_form_kwargs(self):
        return super().get_form_kwargs()

    def form_valid(self, form):
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        return super().get_context_data(**kwargs)


class PasswordResetCompleteView_(PasswordResetCompleteView):
    """Vista que confirma la nueva contraseña reestablecida."""

    template_name = "authentication/password_reset_complete.html"

    def get_context_data(self, **kwargs):
        return super().get_context_data(**kwargs)


class Main_(LoginRequiredMixin, TemplateView):
    login_url = reverse_lazy("index")
    template_name = "authentication/dashboard_test.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class UserLisTemplate(PermissionRequiredMixin, LoginRequiredMixin, generic.ListView):
    """
    Vista como clase que renderiza el template HTML que contiene la lista de vehículos.
    """

    model = User
    template_name = "authentication/users/user_main.html"
    login_url = "login"
    permission_required = "authentication.view_user"

    def get_paginate_by(self, queryset):
        """
        Obtiene el número de elementos a mostrar por página.

        Args:
            queryset (QuerySet): El conjunto de datos de la consulta.

        Returns:
            int: El número de elementos a mostrar por página.
        """
        return get_paginate_by(self.request)

    def get_queryset(self):
        """
        Obtiene el conjunto de datos de los comandos de envío filtrados y ordenados.

        Returns:
            QuerySet: El conjunto de datos de los comandos de envío filtrados y ordenados.
        """
        user = self.request.user
        company= user.company
        return fetch_all_user(company, user.id)

    def get_context_data(self, **kwargs):
        """
        Obtiene el contexto de datos para renderizar la vista.

        Args:
            **kwargs: Argumentos clave adicionales.

        Returns:
            dict: El contexto de datos para renderizar la vista.
        """
        context = super().get_context_data(**kwargs)
        # Simplificación directa para calcular start_number
        page_number = context.get("page_obj").number if context.get("page_obj") else 1
        context["start_number"] = (page_number - 1) * self.get_paginate_by(None)
        return context


class AddUserView(PermissionRequiredMixin, LoginRequiredMixin, generic.CreateView):

    """Vista en la cual se le permite al usuario agregar un nuevo usuario, ademas cuenta con su
    propio formulario para hacer la creacion"""

    model = User
    form_class = UserCreationForm_
    login_url = "index"
    template_name = "authentication/users/add_user.html"
    permission_required = "authentication.add_user"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.company_id == 1:
            companies_queryset = Company.objects.filter(
                 visible=True, actived=True)
            context["form"].fields[
                "vehicles_to_monitor"
            ].queryset = Vehicle.objects.filter(visible=True, is_active=True)
            context["form"].fields[
                "group_vehicles"
            ].queryset = VehicleGroup.objects.filter(visible=True)
            context["form"].fields["process_type"].queryset = Process.objects.filter(
                Q(company__provider_id=self.request.user.company_id)
                | Q(company_id=self.request.user.company_id)
            )
        else:
            companies_queryset = self.request.user.companies_to_monitor.filter(visible=True, actived=True) if self.request.user.companies_to_monitor.exists() else Company.objects.filter(
                Q(id=self.request.user.company_id) | Q(provider_id=self.request.user.company_id),
                visible=True,
                actived=True,
            )

            user_vehicles = self.request.user.vehicles_to_monitor.filter(visible=True, is_active=True) if self.request.user.vehicles_to_monitor.exists() else Vehicle.objects.none()
            vehicles = user_vehicles

            if companies_queryset.exists():
                company_vehicles = Vehicle.objects.filter(company__in=companies_queryset, visible=True, is_active=True)
                vehicles = user_vehicles | company_vehicles

            context["form"].fields["vehicles_to_monitor"].queryset = vehicles.distinct()

            if not companies_queryset.exists() and not user_vehicles.exists():
                context["form"].fields["vehicles_to_monitor"].queryset = Vehicle.objects.filter(
                    Q(company__provider_id=self.request.user.company_id) | Q(company_id=self.request.user.company_id),
                    visible=True,
                    is_active=True,
                )
            else:
                if not vehicles:
                    vehicles = Vehicle.objects.filter(
                        Q(company__provider_id=self.request.user.company_id) | Q(company_id=self.request.user.company_id),
                        visible=True,
                        is_active=True,
                    ) | user_vehicles
                    context["form"].fields["vehicles_to_monitor"].queryset = vehicles.distinct()

            users = User.objects.filter(
                Q(company__provider_id=self.request.user.company_id)
                | Q(company=self.request.user.company_id),
                visible=True,
            )
            users_ids = list(users.values_list("id", flat=True))
            # Filtrar VehicleGroup por los usuarios
            vehicle_groups = VehicleGroup.objects.filter(
                created_by__in=users_ids, visible=True
            )
            context["form"].fields["group_vehicles"].queryset = vehicle_groups
        companies_queryset = companies_queryset.order_by('company_name')
        context["form"].fields["company"].queryset = companies_queryset
        context["form"].fields["companies_to_monitor"].queryset = companies_queryset
        return context

    def form_valid(self, form):
        form.instance.actived = True
        # No guardar las relaciones ManyToManyField
        user = form.save(commit=False)
        user.modified_by = self.request.user
        user.created_by = self.request.user
        user.save()  # Guardar el objeto de usuario
        # Guardar las relaciones ManyToManyField manualmente
        form.save_m2m()
        return redirect("PermissionUsers", pk=user.id)


class UpdateUserView(PermissionRequiredMixin, LoginRequiredMixin, generic.UpdateView):

    """Vista en la cual se le permite al usuario editar la informacion del cada usuario,
    ademas no podra editar la contraseña y cuenta con su propio formulario para hacer la
    modificaciones"""

    login_url = "index"
    template_name = "authentication/users/update_user.html"
    permission_required = "authentication.change_user"
    model = User
    form_class = UserChangeForm_
    success_url = reverse_lazy("users")

    def get_success_url(self):
        # Asegúrate de que el nombre de la URL sea correcto y esté definido en tus archivos de URL.
        return reverse("users")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.company_id == 1:
            companies_queryset = Company.objects.filter(
                 visible=True, actived=True)
            context["form"].fields[
                "vehicles_to_monitor"
            ].queryset = Vehicle.objects.filter(visible=True, is_active=True)
            context["form"].fields[
                "group_vehicles"
            ].queryset = VehicleGroup.objects.filter(visible=True)
        else:
            companies_queryset = self.request.user.companies_to_monitor.filter(visible=True, actived=True) if self.request.user.companies_to_monitor.exists() else Company.objects.filter(
                Q(id=self.request.user.company_id) | Q(provider_id=self.request.user.company_id),
                visible=True,
                actived=True,
            )

            user_vehicles = self.request.user.vehicles_to_monitor.filter(visible=True, is_active=True) if self.request.user.vehicles_to_monitor.exists() else Vehicle.objects.none()
            vehicles = user_vehicles

            if companies_queryset.exists():
                company_vehicles = Vehicle.objects.filter(company__in=companies_queryset, visible=True, is_active=True)
                vehicles = user_vehicles | company_vehicles

            context["form"].fields["vehicles_to_monitor"].queryset = vehicles.distinct()

            if not companies_queryset.exists() and not user_vehicles.exists():
                context["form"].fields["vehicles_to_monitor"].queryset = Vehicle.objects.filter(
                    Q(company__provider_id=self.request.user.company_id) | Q(company_id=self.request.user.company_id),
                    visible=True,
                    is_active=True,
                )
            else:
                if not vehicles:
                    vehicles = Vehicle.objects.filter(
                        Q(company__provider_id=self.request.user.company_id) | Q(company_id=self.request.user.company_id),
                        visible=True,
                        is_active=True,
                    ) | user_vehicles
                    context["form"].fields["vehicles_to_monitor"].queryset = vehicles.distinct()
            users = User.objects.filter(
                Q(company__provider_id=self.request.user.company_id)
                | Q(company=self.request.user.company_id),
                visible=True,
            )
            users_ids = list(users.values_list("id", flat=True))
            # Filtrar VehicleGroup por los usuarios
            vehicle_groups = VehicleGroup.objects.filter(
                created_by__in=users_ids, visible=True
            )
            context["form"].fields["group_vehicles"].queryset = vehicle_groups
        companies_queryset = companies_queryset.order_by('company_name')
        context["form"].fields["company"].queryset = companies_queryset
        context["form"].fields["companies_to_monitor"].queryset = companies_queryset  
        return context

    def form_valid(self, form):
        form.instance.actived = True
        # No guardar las relaciones ManyToManyField
        user = form.save(commit=False)
        user.modified_by = self.request.user
        user.save()  # Guardar el objeto de usuario
        form.save_m2m()
        page_update = HttpResponse(
            ""
        )  # O puedes enviar algún contenido si es necesario.
        page_update["HX-Redirect"] = self.get_success_url()
        return page_update


class DeleteUser(PermissionRequiredMixin, LoginRequiredMixin, generic.UpdateView):
    """
    Vista que permite eliminar un usuario.
    """

    model = User
    permission_required = "authentication.delete_user"
    success_url = reverse_lazy("users")
    template_name = "authentication/users/delete_user.html"
    fields = ["visible"]

    def get_success_url(self):
        # Asegúrate de que el nombre de la URL sea correcto y esté definido en tus archivos de URL.
        return reverse("users")

    def form_valid(self, form):
        form = form.save(commit=False)
        form.modified_by = self.request.user
        form.visible = False
        form.is_active = False
        form.save()

        page_update = HttpResponse(
            ""
        )  # O puedes enviar algún contenido si es necesario.
        page_update["HX-Redirect"] = self.get_success_url()
        return page_update


class PermissionUserView(
    PermissionRequiredMixin, LoginRequiredMixin, generic.UpdateView
):
    """
    Vista que permite asignar los grupos (módulos) y permisos a un usuario después de que se
    realice la creación del usuario.
    """

    model = User
    success_url = reverse_lazy("users")
    permission_required = "authentication.change_user"
    template_name = "authentication/users/user_permissions.html"
    form_class = PermissionForm

    def get_success_url(self):
        # Asegúrate de que el nombre de la URL sea correcto y esté definido en tus archivos de URL.
        return reverse("users")

    def get_initial(self, *args, **kwargs):
        """
        Obtiene los valores iniciales para el formulario de actualización.
        Si el usuario ya tiene permisos asignados, se establece el valor inicial del campo "user_permissions"
        con los IDs de los permisos del usuario.
        """
        initial = super().get_initial(*args, **kwargs)
        if self.object.user_permissions.exists() or self.object.groups.exists():
            initial["user_permissions"] = self.object.user_permissions.values_list(
                "id", flat=True
            )
            initial["groups"] = self.object.groups.values_list(
                "id", flat=True
            )  # Ajusta esta línea

        return initial

    def get_context_data(self, **kwargs):
        """
        Sobrescribe el método get_context_data para personalizar el contexto que se pasa al template.
        Este método limita el queryset del campo "groups" y "user_permission" en el formulario
        a aquellos grupos y permisos que están asociados a la compañía del usuario.
        """
        context = super().get_context_data(**kwargs)
        # Obtiene la instancia del usuario que se está actualizando
        user = self.object
        # Obtiene la instancia de la compañía asociada al usuario
        company = user.company
        # Inicializa una lista vacía para almacenar los grupos de usuario permitidos
        user_group = []
        # Obtiene todos los módulos asociados a la compañía del usuario y extrae sus IDs de grupo
        modules_for_company = Module.objects.filter(company=company).values_list(
            "group_id", flat=True
        )
        # Itera sobre el queryset de grupos del formulario
        for group in context["form"].fields["groups"].queryset:
            # Si el ID del grupo está en los módulos permitidos para la compañía, lo añade a la lista user_group
            if group.id in modules_for_company:
                user_group.append(group)
        # Actualiza el queryset del campo "groups" en el formulario con los grupos permitidos (user_group)
        groups = Group.objects.filter(id__in=[g.id for g in user_group])
        grouped_permissions = []
        for group in groups:
            group_content_type_ids = group.permissions.values_list(
                "content_type_id", flat=True
            )
            permissions_with_same_content_type_id = Permission.objects.filter(
                content_type_id__in=group_content_type_ids
            )
            grouped_permissions.append((group, permissions_with_same_content_type_id))
        # Agrega los permisos agrupados al contexto
        context["grouped_permissions"] = grouped_permissions
        context["user_group"] = self.object.groups.values_list("id", flat=True)
        context["user_permissions"] = self.object.user_permissions.values_list(
            "id", flat=True
        )
        return context

    def form_valid(self, form):
        """
        Sobrescribe el método form_valid para guardar el formulario y retornar una respuesta HTTP
        204.
        """
        form.save()
        page_update = HttpResponse(
            ""
        )  # O puedes enviar algún contenido si es necesario.
        page_update["HX-Redirect"] = self.get_success_url()
        return page_update

    def form_invalid(self, form):
        """
        Sobrescribe el método form_invalid para renderizar el formulario con errores.
        """
        return render(self.request, self.template_name, {"form": form})


class UpdatePermissionUser(
    PermissionRequiredMixin, LoginRequiredMixin, generic.UpdateView
):

    """
    Vista que permite asignar los grupos (módulos) y permisos a un usuario después de que se
    realice la creación del usuario.
    """

    model = User
    success_url = reverse_lazy("users")
    permission_required = "authentication.change_user"
    template_name = "authentication/users/update_permissions.html"
    form_class = PermissionForm

    def get_success_url(self):
        # Asegúrate de que el nombre de la URL sea correcto y esté definido en tus archivos de URL.
        return reverse("users")

    def get_initial(self, *args, **kwargs):
        """
        Obtiene los valores iniciales para el formulario de actualización.
        Si el usuario ya tiene permisos asignados, se establece el valor inicial del campo "user_permissions"
        con los IDs de los permisos del usuario.
        """
        initial = super().get_initial(*args, **kwargs)
        if self.object.user_permissions.exists() or self.object.groups.exists():
            initial["user_permissions"] = self.object.user_permissions.values_list(
                "id", flat=True
            )
            initial["groups"] = self.object.groups.values_list(
                "id", flat=True
            )  # Ajusta esta línea

        return initial

    def get_context_data(self, **kwargs):
        """
        Sobrescribe el método get_context_data para personalizar el contexto que se pasa al template.
        Este método limita el queryset del campo "groups" y "user_permission" en el formulario
        a aquellos grupos y permisos que están asociados a la compañía del usuario.
        """
        context = super().get_context_data(**kwargs)
        # Obtiene la instancia del usuario que se está actualizando
        user = self.object
        # Obtiene la instancia de la compañía asociada al usuario
        company = user.company
        # Inicializa una lista vacía para almacenar los grupos de usuario permitidos
        user_group = []
        # Obtiene todos los módulos asociados a la compañía del usuario y extrae sus IDs de grupo
        modules_for_company = Module.objects.filter(company=company).values_list(
            "group_id", flat=True
        )
        # Itera sobre el queryset de grupos del formulario
        for group in context["form"].fields["groups"].queryset:
            # Si el ID del grupo está en los módulos permitidos para la compañía, lo añade a la lista user_group
            if group.id in modules_for_company:
                user_group.append(group)
        # Actualiza el queryset del campo "groups" en el formulario con los grupos permitidos (user_group)
        groups = Group.objects.filter(id__in=[g.id for g in user_group])
        grouped_permissions = []
        for group in groups:
            group_content_type_ids = group.permissions.values_list(
                "content_type_id", flat=True
            )
            permissions_with_same_content_type_id = Permission.objects.filter(
                content_type_id__in=group_content_type_ids
            )
            grouped_permissions.append((group, permissions_with_same_content_type_id))
        # Agrega los permisos agrupados al contexto
        context["grouped_permissions"] = grouped_permissions
        context["user_group"] = self.object.groups.values_list("id", flat=True)
        context["user_permissions"] = self.object.user_permissions.values_list(
            "id", flat=True
        )
        return context

    def form_valid(self, form):
        """
        Sobrescribe el método form_valid para guardar el formulario y retornar una respuesta HTTP 204.
        """
        form.save()
        page_update = HttpResponse(
            ""
        )  # O puedes enviar algún contenido si es necesario.
        page_update["HX-Redirect"] = self.get_success_url()
        return page_update

    def form_invalid(self, form):
        """
        Sobrescribe el método form_invalid para renderizar el formulario con errores.
        """
        return render(self.request, self.template_name, {"form": form})


class ProfileUserView(LoginRequiredMixin, generic.UpdateView):
    """Vista que muestra la lista de usuarios."""

    """Vista en la cual se le permite al usuario editar la informacion del cada usuario, ademas
    no podra editar la contraseña y cuenta con su propio formulario para hacer la modificaciones"""

    model = User
    login_url = "login"
    template_name = "authentication/users/profile_user.html"
    form_class = UserProfileForm
    success_url = reverse_lazy("users")

    def dispatch(self, request, *args, **kwargs):
        if "pk" not in self.kwargs:
            # Redirige al usuario al inicio de sesión si no se proporciona una pk
            return HttpResponseRedirect(reverse("login"))
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.save()
        return HttpResponse(status=204, headers={"HX-Trigger": "ListUserChanged"})

    def form_invalid(self, form):
        """
        Llamado cuando se envía el formulario y es inválido.
        Muestra de nuevo el formulario con los errores.
        """
        return render(self.request, self.template_name, {"form": form})


class PasswordUserView(LoginRequiredMixin, FormView):
    """
    Vista para cambiar la contraseña del usuario.

    Esta vista maneja las solicitudes GET y POST para cambiar la contraseña del usuario.
    Utiliza un formulario personalizado para cambiar la contraseña.

    Attributes:
        template_name (str): El nombre del archivo de plantilla para renderizar el formulario de cambio de contraseña.
        login_url (str): La URL a la que se redirige si el usuario no está autenticado.
        success_url (str): La URL a la que se redirige después de cambiar la contraseña con éxito.
        form_class (class): La clase del formulario personalizado para cambiar la contraseña.

    Methods:
        dispatch(*args, **kwargs): Sobrescribe el método dispatch para agregar el decorador `never_cache`.
        get(request, *args, **kwargs): Maneja las solicitudes GET y renderiza el formulario de cambio de contraseña.
        post(request, *args, **kwargs): Maneja las solicitudes POST y procesa el formulario de cambio de contraseña.
    """

    template_name = "authentication/users/password_user.html"
    login_url = "login"
    success_url = reverse_lazy("main")
    form_class = SetPasswordForm_  # Asegúrate de que este es tu formulario personalizado para cambiar la contraseña

    @method_decorator(never_cache)
    def dispatch(self, *args, **kwargs):
        """
        Sobrescribe el método dispatch para agregar el decorador `never_cache`.

        Args:
            *args: Lista de argumentos variables.
            **kwargs: Diccionario de argumentos clave.

        Returns:
            El resultado del método dispatch de la superclase.

        """
        return super().dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        """
        Maneja las solicitudes GET y renderiza el formulario de cambio de contraseña.

        Args:
            request (HttpRequest): El objeto de solicitud HTTP.
            *args: Lista de argumentos variables.
            **kwargs: Diccionario de argumentos clave.

        Returns:
            HttpResponse: El objeto de respuesta HTTP que contiene la plantilla renderizada.

        """
        form = self.form_class(user=request.user)
        return render(request, self.template_name, {"form": form})

    def post(self, request, *args, **kwargs):
        """
        Maneja las solicitudes POST y procesa el formulario de cambio de contraseña.

        Args:
            request (HttpRequest): El objeto de solicitud HTTP.
            *args: Lista de argumentos variables.
            **kwargs: Diccionario de argumentos clave.

        Returns:
            HttpResponse: El objeto de respuesta HTTP.

        """

        form = self.form_class(user=request.user, data=request.POST)
        if form.is_valid():
            form.save()
            update_session_auth_hash(
                request, form.user
            )  # Para no desloguear al usuario
            response = HttpResponse("")
            response["HX-Redirect"] = self.success_url
            return response
        else:
            # Aquí, si el formulario no es válido, simplemente vuelve a renderizar la misma página
            # con el formulario que ahora incluye los errores.
            return render(request, self.template_name, {"form": form})
