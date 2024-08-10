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
import asyncio
import json
import os
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
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
from django.core.paginator import Paginator
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from django.views.generic import ListView
from django.utils.translation import gettext_lazy as _
from django.views import View, generic
from django.views.decorators import cache, csrf
from django.views.decorators.cache import never_cache
from django.views.generic import TemplateView
from django.views.generic.edit import FormView

from apps.log.mixins import (CreateAuditLogAsyncMixin, CreateAuditLogSyncMixin,
                             DeleteAuditLogSyncMixin, UpdateAuditLogSyncMixin,
                             obtener_ip_publica)
from apps.log.utils import log_action
from apps.realtime.apis import extract_number, sort_key
from apps.realtime.models import Vehicle, VehicleGroup
from apps.whitelabel.models import Company, Module, Process, Theme

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
    @method_decorator(never_cache)
    def dispatch(self, request, *args, **kwargs):
        """
        Si el usuario está autentificado, redirígelo a la página principal `main`.

        :param request: El objeto de solicitud actual.
        :return: Se devuelve el método super().dispatch().
        """
        if self.redirect_authenticated_user and request.user.is_authenticated:
            return redirect("main")
        if request.session.get("email"):
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


def has_group_by_id(self, group_id):
    return self.groups.filter(id=group_id).exists()


User.add_to_class("has_group_by_id", has_group_by_id)


class LoginView_(FormView):
    """
    Vista que autentica a un usuario en la aplicación.
    """

    template_name = "authentication/login.html"
    form_class = LoginForm_
    success_url = reverse_lazy("main")
    redirect_authenticated_user = True

    @method_decorator(csrf.csrf_protect)
    @method_decorator(cache.never_cache)
    def dispatch(self, request, *args, **kwargs):
        if self.redirect_authenticated_user and request.user.is_authenticated:
            return redirect("main")
        if not request.session.get("email"):
            return redirect("index")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        email = self.request.session.get("email")
        if email:
            user = User.objects.filter(email=email).first()
            if user:
                company_theme = Theme.objects.filter(company_id=user.company_id).first()
                company_user = Company.objects.filter(id=user.company_id).first()
                provider_theme = Theme.objects.filter(company_id=user.company.provider_id).first() if user.company.provider_id else None
                
                if provider_theme and not company_theme:
                    # Crear el tema de la compañía copiando el del proveedor
                    company_theme = Theme(
                        company_id=user.company_id,
                        button_color=provider_theme.button_color,
                        sidebar_color=provider_theme.sidebar_color,
                        opacity=provider_theme.opacity,
                    )

                    # Copiar imágenes del proveedor
                    for field in ['lock_screen_image', 'sidebar_image']:
                        provider_image = getattr(provider_theme, field)
                        if provider_image and provider_image.name:
                            # Generar un nombre de archivo único para la nueva copia
                            ext = provider_image.name.split('.')[-1]
                            new_file_name = f"{field}_{user.company_id}.{ext}"
                            new_file_path = os.path.normpath(os.path.join('uploads', new_file_name)).replace('\\', '/')

                            # Copiar el archivo en el almacenamiento
                            with default_storage.open(provider_image.name, 'rb') as f:
                                file_content = f.read()
                                default_storage.save(new_file_path, ContentFile(file_content))

                            # Asignar la nueva ruta de archivo al campo correspondiente del tema
                            setattr(company_theme, field, new_file_path)

                    company_theme.save()

                if company_user and not company_user.company_logo:
                    company_provider = Company.objects.filter(id=user.company.provider_id).first()
                    if company_provider:
                        company_user.company_logo = company_provider.company_logo
                        company_user.save()

                context.update({
                    "company_logo": company_user.company_logo if company_user else None,
                    "username": user.username,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "email": user.email,
                    "theme": company_theme.lock_screen_image if company_theme else provider_theme.lock_screen_image,
                    "profile_picture": user.profile_picture.url if user.profile_picture else "/static/Perfil/Perfil.png",
                    "color_theme": company_theme.button_color if company_theme else provider_theme.button_color,
                })
                self.request.session["username"] = user.username

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

        if user:
            login(self.request, user)
            self.request.session.set_expiry(0)
            group_redirects = {
                18: "main",
                14: "companies:main_ticket",
                1: "events:list_user_events",
                2: "companies:companies",
                3: "users",
                4: "companies:module",
                5: "realtime:simcards",
                6: "realtime:devices",
                7: "realtime:commands",
                8: "realtime:vehicles",
                9: "realtime:group_vehicles",
                10: "realtime:geozones",
                11: "checkpoints:list_drivers",
                12: "checkpoints:list_score_configuration",
                13: "checkpoints:report_today",
                15: "realtime:dataplan",
                17: "realtime:add_configuration_report",
                # Agrega más grupos y URLs aquí según sea necesario
            }

            for group_id, redirect_url in group_redirects.items():
                if user.has_group_by_id(group_id):
                    return redirect(redirect_url)
            return redirect(self.success_url)
        else:
            form.add_error("password", _("The password is incorrect. Please try again."))
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


