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

from django.contrib.auth import authenticate, login, update_session_auth_hash
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
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views import generic
from django.views.decorators import cache, csrf
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.generic import ListView, TemplateView
from django.views.generic.edit import FormView

from apps.log.mixins import (CreateAuditLogAsyncMixin, CreateAuditLogSyncMixin,
                             DeleteAuditLogSyncMixin, UpdateAuditLogSyncMixin,
                             obtener_ip_publica)
from apps.log.utils import log_action
from apps.realtime.apis import sort_key
from apps.realtime.models import Vehicle, VehicleGroup
from apps.whitelabel.models import Company, Module, Process

from .forms import (LoginForm_, PasswordChangeForm_, PasswordResetForm_,
                    PermissionForm, SetPasswordForm_, UserChangeForm_,
                    UserCreationForm_, UserProfileForm)
from .models import User
from .sql import fetch_all_user


class LoginView_(FormView):
    """
    Vista para el inicio de sesión de usuarios.

    Esta vista maneja el proceso de autenticación de usuarios basándose en un formulario.
    Si el usuario ya está autenticado, se le redirige automáticamente a la página principal.
    Los usuarios son redirigidos a diferentes URLs dependiendo del grupo al que pertenecen.
    """

    template_name = "authentication/login/login.html"  # Plantilla que se utilizará para renderizar el formulario de login
    form_class = LoginForm_  # El formulario que se utiliza para el inicio de sesión
    success_url = reverse_lazy("main")  # URL de redirección en caso de éxito
    redirect_authenticated_user = True  # Bandera para redirigir a usuarios ya autenticados

    # Diccionario para redirigir a los usuarios según el grupo al que pertenecen
    group_redirects = {
        18: "main",  # Grupo 18 es redirigido a 'main'
        14: "companies:main_ticket",  # Grupo 14 es redirigido a 'companies:main_ticket'
        1: "events:list_user_events",  # Grupo 1 es redirigido a 'events:list_user_events'
        2: "companies:companies",  # Grupo 2 es redirigido a 'companies:companies'
        # Se pueden agregar más grupos y redirecciones según sea necesario
    }

    @method_decorator(csrf.csrf_protect)
    @method_decorator(cache.never_cache)
    def dispatch(self, request, *args, **kwargs):
        """
        Maneja la solicitud HTTP y redirige a usuarios ya autenticados.

        Si el usuario está autenticado y `redirect_authenticated_user` es True, 
        se le redirige automáticamente a la página principal definida en 'main'.
        """
        if self.redirect_authenticated_user and request.user.is_authenticated:
            return redirect("main")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """
        Añade información adicional al contexto de la plantilla.

        Si hay un email en la sesión, intenta autenticar al usuario por dicho email.
        Si se encuentra un usuario válido, lo redirige según su grupo.
        """
        context = super().get_context_data(**kwargs)
        email = self.request.session.get("email")
        
        if email:
            user = self.authenticate_user_by_email(email)  # Autenticar por correo sin contraseña
            if user:
                return self.redirect_user_by_group(user)  # Redirige según el grupo del usuario
        return context

    def form_valid(self, form):
        """
        Maneja el caso en que el formulario sea válido.

        Intenta autenticar al usuario usando el email y la contraseña proporcionados.
        Si la autenticación tiene éxito, redirige al usuario según su grupo.
        En caso contrario, muestra un error en el formulario.
        """
        email = form.cleaned_data["email"]  # Obtiene el email ingresado
        password = form.cleaned_data["password"]  # Obtiene la contraseña ingresada
        user = self.authenticate_user_by_email(email, password)  # Autenticación por email y contraseña

        if user:
            return self.redirect_user_by_group(user)  # Redirige según el grupo del usuario
        else:
            form.add_error("password", _("The password is incorrect. Please try again."))
            return self.form_invalid(form)  # Muestra el formulario con el error

    def authenticate_user_by_email(self, email, password=None):
        """
        Autentica al usuario por correo y opcionalmente por contraseña.

        Si no se proporciona una contraseña, autentica únicamente por correo y devuelve el usuario.
        Si se proporciona una contraseña, se verifica y se autentica al usuario por ambos campos.

        Args:
            email (str): El correo electrónico del usuario.
            password (str, opcional): La contraseña del usuario.

        Returns:
            User: El usuario autenticado, o None si la autenticación falla.
        """
        user = User.objects.filter(email=email).first()  # Busca el usuario por email

        if user and password:
            # Autenticar por username y contraseña
            authenticated_user = authenticate(username=user.username, password=password)
            if authenticated_user:
                login(self.request, authenticated_user)  # Inicia sesión para el usuario autenticado
                self.request.session.set_expiry(0)  # La sesión se cerrará cuando se cierre el navegador
                return authenticated_user
        elif user:
            # Autenticar solo por email si no se proporciona contraseña
            login(self.request, user)  # Inicia sesión sin contraseña
            self.request.session.set_expiry(0)
            return user

        return None

    def redirect_user_by_group(self, user):
        """
        Redirige al usuario a la URL correspondiente según el grupo al que pertenece.

        Si el usuario pertenece a varios grupos, se le redirige según el primer grupo que coincida
        en el diccionario `group_redirects`.

        Args:
            user (User): El usuario autenticado.

        Returns:
            HttpResponseRedirect: Redirige a la URL correspondiente según el grupo del usuario.
        """
        for group_id, redirect_url in self.group_redirects.items():
            if user.groups.filter(id=group_id).exists():  # Verifica si el usuario pertenece al grupo
                return redirect(redirect_url)
        return redirect(self.success_url)  # Redirige a la URL de éxito por defecto


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