class UserLisTemplate(PermissionRequiredMixin, LoginRequiredMixin, ListView):
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
        paginate_by = self.request.POST.get('paginate_by', None)  # Obtener paginate_by de los parámetros POST

        if paginate_by is None:
            session_filters = self.request.session.get(
                f"filters_sorted_users_{self.request.user.id}", {}
            )
            paginate_by = session_filters.get("paginate_by", 15)
            # Convertir a entero si es una lista
            try:
                paginate_by = int(
                    paginate_by[0]
                )  # Convertir el primer elemento de la lista a entero
            except (TypeError, ValueError):
                paginate_by = int(paginate_by) if paginate_by else 15
            # Añadir paginate_by a self.request.GET para asegurar que esté presente
            self.request.POST = self.request.POST.copy()
            self.request.POST['paginate_by'] = paginate_by
        return int(self.request.POST['paginate_by'])

    def get_queryset(self):
        """
        Obtiene el conjunto de datos de los comandos de envío filtrados y ordenados.

        Returns:
            QuerySet: El conjunto de datos de los comandos de envío filtrados y ordenados.
        """
        user = self.request.user
        company = user.company
        params = self.request.GET if self.request.method == 'GET' else self.request.POST
        query = params.get("query", "").lower()
        search = params.get("q", query).lower()
        if 'order_by' not in params and 'paginate_by' not in params and 'page' not in params:
            # Limpiar los filtros de la sesión
            if f"filters_sorted_users_{user.id}" in self.request.session:
                del self.request.session[f"filters_sorted_users_{user.id}"]
                self.request.session.modified = True
        # Recuperar filtros almacenados en la sesión
        session_filters = self.request.session.get(f'filters_sorted_users_{user.id}', {})
        order_by = params.get('order_by', session_filters.get('order_by', ['company'])[0])
        direction = params.get('direction', session_filters.get('direction',['asc'])[0])
        # Actualizar los filtros con los parámetros actuales de la solicitud GET
        session_filters.update(params)
        # Actualizar los filtros de la sesión con los nuevos parámetros
        self.request.session[f"filters_sorted_users_{user.id}"] = session_filters
        self.request.session.modified = True
        users = fetch_all_user(company.id, user.id, search)
        # Función para convertir los valores a minúsculas y extraer números cuando sea necesario
        key_function = sort_key(order_by)
        reverse = direction == 'desc'
        try:
            sorted_queryset = sorted(users, key=key_function, reverse=reverse)
        except KeyError:
            # Ordenamiento por defecto si la clave no existe
            sorted_queryset = sorted(
                users, key=lambda x: x["company"].lower(), reverse=reverse
            )

        return sorted_queryset

    def get_context_data(self, **kwargs):
        """
        Obtiene el contexto de datos para renderizar la vista.

        Args:
            **kwargs: Argumentos clave adicionales.

        Returns:
            dict: El contexto de datos para renderizar la vista.
        """
        context = super().get_context_data(**kwargs)
        paginate_by = self.get_paginate_by(None)
        context["paginate_by"] = paginate_by
        # Simplificación directa para calcular start_number
        page_number = context.get("page_obj").number if context.get("page_obj") else 1
        context["start_number"] = (page_number - 1) * self.get_paginate_by(None)
        session_filters = self.request.session.get(f'filters_sorted_users_{self.request.user.id}', {})
        order_by = self.request.GET.get('order_by') or self.request.POST.get('order_by') or session_filters.get('order_by', ['company'])[0]
        direction = self.request.GET.get('direction') or self.request.POST.get('direction') or session_filters.get('direction', ['asc'])[0]
        context['order_by'] = order_by
        context['direction'] = direction
        return context
    
    @method_decorator(csrf_protect)
    def post(self, request, *args, **kwargs):
        # Obtén el número de página desde la solicitud POST
        page_number = request.POST.get('page', 1)
        # Modifica la consulta para aplicar la paginación
        self.object_list = self.get_queryset()
        paginator = Paginator(self.object_list, self.get_paginate_by(None))
        page_obj = paginator.get_page(page_number)
        context = self.get_context_data(object_list=page_obj.object_list, page_obj=page_obj)
        return self.render_to_response(context)


class AddUserView(PermissionRequiredMixin, LoginRequiredMixin, CreateAuditLogSyncMixin, generic.CreateView):
    """Vista que permite a los usuarios agregar un nuevo usuario a la base de datos.
    Utiliza un formulario personalizado para la creación de usuarios.

    Atributos:
        model (Model): El modelo de datos para los usuarios.
        form_class (Form): El formulario que se utiliza para crear nuevos usuarios.
        login_url (str): La URL a la que se redirige si el usuario no está autenticado.
        template_name (str): La plantilla HTML que se usa para renderizar la vista.
        permission_required (str): El permiso necesario para acceder a esta vista."""

    model = User
    form_class = UserCreationForm_
    login_url = "index"
    template_name = "authentication/users/add_user.html"
    permission_required = "authentication.add_user"

    def get_context_data(self, **kwargs):
        """
        Proporciona datos adicionales al contexto de la plantilla.

        Args:
            **kwargs: Argumentos adicionales que se pasan a la función.

        Returns:
            dict: Contexto adicional para la plantilla, incluyendo los formularios y el color del botón.
        """
        context = super().get_context_data(**kwargs)
        context["form"].fields["company"].queryset = self.get_companies_queryset()
        context["form"].fields["vehicles_to_monitor"].queryset = self.get_vehicles_queryset()
        context["form"].fields["group_vehicles"].queryset = self.get_vehicle_groups_queryset()
        context["form"].fields["process_type"].queryset = self.get_process_types_queryset()
        context["form"].fields["company"].choices = self.get_companies_choices()
        context["form"].fields["companies_to_monitor"].choices = self.get_companies_to_monitor_choices()
        context["button_color"] = self.request.user.company.theme_set.all().first().button_color
        context["leader_button"] = self.get_leader_button()
        return context

    def get_companies_queryset(self):
        """
        Obtiene el queryset de compañías basado en el usuario autenticado.

        Returns:
            QuerySet: El queryset de compañías filtrado según las reglas de visibilidad y activación.
        """
        user = self.request.user
        if user.company_id == 1:
            return Company.objects.filter(visible=True, actived=True)
        return user.companies_to_monitor.filter(visible=True, actived=True) if user.companies_to_monitor.exists() else Company.objects.filter(
            Q(id=user.company_id) | Q(provider_id=user.company_id), visible=True, actived=True
        )

    def get_vehicles_queryset(self):
        """
        Obtiene el queryset de vehículos basado en las compañías y vehículos que el usuario puede monitorear.

        Returns:
            QuerySet: El queryset de vehículos filtrado según las reglas de visibilidad y activación.
        """
        user = self.request.user
        companies_queryset = self.get_companies_queryset()
        if user.company_id == 1:
            return Vehicle.objects.filter(visible=True, is_active=True)
        user_vehicles = user.vehicles_to_monitor.filter(visible=True, is_active=True) if user.vehicles_to_monitor.exists() else Vehicle.objects.none()
        vehicles = user_vehicles
        if companies_queryset.exists():
            company_vehicles = Vehicle.objects.filter(company__in=companies_queryset, visible=True, is_active=True)
            vehicles = user_vehicles | company_vehicles
        if not companies_queryset.exists() and not user_vehicles.exists():
            return Vehicle.objects.filter(Q(company__provider_id=user.company_id) | Q(company_id=user.company_id), visible=True, is_active=True)
        return vehicles.distinct()

    def get_vehicle_groups_queryset(self):
        """
        Obtiene el queryset de grupos de vehículos basado en el usuario autenticado.

        Returns:
            QuerySet: El queryset de grupos de vehículos filtrado según el usuario y la visibilidad.
        """
        user = self.request.user
        users = User.objects.filter(Q(company__provider_id=user.company_id) | Q(company=user.company_id), visible=True)
        users_ids = list(users.values_list("id", flat=True))
        return VehicleGroup.objects.filter(created_by__in=users_ids, visible=True)

    def get_process_types_queryset(self):
        """
        Obtiene el queryset de los proceso y los quita de forma predeterminada

        Returns:
            QuerySet: El queryset de tipos de procesos filtrado según el usuario.
        """
        user = self.request.user
        return Process.objects.none()

    def get_companies_choices(self):
        """
        Obtiene una lista de opciones de compañías para el formulario.

        Returns:
            list: Lista de tuplas con ID de la compañía y nombre de la compañía.
        """
        user = self.request.user
        companies_queryset = self.get_companies_queryset().order_by("company_name")
        if user.company_id == 1:
            return [(company.id, f"{company.company_name} -- {Company.objects.get(id=company.provider_id).company_name}") if company.provider_id else (company.id, company.company_name) for company in companies_queryset]
        return [(company.id, company.company_name) for company in companies_queryset]

    def get_companies_to_monitor_choices(self):
        """
        Obtiene una lista de opciones de compañías a monitorear para el formulario.

        Returns:
            list: Lista de tuplas con ID de la compañía y nombre de la compañía.
        """
        user = self.request.user
        companies_queryset = self.get_companies_queryset().order_by("company_name")
        if user.company_id == 1:
            return [(company.id, f"{company.company_name} -- {Company.objects.get(id=company.provider_id).company_name}") if company.provider_id else (company.id, company.company_name) for company in companies_queryset]
        return [(company.id, company.company_name) for company in companies_queryset]

    def get_leader_button(self):
        """
        Obtiene el valor del botón del líder basado en el tipo de proceso del usuario.

        Returns:
            str: Valor del botón del líder o una cadena vacía si no hay tipo de proceso.
        """
        user = self.request.user
        return user.process_type.process_type.lower() if user.process_type else ""

    def get_success_url(self):
        """
        Devuelve la URL de éxito a la que se redirige después de una creación exitosa.

        Returns:
            str: La URL de redirección.
        """
        return reverse("PermissionUsers", kwargs={"pk": self.object.id})

    def form_valid(self, form):
        """
        Maneja la validación del formulario y guarda el usuario creado. Devuelve una respuesta de redirección.

        Args:
            form (Form): El formulario con los datos del nuevo usuario.

        Returns:
            HttpResponse: Respuesta de redirección utilizando HTMX.
        """
        user = form.save(commit=False)
        user.modified_by = self.request.user
        user.created_by = self.request.user
        user.save()
        form.save_m2m()
        response = super().form_valid(form)
        # Prepara una respuesta con redirección usando HTMX
        return redirect(self.get_success_url())

class UpdateUserView(
    PermissionRequiredMixin,
    LoginRequiredMixin,
    UpdateAuditLogSyncMixin,
    generic.UpdateView,
):

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
        """
        Devuelve la URL de éxito a la que se redirige después de una creación exitosa.

        Returns:
            str: La URL de redirección.
        """
        return reverse("users") 

    def get_context_data(self, **kwargs):
        """
        Proporciona datos adicionales al contexto de la plantilla.

        Args:
            **kwargs: Argumentos adicionales que se pasan a la función.

        Returns:
            dict: Contexto adicional para la plantilla, incluyendo los formularios y el color del botón.
        """
        context = super().get_context_data(**kwargs)
        context["form"].fields["company"].queryset = self.get_companies_queryset()
        context["form"].fields["vehicles_to_monitor"].queryset = self.get_vehicles_queryset()
        context["form"].fields["group_vehicles"].queryset = self.get_vehicle_groups_queryset()
        context["form"].fields["process_type"].queryset = self.get_process_types_queryset()
        context["form"].fields["company"].choices = self.get_companies_choices()
        context["form"].fields["companies_to_monitor"].choices = self.get_companies_to_monitor_choices()
        context["button_color"] = self.request.user.company.theme_set.all().first().button_color
        context["leader_button"] = self.get_leader_button()
        context["user"]=self.request.user
        return context

    def get_companies_queryset(self):
        """
        Obtiene el queryset de compañías basado en el usuario autenticado.

        Returns:
            QuerySet: El queryset de compañías filtrado según las reglas de visibilidad y activación.
        """
        user = self.request.user
        if user.company_id == 1:
            return Company.objects.filter(visible=True, actived=True)
        return user.companies_to_monitor.filter(visible=True, actived=True) if user.companies_to_monitor.exists() else Company.objects.filter(
            Q(id=user.company_id) | Q(provider_id=user.company_id), visible=True, actived=True
        )

    def get_vehicles_queryset(self):
        """
        Obtiene el queryset de vehículos basado en las compañías y vehículos que el usuario puede monitorear.

        Returns:
            QuerySet: El queryset de vehículos filtrado según las reglas de visibilidad y activación.
        """
        user = self.request.user
        companies_queryset = self.get_companies_queryset()
        if user.company_id == 1:
            return Vehicle.objects.filter(visible=True, is_active=True)
        user_vehicles = user.vehicles_to_monitor.filter(visible=True, is_active=True) if user.vehicles_to_monitor.exists() else Vehicle.objects.none()
        vehicles = user_vehicles
        if companies_queryset.exists():
            company_vehicles = Vehicle.objects.filter(company__in=companies_queryset, visible=True, is_active=True)
            vehicles = user_vehicles | company_vehicles
        if not companies_queryset.exists() and not user_vehicles.exists():
            return Vehicle.objects.filter(Q(company__provider_id=user.company_id) | Q(company_id=user.company_id), visible=True, is_active=True)
        return vehicles.distinct()

    def get_vehicle_groups_queryset(self):
        """
        Obtiene el queryset de grupos de vehículos basado en el usuario autenticado.

        Returns:
            QuerySet: El queryset de grupos de vehículos filtrado según el usuario y la visibilidad.
        """
        user = self.request.user
        users = User.objects.filter(Q(company__provider_id=user.company_id) | Q(company=user.company_id), visible=True)
        users_ids = list(users.values_list("id", flat=True))
        return VehicleGroup.objects.filter(created_by__in=users_ids, visible=True)

    def get_process_types_queryset(self):
        """
        Obtiene el queryset de los proceso y los quita de forma predeterminada

        Returns:
            QuerySet: El queryset de tipos de procesos filtrado según el usuario.
        """
        user = self.request.user
        return Process.objects.none()

    def get_companies_choices(self):
        """
        Obtiene una lista de opciones de compañías para el formulario.

        Returns:
            list: Lista de tuplas con ID de la compañía y nombre de la compañía.
        """
        user = self.request.user
        companies_queryset = self.get_companies_queryset().order_by("company_name")
        if user.company_id == 1:
            return [(company.id, f"{company.company_name} -- {Company.objects.get(id=company.provider_id).company_name}") if company.provider_id else (company.id, company.company_name) for company in companies_queryset]
        return [(company.id, company.company_name) for company in companies_queryset]

    def get_companies_to_monitor_choices(self):
        """
        Obtiene una lista de opciones de compañías a monitorear para el formulario.

        Returns:
            list: Lista de tuplas con ID de la compañía y nombre de la compañía.
        """
        user = self.request.user
        companies_queryset = self.get_companies_queryset().order_by("company_name")
        if user.company_id == 1:
            return [(company.id, f"{company.company_name} -- {Company.objects.get(id=company.provider_id).company_name}") if company.provider_id else (company.id, company.company_name) for company in companies_queryset]
        return [(company.id, company.company_name) for company in companies_queryset]

    def get_leader_button(self):
        """
        Obtiene el valor del botón del líder basado en el tipo de proceso del usuario.

        Returns:
            str: Valor del botón del líder o una cadena vacía si no hay tipo de proceso.
        """
        user = self.request.user
        return user.process_type.process_type.lower() if user.process_type else ""

    def form_valid(self, form):
        """
        Maneja la validación del formulario y guarda el usuario creado. Devuelve una respuesta de redirección.

        Args:
            form (Form): El formulario con los datos del nuevo usuario.

        Returns:
            HttpResponse: Respuesta de redirección utilizando HTMX.
        """
        form.instance.actived = True
        user = form.save(commit=False)
        user.modified_by = self.request.user
        user.save()
        form.save_m2m()

        # Llama al método form_valid de la clase padre para registrar la acción en el log de auditoría
        response = super().form_valid(form)

        # Prepara una respuesta con redirección usando HTMX
        page_update = HttpResponse("")
        page_update["HX-Redirect"] = self.get_success_url()
        return page_update


class DeleteUser(
    PermissionRequiredMixin,
    LoginRequiredMixin,
    DeleteAuditLogSyncMixin,
    generic.UpdateView,
):
    model = User
    permission_required = "authentication.delete_user"
    success_url = reverse_lazy("users")
    template_name = "authentication/users/delete_user.html"
    fields = ["visible"]

    def get_success_url(self):
        """
        Devuelve la URL de éxito a la que se redirige después de una creación exitosa.

        Returns:
            str: La URL de redirección.
        """
        return reverse("users")

    def form_valid(self, form):
        """
        Maneja la validación del formulario y guarda el usuario creado. Devuelve una respuesta de redirección.

        Args:
            form (Form): El formulario con los datos del nuevo usuario.

        Returns:
            HttpResponse: Respuesta de redirección utilizando HTMX.
        """
        # Modifica el plan de datos en lugar de eliminarlo
        form.instance.modified_by = self.request.user
        form.instance.visible = False
        form.instance.is_active = False
        form.save()

        # Llama al método form_valid de la clase padre para registrar la acción en el log de auditoría
        response = super().form_valid(form)

        # Prepara una respuesta con redirección usando HTMX
        page_update = HttpResponse("")
        page_update["HX-Redirect"] = self.get_success_url()
        return page_update


class PermissionUserView(
    PermissionRequiredMixin,
    LoginRequiredMixin,
    UpdateAuditLogSyncMixin,
    generic.UpdateView,
):
    """
    Vista que permite asignar los grupos (módulos) y permisos a un usuario después de su creación.

    Atributos:
        model (Model): El modelo de datos para los usuarios.
        form_class (Form): El formulario para asignar permisos y grupos al usuario.
        template_name (str): La plantilla HTML que se usa para renderizar la vista.
        permission_required (str): El permiso necesario para acceder a esta vista.
        success_url (str): URL de redirección después de una actualización exitosa.
    """

    model = User
    form_class = PermissionForm
    template_name = "authentication/users/user_permissions.html"
    permission_required = "authentication.change_user"
    success_url = reverse_lazy("users")

    def get_success_url(self):
        """
        Devuelve la URL de redirección después de una actualización exitosa.

        Returns:
            str: La URL de redirección.
        """
        return reverse("users")

    def get_initial(self, *args, **kwargs):
        """
        Proporciona valores iniciales para el formulario, incluyendo permisos y grupos.

        Args:
            *args: Argumentos adicionales que se pasan a la función.
            **kwargs: Argumentos clave adicionales que se pasan a la función.

        Returns:
            dict: Valores iniciales para el formulario.
        """
        initial = super().get_initial(*args, **kwargs)
        initial["user_permissions"] = self.get_initial_permissions()
        initial["groups"] = self.get_initial_groups()
        return initial

    def get_initial_permissions(self):
        """
        Obtiene los permisos iniciales del usuario para prellenar el formulario.

        Returns:
            list: Lista de IDs de permisos que el usuario ya tiene.
        """
        if self.object.user_permissions.exists():
            return self.object.user_permissions.values_list("id", flat=True)
        return []

    def get_initial_groups(self):
        """
        Obtiene los grupos iniciales del usuario para prellenar el formulario.

        Returns:
            list: Lista de IDs de grupos a los que el usuario pertenece.
        """
        if self.object.groups.exists():
            return self.object.groups.values_list("id", flat=True)
        return []

    def get_context_data(self, **kwargs):
        """
        Proporciona datos adicionales al contexto de la plantilla.

        Args:
            **kwargs: Argumentos adicionales que se pasan a la función.

        Returns:
            dict: Contexto adicional para la plantilla, incluyendo permisos agrupados y datos del usuario.
        """
        context = super().get_context_data(**kwargs)
        context["grouped_permissions"] = self.get_grouped_permissions()
        context["user_group"] = self.object.groups.values_list("id", flat=True)
        context["user_permissions"] = self.object.user_permissions.values_list("id", flat=True)
        return context

    def get_grouped_permissions(self):
        """
        Obtiene los permisos agrupados por módulo basado en la compañía del usuario.

        Returns:
            list: Lista de tuplas, cada una contiene un grupo y los permisos asociados a ese grupo.
        """
        user = self.object
        company = user.company
        modules_for_company = Module.objects.filter(company=company).values_list("group_id", flat=True)
        user_group = [group for group in Group.objects.filter(id__in=modules_for_company) if group.id in modules_for_company]
        return [
            (group, Permission.objects.filter(content_type_id__in=group.permissions.values_list("content_type_id", flat=True)))
            for group in user_group
        ]

    def form_valid(self, form):
        """
        Maneja la validación del formulario, guarda los datos y registra la auditoría.

        Args:
            form (Form): El formulario con los datos del usuario.

        Returns:
            HttpResponse: Respuesta de redirección utilizando HTMX.
        """
        response = super().form_valid(form)
        user_permissions_before, groups_before = self.get_permissions_and_groups_before_save()
        user_permissions_after, groups_after = self.get_permissions_and_groups_after_save()

        self.log_audit(user_permissions_before, user_permissions_after, groups_before, groups_after)

        page_update = HttpResponse("")
        page_update["HX-Redirect"] = self.get_success_url()
        return page_update

    def get_permissions_and_groups_before_save(self):
        """
        Obtiene los permisos y grupos del usuario antes de guardar los cambios.

        Returns:
            tuple: Tupla con dos listas: permisos y grupos del usuario antes de guardar.
        """
        return (
            list(self.object.user_permissions.values_list("id", flat=True)),
            list(self.object.groups.values_list("id", flat=True))
        )

    def get_permissions_and_groups_after_save(self):
        """
        Obtiene los permisos y grupos del usuario después de guardar los cambios.

        Returns:
            tuple: Tupla con dos listas: permisos y grupos del usuario después de guardar.
        """
        self.object.refresh_from_db()
        return (
            list(self.object.user_permissions.values_list("id", flat=True)),
            list(self.object.groups.values_list("id", flat=True))
        )

    def log_audit(self, user_permissions_before, user_permissions_after, groups_before, groups_after):
        """
        Registra la auditoría de los cambios realizados en los permisos y grupos del usuario.

        Args:
            user_permissions_before (list): Lista de permisos del usuario antes de los cambios.
            user_permissions_after (list): Lista de permisos del usuario después de los cambios.
            groups_before (list): Lista de grupos del usuario antes de los cambios.
            groups_after (list): Lista de grupos del usuario después de los cambios.
        """
        user = self.request.user
        company_id = getattr(user, "company_id", None)
        view_name = self.__class__.__name__
        ip_address = asyncio.run(obtener_ip_publica(self.request))

        before = {
            "user_permissions": user_permissions_before,
            "groups": groups_before,
        }
        after = {
            "user_permissions": user_permissions_after,
            "groups": groups_after,
        }

        before_json = json.dumps(before, default=str)
        after_json = json.dumps(after, default=str)

        log_action(
            user=user,
            company_id=company_id,
            view_name=view_name,
            action=self.action,
            before=before_json,
            after=after_json,
            ip_address=ip_address,
        )


class UpdatePermissionUser(
    PermissionRequiredMixin,
    LoginRequiredMixin,
    UpdateAuditLogSyncMixin,
    generic.UpdateView,
):
    """
    Vista que permite asignar los grupos (módulos) y permisos a un usuario después de su creación.

    Atributos:
        model (Model): El modelo de datos para los usuarios.
        form_class (Form): El formulario para asignar permisos y grupos al usuario.
        template_name (str): La plantilla HTML que se usa para renderizar la vista.
        permission_required (str): El permiso necesario para acceder a esta vista.
        success_url (str): URL de redirección después de una actualización exitosa.

    """

    model = User
    form_class = PermissionForm
    template_name = "authentication/users/update_permissions.html"
    permission_required = "authentication.change_user"
    success_url = reverse_lazy("users")

    def get_success_url(self):
        """
        Devuelve la URL de redirección después de una actualización exitosa.

        Returns:
            str: La URL de redirección.
        """
        return reverse("users")

    def get_initial(self, *args, **kwargs):
        """
        Proporciona valores iniciales para el formulario, incluyendo permisos y grupos.

        Args:
            *args: Argumentos adicionales que se pasan a la función.
            **kwargs: Argumentos clave adicionales que se pasan a la función.

        Returns:
            dict: Valores iniciales para el formulario.
        """
        initial = super().get_initial(*args, **kwargs)
        initial["user_permissions"] = self.get_initial_permissions()
        initial["groups"] = self.get_initial_groups()
        return initial

    def get_initial_permissions(self):
        """
        Obtiene los permisos iniciales del usuario para prellenar el formulario.

        Returns:
            list: Lista de IDs de permisos que el usuario ya tiene.
        """
        if self.object.user_permissions.exists():
            return self.object.user_permissions.values_list("id", flat=True)
        return []

    def get_initial_groups(self):
        """
        Obtiene los grupos iniciales del usuario para prellenar el formulario.

        Returns:
            list: Lista de IDs de grupos a los que el usuario pertenece.
        """
        if self.object.groups.exists():
            return self.object.groups.values_list("id", flat=True)
        return []

    def get_context_data(self, **kwargs):
        """
        Proporciona datos adicionales al contexto de la plantilla.

        Args:
            **kwargs: Argumentos adicionales que se pasan a la función.

        Returns:
            dict: Contexto adicional para la plantilla, incluyendo permisos agrupados y datos del usuario.
        """
        context = super().get_context_data(**kwargs)
        context["grouped_permissions"] = self.get_grouped_permissions()
        context["user_group"] = self.object.groups.values_list("id", flat=True)
        context["user_permissions"] = self.object.user_permissions.values_list("id", flat=True)
        return context

    def get_grouped_permissions(self):
        """
        Obtiene los permisos agrupados por módulo basado en la compañía del usuario.

        Returns:
            list: Lista de tuplas, cada una contiene un grupo y los permisos asociados a ese grupo.
        """
        user = self.object
        company = user.company
        modules_for_company = Module.objects.filter(company=company).values_list("group_id", flat=True)
        user_group = [group for group in Group.objects.filter(id__in=modules_for_company) if group.id in modules_for_company]
        return [
            (group, Permission.objects.filter(content_type_id__in=group.permissions.values_list("content_type_id", flat=True)))
            for group in user_group
        ]

    def form_valid(self, form):
        """
        Maneja la validación del formulario, guarda los datos y registra la auditoría.

        Args:
            form (Form): El formulario con los datos del usuario.

        Returns:
            HttpResponse: Respuesta de redirección utilizando HTMX.
        """
        response = super().form_valid(form)
        user_permissions_before, groups_before = self.get_permissions_and_groups_before_save()
        user_permissions_after, groups_after = self.get_permissions_and_groups_after_save()

        self.log_audit(user_permissions_before, user_permissions_after, groups_before, groups_after)

        page_update = HttpResponse("")
        page_update["HX-Redirect"] = self.get_success_url()
        return page_update

    def get_permissions_and_groups_before_save(self):
        """
        Obtiene los permisos y grupos del usuario antes de guardar los cambios.

        Returns:
            tuple: Tupla con dos listas: permisos y grupos del usuario antes de guardar.
        """
        return (
            list(self.object.user_permissions.values_list("id", flat=True)),
            list(self.object.groups.values_list("id", flat=True))
        )

    def get_permissions_and_groups_after_save(self):
        """
        Obtiene los permisos y grupos del usuario después de guardar los cambios.

        Returns:
            tuple: Tupla con dos listas: permisos y grupos del usuario después de guardar.
        """
        self.object.refresh_from_db()
        return (
            list(self.object.user_permissions.values_list("id", flat=True)),
            list(self.object.groups.values_list("id", flat=True))
        )

    def log_audit(self, user_permissions_before, user_permissions_after, groups_before, groups_after):
        """
        Registra la auditoría de los cambios realizados en los permisos y grupos del usuario.

        Args:
            user_permissions_before (list): Lista de permisos del usuario antes de los cambios.
            user_permissions_after (list): Lista de permisos del usuario después de los cambios.
            groups_before (list): Lista de grupos del usuario antes de los cambios.
            groups_after (list): Lista de grupos del usuario después de los cambios.
        """
        user = self.request.user
        company_id = getattr(user, "company_id", None)
        view_name = self.__class__.__name__
        ip_address = asyncio.run(obtener_ip_publica(self.request))

        before = {
            "user_permissions": user_permissions_before,
            "groups": groups_before,
        }
        after = {
            "user_permissions": user_permissions_after,
            "groups": groups_after,
        }

        before_json = json.dumps(before, default=str)
        after_json = json.dumps(after, default=str)

        log_action(
            user=user,
            company_id=company_id,
            view_name=view_name,
            action=self.action,
            before=before_json,
            after=after_json,
            ip_address=ip_address,
        )

    def form_invalid(self, form):
        """
        Renderiza la plantilla con el formulario que contiene errores de validación.

        Args:
            form (Form): El formulario con errores de validación.

        Returns:
            HttpResponse: Respuesta de renderización de la plantilla con errores.
        """
        return render(self.request, self.template_name, {"form": form})


class ProfileUserView(LoginRequiredMixin, UpdateAuditLogSyncMixin, generic.UpdateView):
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

    def get_success_url(self):
        """
        Retorna la URL de redirección después de crear un nuevo usuario.
        """
        return reverse("Profile", kwargs={"pk": self.object.id})

    def form_valid(self, form):
        form.save()
        # Renderiza la misma plantilla con el formulario actualizado
        # Llama al método form_valid de la clase padre para registrar la acción en el log de auditoría
        response = super().form_valid(form)
        return redirect(self.get_success_url())

    def form_invalid(self, form):
        """
        Llamado cuando se envía el formulario y es inválido.
        Muestra de nuevo el formulario con los errores.
        """
        return render(self.request, self.template_name, {"form": form})


class PasswordUserView(LoginRequiredMixin, CreateAuditLogAsyncMixin, FormView):
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
    form_class = SetPasswordForm_  # Asegúrate de que este es tu formulario personalizado para cambiar la contraseña

    def get_success_url(self):
        """
        Retorna la URL de redirección después de crear un nuevo usuario.
        """
        return reverse("Profile", kwargs={"pk": self.request.user.id})

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

    def get_object(self):
        return self.request.user

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
            # Llama al método form_valid de la clase padre para registrar la acción en el log de auditoría
            response = super().form_valid(form)

            # Prepara una respuesta con redirección usando HTMX
            return redirect(self.get_success_url())
        else:
            # Aquí, si el formulario no es válido, simplemente vuelve a renderizar la misma página
            # con el formulario que ahora incluye los errores.
            return render(request, self.template_name, {"form": form})
