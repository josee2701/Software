import asyncio
import json
from datetime import date, timedelta

from django import forms
from django.contrib.auth.mixins import (LoginRequiredMixin,
                                        PermissionRequiredMixin)
from django.core.paginator import Paginator
from django.db import connection
from django.db.models import Q
from django.forms.models import model_to_dict
from django.http import (Http404, HttpResponse, HttpResponseRedirect,
                         JsonResponse)
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views import View, generic
from django.views.decorators import cache, csrf
from django.views.decorators.csrf import csrf_protect
from django.views.generic import ListView
from django.views.generic.detail import SingleObjectMixin
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.events.models import Event, EventFeature
from apps.log.mixins import (CreateAuditLogAsyncMixin,
                             DeleteAuditLogAsyncMixin,
                             UpdateAuditLogAsyncMixin, obtener_ip_publica)
from apps.log.utils import log_action
from apps.realtime.apis import extract_number, get_user_companies, sort_key
from apps.realtime.models import AVLData, Device, Vehicle
from apps.realtime.serializer import AVLDataSerializer
from apps.realtime.sql import fetch_all_dataplan
from apps.whitelabel.models import Company
from config.pagination import get_paginate_by

from .forms import (CompanyScoreForm, DataSemConfigurationForm,
                    DriverAnalyticForm, DriverForm, ItemScoreFormsets,
                    ReportDriverForm, ReportTodayForm)
from .models import (Advanced_Analytical, CompanyScoreSetup, Driver,
                     DriverAnalytic, FatigueControl, ItemScore, ItemScoreSetup)
from .postgres import GeocodingService, connect_db
from .sql import (fetch_all_confidatasem, get_drivers_list,
                  getCompanyScoresByCompanyAndUser)


class ListDriverTemplate(PermissionRequiredMixin, LoginRequiredMixin, ListView):
    """
    Vista como clase que renderiza el template HTML que contiene la lista de conductores
    creados por una empresa (distribuidor).
    """

    model = Driver
    template_name = "checkpoints/driver/main_drivers.html"
    permission_required = "checkpoints.view_driver"

    def get_paginate_by(self, queryset):
        """
        Obtiene el número de elementos a mostrar por página.

        Args:
            queryset (QuerySet): El conjunto de datos de la consulta.

        Returns:
            int: El número de elementos a mostrar por página.
        """
        paginate_by = self.request.POST.get('paginate_by', None)  # Obtener paginate_by de los parámetros GET

        if paginate_by is None:
            session_filters = self.request.session.get(
                f"filters_sorted_driver_{self.request.user.id}", {}
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
        Obtiene el conjunto de datos de los planes de datos reales de la compañía asociada al
        usuario que realiza la solicitud.

        Returns:
            List[dict]: Lista de planes de datos ordenada por 'Company' en forma descendente.
        """
        user = self.request.user
        company = user.company
        params = self.request.GET if self.request.method == 'GET' else self.request.POST
        query = params.get("query", "").lower()
        search = params.get("q", query).lower()
        # Parámetros de ordenamiento por defecto
        if 'order_by' not in params and 'paginate_by' not in params and 'page' not in params:
            # Limpiar los filtros de la sesión
            if f"filters_sorted_driver_{user.id}" in self.request.session:
                del self.request.session[f"filters_sorted_driver_{user.id}"]
                self.request.session.modified = True
        # Recuperar filtros almacenados en la sesión
        session_filters = self.request.session.get(f'filters_sorted_driver_{user.id}', {})
        order_by = params.get('order_by', session_filters.get('order_by', ['company'])[0])
        direction = params.get('direction', session_filters.get('direction',['asc'])[0])
        # Actualizar los filtros con los parámetros actuales de la solicitud GET
        session_filters.update(params)
        # Actualizar los filtros de la sesión con los nuevos parámetros
        self.request.session[f'filters_sorted_driver_{user.id}'] = session_filters
        self.request.session.modified = True
        # Obtener los planes de datos a través de la función fetch_all_dataplan.
        queryset = get_drivers_list(company.id, user.id, search)

        # Función para convertir los valores a minúsculas y extraer números cuando sea necesario
        key_function = sort_key(order_by)
        reverse = direction == 'desc'
        try:
            sorted_queryset = sorted(queryset, key=key_function, reverse=reverse)
        except KeyError:
            # Ordenamiento por defecto si la clave no existe
            sorted_queryset = sorted(
                queryset, key=lambda x: x["company"].lower(), reverse=reverse
            )

        return sorted_queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({"pk": self.request.user.company_id})
        paginate_by = self.get_paginate_by(None)
        context["paginate_by"] = paginate_by
        # Simplificación directa para calcular start_number
        page_number = context.get("page_obj").number if context.get("page_obj") else 1
        context["start_number"] = (page_number - 1) * self.get_paginate_by(None)
        session_filters = self.request.session.get(f'filters_sorted_driver_{self.request.user.id}', {})
        # Obtener el ordenamiento desde la solicitud actual
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


class AddDriverView(
    PermissionRequiredMixin,
    LoginRequiredMixin,
    CreateAuditLogAsyncMixin,
    generic.CreateView,
):
    """
    Vista como clase que implementa la opción de crear conductores para las empresas
    distribuidoras y asignarlas a un cliente final.
    Permite añadir una configuración personalizada para los campos  'Personal ID', 'first_name',
    'last_name', 'address','date_joined', 'is_active', 'password'.
    """

    template_name = "checkpoints/driver/add_driver.html"
    permission_required = "checkpoints.add_driver"
    form_class = DriverForm

    def get_success_url(self):
        """
        Devuelve la URL a la que se redirige después de una eliminación exitosa.
        """
        return reverse("checkpoints:list_drivers")

    def clean_date_joined(self):
        date_joined = self.cleaned_data.get("date_joined")
        try:
            if date_joined < date.today():
                raise Exception
        except Exception:
            raise forms.ValidationError(_("Date joined can't be before of today"))
        return date_joined

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        companies = get_user_companies(user)
        if user.company_id == 1:
            context["form"].fields["company"].choices = companies
        else:
            context["form"].fields["company"].queryset = companies
        button_color = self.request.user.company.theme_set.all().first().button_color
        context["button_color"] = button_color
        return context

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.modified_by = self.request.user
        # Llama al método form_valid de la clase padre para registrar la acción en el log de auditoría
        response = super().form_valid(form)
        form.save()

        # Prepara una respuesta con redirección usando HTMX
        page_update = HttpResponse("")
        page_update["HX-Redirect"] = self.get_success_url()
        return page_update


class UpdateDriverView(
    PermissionRequiredMixin,
    LoginRequiredMixin,
    UpdateAuditLogAsyncMixin,
    generic.UpdateView,
):
    """
    Vista como clase que implementa la opción de editar la configuración personalizada
    de conductores para las empresas distribuidoras.
    """

    model = Driver
    template_name = "checkpoints/driver/update_driver.html"
    permission_required = "checkpoints.change_driver"
    form_class = DriverForm
    success_url = "/checkpoints/drivers"

    def get_success_url(self):
        """
        Devuelve la URL a la que se redirige después de una eliminación exitosa.
        """
        return reverse("checkpoints:list_drivers")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        companies = get_user_companies(user)
        if user.company_id == 1:
            context["form"].fields["company"].choices = companies
        else:
            context["form"].fields["company"].queryset = companies

        button_color = self.request.user.company.theme_set.all().first().button_color
        context["button_color"] = button_color
        return context

    def form_valid(self, form):
        form.instance.modified_by = self.request.user
        # Llama al método form_valid de la clase padre para registrar la acción en el log de auditoría
        response = super().form_valid(form)
        form.save()

        # Prepara una respuesta con redirección usando HTMX
        page_update = HttpResponse("")
        page_update["HX-Redirect"] = self.get_success_url()
        return page_update


class DeleteDriverView(
    PermissionRequiredMixin,
    LoginRequiredMixin,
    DeleteAuditLogAsyncMixin,
    generic.UpdateView,
):
    """
    Este código define una vista de Django que implementa la eliminación de una instancia del
    modelo "Driver". En lugar de eliminar el objeto, se establece el valor de la propiedad
    "visible" en False, lo que oculta la información del objeto. El usuario debe estar autenticado
    y tener los permisos necesarios para acceder a esta vista. La vista utiliza un formulario con
    un campo "visible" y, una vez validado, redirige a la lista de objetos "Driver" creados.
    """

    model = Driver
    template_name = "checkpoints/driver/delete_driver.html"
    permission_required = "checkpoints.delete_driver"
    success_url = reverse_lazy("checkpoints:list_driver_created")
    fields = ["visible"]

    def get_success_url(self):
        """
        Devuelve la URL a la que se redirige después de una eliminación exitosa.
        """
        return reverse("checkpoints:list_drivers")

    def form_valid(self, form):
        driver = form.save(commit=False)
        driver.modified_by = self.request.user
        driver.visible = False
        # Llama al método form_valid de la clase padre para registrar la acción en el log de auditoría
        response = super().form_valid(form)
        driver.save()

        # Prepara una respuesta con redirección usando HTMX
        page_update = HttpResponse("")
        page_update["HX-Redirect"] = self.get_success_url()
        return page_update


class BottonView(LoginRequiredMixin, generic.TemplateView):
    """
    Vista intermedia que redirecciona la solicitud enviada a través del botón que asigna
    un vehículo a un conductor teniendo en cuenta si el conductor tiene o no un vehículo
    ya asignado.
    """

    template_name = "checkpoints/driver_analytic/button_view.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({"pk": kwargs.get("pk")})
        return context

    @method_decorator(csrf.csrf_protect)
    @method_decorator(cache.never_cache)
    def dispatch(self, request, *args, **kwargs):
        """
        Esta función se encarga de redireccionar al usuario a la primera asignación de un
        vehículo para un conductor o permite añadir más vehículos según sea el caso.
        """
        get_object_or_404(Driver, id=kwargs.get("pk"))
        try:
            query_analytic = list(
                DriverAnalytic.objects.filter(driver_id=kwargs.get("pk"))
            )
            if len(query_analytic) == 0:
                return HttpResponseRedirect(
                    reverse("checkpoints:assign_driver", args=(kwargs.get("pk"),))
                )
            else:
                return HttpResponseRedirect(
                    reverse("checkpoints:update_assign", args=(kwargs.get("pk"),))
                )
        except Exception as e:
            print(f"Error: {e}")
            return HttpResponseRedirect(reverse_lazy("checkpoints:list_drivers"))


class AddAssignDriverView(
    LoginRequiredMixin, CreateAuditLogAsyncMixin, generic.CreateView
):
    """
    Vista como clase que permite a los usuarios (distribuidores) asignar un vehículo a un conductor
    por primera vez.
    """

    model = DriverAnalytic
    form_class = DriverAnalyticForm
    template_name = "checkpoints/driver_analytic/assign_driver.html"

    def get_success_url(self):
        # Asegúrate de que el nombre de la URL sea correcto y esté definido en tus archivos de URL.
        return reverse("checkpoints:list_drivers")

    def get_context_data(self, **kwargs):
        """
        Esta función consulta los vehículos ya asignados al conductor y los retorna,
        para ser mostrados en el template.
        """
        context = super().get_context_data(**kwargs)
        driver = Driver.objects.get(id=self.kwargs.get("pk"))
        driver_company = driver.company_id
        #  Filtrar los dispositivos que ya están asignados a un vehículo
        assigned_vehicle = Vehicle.objects.filter(
            company_id=driver_company,
            visible=True,
            is_active=True,
            # driveranalytic__isnull=True,
        )
        context["form"].fields["vehicle"].queryset = assigned_vehicle
        context.update({"Driver": driver, "pk": self.kwargs.get("pk")})
        button_color = self.request.user.company.theme_set.all().first().button_color
        context["button_color"] = button_color
        return context

    def form_valid(self, DriverAnalitycForm):
        print(self.request.POST)
        DriverAnalitycForm.instance.driver_id = self.kwargs.get("pk")
        DriverAnalitycForm.instance.created_by = self.request.user
        DriverAnalitycForm.instance.modified_by = self.request.user
        DriverAnalitycForm.save()
        # Llama al método form_valid de la clase padre para registrar la acción en el log de auditoría
        response = super().form_valid(DriverAnalitycForm)
        # Prepara una respuesta con redirección usando HTMX
        page_update = HttpResponse("")
        page_update["HX-Redirect"] = self.get_success_url()
        return page_update


class UpdateAssignDriverView(
    LoginRequiredMixin, CreateAuditLogAsyncMixin, generic.CreateView
):
    """
    Vista como clase que permite a los usuarios (distribuidores) añadir más vehículos a un
    conductor que ya cuenta con un vehículo asignado.
    """

    model = DriverAnalytic
    form_class = DriverAnalyticForm
    template_name = "checkpoints/driver_analytic/update_assign.html"

    def get_success_url(self):
        # Asegúrate de que el nombre de la URL sea correcto y esté definido en tus archivos de URL.
        return reverse("checkpoints:list_drivers")

    def get_context_data(self, **kwargs):
        """
        Esta función consulta los vehículos ya asignados al conductor y los retorna,
        para ser mostrados en el template.
        """
        context = super().get_context_data(**kwargs)
        driver_assign = DriverAnalytic.objects.filter(
            driver_id=self.kwargs.get("pk")
        ).order_by("-date_leaving")
        driver = Driver.objects.get(id=self.kwargs.get("pk"))
        driver_company = driver.company_id
        #  Filtrar los dispositivos que ya están asignados a un vehículo
        assigned_vehicle = Vehicle.objects.filter(
            company_id=driver_company, visible=True, driveranalytic__isnull=True
        )
        context["form"].fields["vehicle"].queryset = assigned_vehicle
        context.update(
            {
                "assign_drivers": driver_assign,
                "Driver": driver,
                "pk": self.kwargs.get("pk"),
            }
        )
        button_color = self.request.user.company.theme_set.all().first().button_color
        context["button_color"] = button_color
        return context

    def form_valid(self, form):
        """
        Verifica las validaciones creadas para el formulario.
        """
        form.instance.driver_id = self.kwargs.get("pk")
        form.instance.modified_by = self.request.user
        form.clean_date_joined()
        form.clean_date_leaving()

        actual_date_joined = form.instance.date_joined
        query_past_date_leaving = DriverAnalytic.objects.filter(
            driver=self.kwargs.get("pk")
        ).order_by("-date_leaving")[:1]
        for date_np in query_past_date_leaving:
            past_date_leaving = date_np.date_leaving
        if actual_date_joined < past_date_leaving:
            msg = _(
                """You already have this driver assigned in this time slot!!
            Please select a future time slot
            """
            )
            form.add_error("date_joined", msg)
            return self.form_invalid(form)
        form.save()
        # Llama al método form_valid de la clase padre para registrar la acción en el log de auditoría
        response = super().form_valid(form)
        # Prepara una respuesta con redirección usando HTMX
        page_update = HttpResponse("")
        page_update["HX-Redirect"] = self.get_success_url()
        return page_update

    def form_invalid(self, form):
        """
        Eleva la condición de error para la que fue llamada en la función
        form_valid, renderizando el mensaje de error así como el formulario.
        """
        return self.render_to_response(self.get_context_data(form=form))


class UpdateVehicleAssignView(
    LoginRequiredMixin, UpdateAuditLogAsyncMixin, generic.UpdateView
):
    model = DriverAnalytic
    form_class = DriverAnalyticForm
    template_name = "checkpoints/driver_analytic/update_vehicle_assign.html"

    def get_context_data(self, **kwargs):
        """
        Esta función consulta los vehículos ya asignados al conductor y los retorna,
        para ser mostrados en el template.
        """
        context = super().get_context_data(**kwargs)
        Company = self.request.user.company
        #  Filtrar los dispositivos que ya están asignados a un vehículo
        assigned_vehicle = Vehicle.objects.filter(
            company_id=Company,
            visible=True,
            is_active=True,
            # driveranalytic__isnull=True,
        )
        context["form"].fields["vehicle"].queryset = assigned_vehicle
        button_color = self.request.user.company.theme_set.all().first().button_color
        context["button_color"] = button_color
        return context

    def form_valid(self, form):
        """
        Verifica las validaciones creadas para el formulario.
        """
        form.instance.modified_by = self.request.user
        response = super().form_valid(form)
        # Aquí deberías actualizar el objeto existente en lugar de crear uno nuevo
        return super().form_valid(form)

    def get_success_url(self):
        driver_analytic = (
            self.object
        )  # Usar self.object en lugar de consultar la base de datos nuevamente
        driver = driver_analytic.driver
        return reverse("checkpoints:update_assign", args=(driver.id,))


class ListScoreCompanyTemplate(PermissionRequiredMixin, LoginRequiredMixin, ListView):
    """
    Vista como clase que renderiza el template HTML que contiene la lista de
    empresas (clientes finales) a las que tiene acceso un distribuidor
    para configurar su calificación de conductores.
    """

    model = CompanyScoreSetup
    template_name = "checkpoints/score_configuration/main_score_configuration.html"
    permission_required = "checkpoints.view_companyscoresetup"
    context_object_name = "list_score_configuration"

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
                f"filters_sorted_scoredriver_{self.request.user.id}", {}
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
        Obtiene el conjunto de datos de los planes de datos reales de la compañía asociada al
        usuario que realiza la solicitud.

        Returns:
            QuerySet: Conjunto de datos de CompanyScoreSetup relacionados con las empresas del usuario.
        """
        companies = Company.objects.filter(
            Q(pk=self.request.user.company_id)
            | Q(provider=self.request.user.company_id),
            visible=True,
            actived=True,
        )

        for user_company in companies:
            try:
                # Intentamos obtener el CompanyScoreSetup para cada empresa
                CompanyScoreSetup.objects.get(company=user_company)
            except CompanyScoreSetup.DoesNotExist:
                # Si no existe un CompanyScoreSetup, lo creamos para la empresa
                CompanyScoreSetup.objects.create(
                    company=user_company,
                    created_by=self.request.user,
                    modified_by=self.request.user,
                )
        user = self.request.user
        params = self.request.GET if self.request.method == 'GET' else self.request.POST
        query = params.get("query", "").lower()
        search = params.get("q", query).lower()
        if 'order_by' not in params and 'paginate_by' not in params and 'page' not in params:
            # Limpiar los filtros de la sesión
            if f"filters_sorted_scoredriver_{user.id}" in self.request.session:
                del self.request.session[f"filters_sorted_scoredriver_{user.id}"]
                self.request.session.modified = True
        session_filters = self.request.session.get(f'filters_sorted_scoredriver_{user.id}', {})
        order_by = params.get('order_by', session_filters.get('order_by', ['company'])[0])
        direction = params.get('direction', session_filters.get('direction',['asc'])[0])
        # Actualizar los filtros con los parámetros actuales de la solicitud GET
        session_filters.update(params)
        # Actualizar los filtros de la sesión con los nuevos parámetros
        self.request.session[f'filters_sorted_scoredriver_{user.id}'] = session_filters
        self.request.session.modified = True
        # Obtener los planes de datos a través de la función fetch_all_dataplan.
        queryset = getCompanyScoresByCompanyAndUser(self.request.user.company_id, self.request.user.id, search)
        # Función para convertir los valores a minúsculas y extraer números cuando sea necesario
        key_function = sort_key(order_by)
        # Determinar si es orden descendente
        reverse = direction == 'desc'
        try:
            sorted_queryset = sorted(queryset, key=key_function, reverse=reverse)
        except KeyError:
            # Ordenamiento por defecto si la clave no existe
            sorted_queryset = sorted(queryset, key=lambda x: x['company'].lower(), reverse=reverse)
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
        session_filters = self.request.session.get(f'filters_sorted_scoredriver_{self.request.user.id}', {})
        # Obtener el ordenamiento desde la solicitud actual
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


class ScoreConfigurationView(
    PermissionRequiredMixin,
    LoginRequiredMixin,
    SingleObjectMixin,
    UpdateAuditLogAsyncMixin,
    generic.FormView,
):
    model = CompanyScoreSetup
    template_name = "checkpoints/score_configuration/update_score_configuration.html"
    permission_required = "checkpoints.add_companyscoresetup"

    # Esta función devuelve la URL a la que se redirigirá al usuario después de guardar con éxito.
    def get_success_url(self):
        return reverse("checkpoints:list_score_configuration")

    # Esta función obtiene todos los elementos ItemScore de la base de datos y los devuelve como
    # una lista.
    def get_queryset(self):
        return list(ItemScore.objects.all())

    # Esta función empareja cada item con su formulario correspondiente y los devuelve como una
    # lista de tuplas.
    def get_score_forms(self, items, score_form):
        return zip(items, score_form)

    # Esta función obtiene el objeto CompanyScoreSetup correspondiente y asegura que todos los
    # ItemScores estén configurados.
    def get_object(self):
        company_id = self.kwargs.get("pk")
        company_score_setup = get_object_or_404(
            CompanyScoreSetup, company_id=company_id
        )
        self.ensure_items_setup(company_score_setup)
        return company_score_setup

    # Esta función asegura que todos los elementos de ItemScore estén configurados en ItemScoreSetup para una compañía específica.
    def ensure_items_setup(self, company_score_setup):
        query_items = ItemScore.objects.all()
        existing_items = ItemScoreSetup.objects.filter(
            company_score_id=company_score_setup.pk
        )
        existing_item_ids = {item.item_id for item in existing_items}

        # Encuentra los elementos que faltan y los crea.
        missing_items = [
            item for item in query_items if item.pk not in existing_item_ids
        ]

        if missing_items:
            ItemScoreSetup.objects.bulk_create(
                [
                    ItemScoreSetup(
                        company_score_id=company_score_setup.pk,
                        item_id=item.pk,
                        created_by=self.request.user,
                        modified_by=self.request.user,
                    )
                    for item in missing_items
                ]
            )

    # Esta función maneja la solicitud GET. Carga los formularios necesarios y los datos del contexto para la plantilla.
    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = CompanyScoreForm(instance=self.object)
        score_form = ItemScoreFormsets(instance=self.object)
        items = self.get_queryset()
        forms = self.get_score_forms(items, score_form)
        company = Company.objects.get(id=self.object.company_id)
        return self.render_to_response(
            self.get_context_data(
                form=form,
                forms=forms,
                formset=score_form,
                company=company,
            )
        )

    # Esta función obtiene los datos del contexto para la plantilla.
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

    # Esta función maneja la solicitud POST. Captura el estado anterior, valida y guarda los formularios.
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = CompanyScoreForm(request.POST, instance=self.object)
        score_formset = ItemScoreFormsets(request.POST, instance=self.object)

        # Captura el estado antes de la actualización.
        self.capture_state_before(form, score_formset)

        if form.is_valid() and score_formset.is_valid():
            return self.form_valid(form, score_formset)
        else:
            return self.form_invalid(form, score_formset)

    # Esta función captura el estado del objeto y los formsets antes de guardarlos.
    def capture_state_before(self, form, score_formset):
        self.obj_before = model_to_dict(form.instance)
        self.formsets_before = [
            model_to_dict(obj) for obj in form.instance.itemscoresetup_set.all()
        ]

    # Esta función guarda el formulario principal y los formsets. Luego, captura el estado después de guardar.
    def form_valid(self, form, score_formset):
        self.save_form_and_formsets(form, score_formset)
        self.capture_state_after(form, score_formset)
        self.log_action()
        return self.redirect_with_htmx()

    # Esta función guarda el formulario principal y los formsets.
    def save_form_and_formsets(self, form, score_formset):
        company_score_setup = form.save(commit=False)
        company_score_setup.modified_by = self.request.user
        if not company_score_setup.created_by_id:
            company_score_setup.created_by = self.request.user
        company_score_setup.save()

        instances = score_formset.save(commit=False)
        for instance in instances:
            instance.modified_by = self.request.user
            if not instance.created_by_id:
                instance.created_by = self.request.user
            instance.save()
        score_formset.save_m2m()

    # Esta función captura el estado del objeto y los formsets después de guardarlos.
    def capture_state_after(self, form, score_formset):
        self.obj_after = model_to_dict(form.instance)
        self.formsets_after = [
            model_to_dict(obj) for obj in score_formset.save(commit=False)
        ]

    # Esta función redirige usando HTMX.
    def redirect_with_htmx(self):
        page_update = HttpResponse("")
        page_update["HX-Redirect"] = self.get_success_url()
        return page_update

    # Esta función maneja el caso en que el formulario no es válido. Recarga los formularios y los datos del contexto.
    def form_invalid(self, form, score_form):
        self.object = self.get_object()
        items = self.get_queryset()
        forms = self.get_score_forms(items, score_form)
        company = Company.objects.get(id=self.object.company_id)
        return self.render_to_response(
            self.get_context_data(
                form=form,
                forms=forms,
                formset=score_form,
                company=company,
            )
        )

    # Esta función registra la acción en el log de auditoría.
    def log_action(self):
        user = self.request.user
        company_id = getattr(user, "company_id", None)
        view_name = self.__class__.__name__

        before = self.obj_before if self.obj_before else {}
        after = self.obj_after if self.obj_after else {}

        before_formsets = self.formsets_before if self.formsets_before else []
        after_formsets = self.formsets_after if self.formsets_after else []

        before_json = json.dumps(
            {"form": before, "formsets": before_formsets}, default=str
        )
        after_json = json.dumps(
            {"form": after, "formsets": after_formsets}, default=str
        )

        ip_address = asyncio.run(obtener_ip_publica(self.request))

        log_action(
            user=user,
            company_id=company_id,
            view_name=view_name,
            action=self.action,
            before=before_json,
            after=after_json,
            ip_address=ip_address,
        )


class ReporDriverView(View, LoginRequiredMixin):

    """
    Se realiza vista en la cual el usuario podra seleccionar la compañia y el conductor o conductores
    a evaluar en un rango de fecha con el cual validara y brindara una tabla con la información
    de la punuación por cada item
    """

    template_name = "checkpoints/reportes/report_driver.html"
    login_url = "login"

    # Método de utilidad para obtener empresas y conductores disponibles
    def get_companies_and_drivers(self):
        if self.request.user.is_authenticated:
            # Obtén el ID de la empresa del usuario
            company_id = self.request.user.company_id
            # Filtra las empresas disponibles para el usuario
            companies = Company.objects.filter(
                Q(id=company_id) | Q(provider_id=company_id), visible=True, actived=True
            )
            # Filtra los conductores disponibles para el usuario
            drivers = Driver.objects.filter(
                company_id=company_id, visible=True, is_active=True
            ).order_by("company")
            return companies, drivers
        else:
            # En lugar de return redirect('login'), puedes generar una redirección HTTP
            raise Http404("User not authenticated")

    def get(self, request):
        form = ReportDriverForm()
        try:
            companies, driver = self.get_companies_and_drivers()
            form.fields["company"].queryset = companies
            form.fields["driver"].queryset = driver
            return render(request, self.template_name, {"form": form})
        except Http404:
            return redirect("login")

    @classmethod
    def find_driver_and_vehicle(cls):
        """
        Encuentra las asignaciones de conductores y vehículos y devuelve una lista de
        tuplas que contiene el nombre completo del conductor y la licencia del vehículo
        correspondiente.

        Returns:
            driver_vehicle (list of tuple): Una lista de tuplas donde cada tupla contiene el
            nombre completo del conductor y la licencia del vehículo.
            drivers_all (QuerySet): Una consulta que representa todos los conductores en la
            base de datos.
            asignation_driver (QuerySet): Una consulta que representa todas las asignaciones
            de conductores y vehículos en la base de datos.

        Example:
            driver_vehicle, drivers_all, asignation_driver = find_driver_and_vehicle()
        """
        asignation_driver = DriverAnalytic.objects.all()
        drivers_all = Driver.objects.all()
        driver_vehicle = []

        for driver in drivers_all:
            for asig_driver in asignation_driver:
                if driver.id == asig_driver.driver.id:
                    driver_vehicle.append(
                        (
                            driver.first_name + " " + driver.last_name,
                            asig_driver.vehicle.license,
                        )
                    )

        return driver_vehicle, drivers_all, asignation_driver

    def post(self, request):
        form = ReportDriverForm(request.POST)
        total_point = 100
        total_time_on = timedelta()
        try:
            companies, driver = self.get_companies_and_drivers()
            (
                driver_vehicle,
                drivers_all,
                asignation_driver,
            ) = ReporDriverView.find_driver_and_vehicle()

            form.fields["company"].queryset = companies
            form.fields["driver"].queryset = driver
            if form.is_valid():
                company = form.cleaned_data["company"]
                drivers = form.cleaned_data["driver"]
                start_date = form.cleaned_data["start_date"]
                end_date = form.cleaned_data["end_date"]
                # Realizar las operaciones necesarias para generar los resultados del informe
                controls = AVLData.objects.all()
                lest_item = ItemScoreSetup.objects.all()
                events = Event.objects.all()

                # Filtrar por empresa
                if company:
                    controls = controls.filter(device_id__company=company)
                    lest_item = lest_item.filter(company_score__company=company)

                if start_date and end_date:
                    controls = controls.filter(
                        server_date__range=(start_date, end_date)
                    ).order_by("-server_date")
                if drivers:
                    controls = controls.filter(
                        device_id__vehicle__driveranalytic__driver_id__in=drivers
                    )

                for control in controls:
                    control.total_point = total_point
                    control_date = control.server_date.date()
                    if control_date == control_date:
                        for verif in asignation_driver:
                            for driver_info in driver_vehicle:
                                driver_name, vehicle = driver_info
                                if (
                                    verif.driver.first_name
                                    + " "
                                    + verif.driver.last_name
                                    == driver_name
                                ):
                                    if verif.vehicle.device_id == control.device_id:
                                        control.driver = driver_name
                                        control.vehicle = vehicle
                                        print("hola")

                        # print(vehicle)
                        # if vehicle.divice_id==control.device_id:
                        #     print(driver)
                        # if driver.vehicle.device_id == control.device_id:
                        #     print(control)
                        #     print(control.server_date)
                # for control in controls:
                #     for driver in drivers:
                #         if driver.driver.id == control.device.
                # for control in controls:
                #     control.total_point = total_point
                #     if control.server_date == control.server_date:
                #         # Filtrar por conductores
                #         for driver in asignation_driver:
                #             if driver.vehicle.device_id == control.device_id:
                #                 control.vehicle = driver.vehicle
                #                 if drivers or not drivers:
                #                     control.driver = f"{driver.driver.first_name} {driver.driver.last_name}"
                #                 for event in events:
                #                     if control.main_event == event.number:
                #                         if control.main_event == 8:
                #                             vehicle_on = control.server_date
                #                         # if control.main_event == 9:
                #                         #     vehicle_off = control.server_date
                #                         # if vehicle_on:
                #                         #     # Calcula la diferencia de tiempo y agrega a total_time_on
                #                         #     time_difference = vehicle_off - vehicle_on
                #                         #     total_time_on += time_difference
                #                         #     total_time_on = (
                #                         #         total_time_on.total_seconds() / 3600
                #                         #     )
                #                         #     control.total_hours = total_time_on
                #                         # if control.main_event == 85:
                #                         #     print()

                context = {
                    "form": form,
                    "lest_item": lest_item,
                    "controls": controls,
                    # Puedes agregar más datos aquí según sea necesario
                }

                # Imprimir para depuración
                print("Company:", company)
                print("Drivers:", drivers)
                print("Start Date:", start_date)
                print("End Date:", end_date)
                print(
                    "Controls Count:", controls.count()
                )  # Verifica la cantidad de controles filtrados

                # Renderizar el mismo template con el contexto actualizado
            return render(request, self.template_name, context)
        except Http404:
            return redirect("login")


def vehicles_by_company(request, company_id):
    # Asume que tienes un modelo Vehicle que está relacionado con Company
    vehicles = Vehicle.objects.filter(company_id=company_id, visible=True).values(
        "id", "license"
    )

    return JsonResponse(list(vehicles), safe=False)


def events_by_company(request, company_id):
    # Obtener todos los números de eventos
    event_numbers = Event.objects.values_list("number", flat=True)

    # Diccionario para mapear números de evento a sus características
    event_features_map = {}

    # Iterar sobre cada número de evento
    for number in event_numbers:
        # Filtrar las características de evento correspondientes a ese número de evento y empresa
        event_features = EventFeature.objects.filter(
            company=company_id, event__number=number, visible=True
        )
        event_features_map[number] = list(event_features)

    # Lista para almacenar los eventos actualizados
    updated_events = []

    # Iterar sobre todos los eventos
    for event in Event.objects.all():
        # Verificar si hay características asociadas a este evento
        event_features = event_features_map.get(event.number)
        if event_features:
            # Concatenar los nombres de las características de evento
            event_name = " | ".join(
                [event_feature.alias for event_feature in event_features]
            )
            # Actualizar el nombre del evento
            event.name = event_name
        # Agregar el evento actualizado a la lista
        updated_events.append(event)
        event_choices = [
            (f"{event.pk} - {event.number} Event: {event.name}")
            for event in updated_events
        ]
    return JsonResponse(list(event_choices), safe=False)


class ReportTodayView(PermissionRequiredMixin, View, LoginRequiredMixin):
    """
    Vista que muestra un informe de datos.

    Esta vista se encarga de procesar las solicitudes GET y POST para generar un informe de datos
    para el reporte. Utiliza un formulario para recopilar los parámetros de búsqueda, como la
    compañía, el IMEI del dispositivo y el rango de fechas. Luego ejecuta un procedimiento almacenado
    en la base de datos para obtener los datos correspondientes y los muestra en una plantilla.

    La vista también se encarga de la paginación de los resultados y de ajustar las fechas y la
    ubicación de los datos obtenidos.

    Requiere los permisos "checkpoints.view_report" y redirige al formulario de inicio de sesión
    si el usuario no está autenticado.
    """

    template_name = "checkpoints/reportes/report_today.html"
    permission_required = "checkpoints.view_report"
    login_url = "login"

    def execute_stored_procedure(
        self, company_id, imei, fecha_inicial, fecha_final, paginate_by, page
    ):
        print("enrtra al bd")
        """
        Ejecuta un procedimiento almacenado y devuelve los resultados en formato JSON.

        Args:
            company_id (int): ID de la compañía.
            imei (str): IMEI del dispositivo.
            fecha_inicial (str): Fecha inicial en formato YYYY-MM-DD.
            fecha_final (str): Fecha final en formato YYYY-MM-DD.
            paginate_by (int): Número de elementos por página.
            page (int): Número de página.

        Returns:
            list: Resultados del procedimiento almacenado en formato JSON.
        """
        with connection.cursor() as cursor:
            cursor.execute(
                "EXEC [dbo].[ReportAvlData] @Company_ID=%s, @IMEI=%s, @dFIni=%s, @dFFin=%s, @PageSize=%s, @PageNumber=%s",
                [company_id, imei, fecha_inicial, fecha_final, paginate_by, page],
            )
            rows = cursor.fetchall()
            json_result = "".join(row[0] for row in rows) if rows else "[]"
        return json.loads(json_result)

    def get_paginated_data(self, json_data, paginate_by, page):
        """
        Obtiene los datos paginados a partir de los datos JSON proporcionados.

        Args:
            json_data (list): Los datos en formato JSON.
            paginate_by (int): El número de elementos por página.
            page (int): El número de página actual.

        Returns:
            tuple: Una tupla que contiene los siguientes elementos:
                - page_obj (Page): El objeto de página que contiene los datos paginados.
                - current_start_item (int): El índice del primer elemento en la página actual.
                - current_end_item (int): El índice del último elemento en la página actual.
                - total_records (int): El número total de registros en los datos JSON.
        """
        total_records = int(json_data[0].get("TotalRecords", 0)) if json_data else 0
        paginator = Paginator(range(total_records), paginate_by)
        page_obj = paginator.get_page(page)
        current_start_item = (page - 1) * paginate_by + 1
        current_end_item = min(page * paginate_by, total_records)
        return page_obj, current_start_item, current_end_item, total_records

    def update_dates_and_location(self, json_data, timezone_offset):
        """
        Actualiza las fechas y realiza la geolocalizacion inversa en los datos JSON proporcionados.

        Args:
            json_data (list): Una lista de diccionarios que contienen los datos JSON.
            timezone_offset (int): El desplazamiento de la zona horaria en minutos.

        Returns:
            list: Una lista de diccionarios actualizados con las fechas y la ubicación ajustadas.
        """
        geocoding_service = GeocodingService()
        geocoding_service.connect()

        try:
            for item in json_data:
                for key in ["server_date", "signal_date"]:
                    if key in item:
                        item[key] = geocoding_service.adjust_dates(
                            item[key], timezone_offset
                        )

                latitude = str(item.get("latitude"))
                longitude = str(item.get("longitude"))
                if latitude and longitude:
                    location = geocoding_service.rev_geocode(latitude, longitude)
                    if location:
                        item["location"] = location
        finally:
            geocoding_service.close()
        return json_data

    def get(self, request, *args, **kwargs):
        """
        Método que maneja la solicitud GET para la vista.

        Parámetros:
        - request: La solicitud HTTP recibida.
        - args: Argumentos posicionales adicionales.
        - kwargs: Argumentos de palabras clave adicionales.

        Retorna:
        - Una respuesta HTTP con el formulario y los datos necesarios para renderizar la plantilla.
        """
        form = ReportTodayForm()
        user = self.request.user
        companies = get_user_companies(user)
        if user.company_id == 1:
            form.fields["Company_id"].choices = companies
        else:
            form.fields["Company_id"].queryset = companies
        button_color = request.user.company.theme_set.all().first().button_color
        return render(
            request, self.template_name, {"form": form, "button_color": button_color}
        )

    def post(self, request, *args, **kwargs):
        """
        Procesa una solicitud POST y devuelve una respuesta HTTP.

        Parámetros:
        - request: La solicitud HTTP recibida.
        - args: Argumentos adicionales pasados a la función.
        - kwargs: Argumentos de palabras clave adicionales pasados a la función.

        Retorna:
        - Una respuesta HTTP que renderiza una plantilla con los datos procesados o los errores del
        formulario.
        """
        form = ReportTodayForm(request.POST, user=request.user)
        user = self.request.user
        companies = get_user_companies(user)
        if user.company_id == 1:
            form.fields["Company_id"].choices = companies
        else:
            form.fields["Company_id"].queryset = companies
        form.fields["Imei"].queryset = Device.objects.filter(
            company_id=request.POST.get("Company_id")
        )

        if form.is_valid():
            page_str = request.POST.get("page", "1").strip()
            page = int(page_str) if page_str.isdigit() else 1

            paginate_by_str = request.POST.get("paginate_by", "").strip()
            paginate_by = (
                int(paginate_by_str)
                if paginate_by_str.isdigit()
                else request.session.get("paginate_by", 15)
            )
            request.session["paginate_by"] = paginate_by

            company_id = form.cleaned_data["Company_id"].id
            imei = form.cleaned_data["Imei"].imei
            timezone_offset = int(request.POST.get("timezone_offset", 0))
            print(imei)
            fecha_inicial = form.cleaned_data["FechaInicial"] + timedelta(
                minutes=timezone_offset
            )
            fecha_final = form.cleaned_data["FechaFinal"] + timedelta(
                minutes=timezone_offset
            )

            fecha_inicial_str = fecha_inicial.strftime("%Y-%m-%d %H:%M:%S")
            fecha_final_str = fecha_final.strftime("%Y-%m-%d %H:%M:%S")

            json_data = self.execute_stored_procedure(
                company_id, imei, fecha_inicial_str, fecha_final_str, paginate_by, page
            )
            json_data = self.update_dates_and_location(json_data, timezone_offset)
            additional_keys = []

            # Obtener las claves adicionales en el mismo orden en que aparecen en el JSON
            if json_data:
                sample_item = json_data[0]
                all_keys = list(sample_item.keys())
                excluded_keys = [
                    "RowNum",
                    "license",
                    "server_date",
                    "signal_date",
                    "event_name",
                    "latitude",
                    "longitude",
                    "calculated_speed",
                    "odometer",
                    "location",
                    "TotalPages",
                    "TotalRecords",
                ]
                additional_keys = [key for key in all_keys if key not in excluded_keys]

            total_registros = (
                int(json_data[0].get("TotalRecords", 0)) if json_data else 0
            )
            (
                page_obj,
                current_start_item,
                current_end_item,
                total_registros,
            ) = self.get_paginated_data(json_data, paginate_by, page)
            button_color = request.user.company.theme_set.all().first().button_color

            return render(
                request,
                self.template_name,
                {
                    "form": form,
                    "data": json_data,
                    "paginate_by": paginate_by,
                    "page_obj": page_obj,
                    "additional_keys": additional_keys,
                    "current_start_item": current_start_item,
                    "current_end_item": current_end_item,
                    "total_registros": total_registros,
                    "button_color": button_color,
                },
            )
        else:
            print("Errores en el formulario:", form.errors)
            return render(
                request, self.template_name, {"form": form, "errors": form.errors}
            )


class Advanced_AnalyticalView(
    PermissionRequiredMixin, LoginRequiredMixin, generic.TemplateView
):
    model = Advanced_Analytical
    login_url = reverse_lazy("index")
    template_name = "checkpoints/powerbi/advanced_analytical.html"
    permission_required = "checkpoints.view_advanced_analytical"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

class DataSemConfigurationList(LoginRequiredMixin, ListView):
    """
    Vista basada en clase para listar y paginar configuraciones de datos SEM.

    Atributos:
        model: Modelo asociado a la vista.
        login_url: URL de redirección para usuarios no autenticados.
        template_name: Plantilla utilizada para renderizar la vista.
    """
    model = Advanced_Analytical
    login_url = reverse_lazy("index")
    template_name = "checkpoints/powerbi/main_datasem.html"

    def get_paginate_by(self, queryset):
        """
        Obtiene el número de elementos por página de la solicitud POST o de los filtros de sesión.

        Args:
            queryset: Conjunto de datos (no utilizado en este método).

        Returns:
            int: Número de elementos por página.
        """
        paginate_by = self.request.POST.get('paginate_by', None)
        if paginate_by is None:
            session_filters = self.request.session.get(f"filters_sorted_confidatasem_{self.request.user.id}", {})
            paginate_by = session_filters.get("paginate_by", 15)
            paginate_by = self.convert_paginate_by_to_int(paginate_by)
            self.request.POST = self.request.POST.copy()
            self.request.POST['paginate_by'] = paginate_by
        return int(self.request.POST['paginate_by'])

    def convert_paginate_by_to_int(self, paginate_by):
        """
        Convierte el valor de `paginate_by` a entero.

        Args:
            paginate_by: Valor de `paginate_by`.

        Returns:
            int: Valor de `paginate_by` convertido a entero.
        """
        try:
            return int(paginate_by[0])
        except (TypeError, ValueError):
            return int(paginate_by) if paginate_by else 15

    def get_queryset(self):
        """
        Obtiene el conjunto de datos basado en los parámetros de solicitud y los filtros de sesión.

        Returns:
            list: Conjunto de datos ordenado.
        """
        user = self.request.user
        company = user.company
        params = self.get_request_params()
        search = params.get("q", params.get("query", "").lower())

        self.reset_session_filters_if_needed(params)

        session_filters = self.update_session_filters(params)
        order_by, direction = self.get_ordering_params(session_filters, params)

        queryset = fetch_all_confidatasem(company, user, search)
        sorted_queryset = self.sort_queryset(queryset, order_by, direction)

        return sorted_queryset

    def get_request_params(self):
        """
        Obtiene los parámetros de solicitud (GET o POST).

        Returns:
            QueryDict: Parámetros de solicitud.
        """
        return self.request.GET if self.request.method == 'GET' else self.request.POST

    def reset_session_filters_if_needed(self, params):
        """
        Reinicia los filtros de sesión si no se encuentran parámetros específicos en la solicitud.

        Args:
            params (dict): Parámetros de solicitud.
        """
        if 'order_by' not in params and 'paginate_by' not in params and 'page' not in params:
            if f"filters_sorted_confidatasem_{self.request.user.id}" in self.request.session:
                del self.request.session[f"filters_sorted_confidatasem_{self.request.user.id}"]
                self.request.session.modified = True

    def update_session_filters(self, params):
        """
        Actualiza los filtros de sesión con los nuevos parámetros de solicitud.

        Args:
            params (dict): Parámetros de solicitud.

        Returns:
            dict: Filtros de sesión actualizados.
        """
        session_filters = self.request.session.get(f'filters_sorted_confidatasem_{self.request.user.id}', {})
        session_filters.update(params)
        self.request.session[f"filters_sorted_confidatasem_{self.request.user.id}"] = session_filters
        self.request.session.modified = True
        return session_filters

    def get_ordering_params(self, session_filters, params):
        """
        Obtiene los parámetros de ordenación de los filtros de sesión o de la solicitud.

        Args:
            session_filters (dict): Filtros de sesión.
            params (dict): Parámetros de solicitud.

        Returns:
            tuple: Parámetros de ordenación (campo de ordenación, dirección).
        """
        order_by = params.get('order_by', session_filters.get('order_by', ['company_name'])[0])
        direction = params.get('direction', session_filters.get('direction', ['asc'])[0])
        return order_by, direction

    def sort_queryset(self, queryset, order_by, direction):
        """
        Ordena el conjunto de datos según los parámetros de ordenación.

        Args:
            queryset (list): Conjunto de datos.
            order_by (str): Campo de ordenación.
            direction (str): Dirección de ordenación ('asc' o 'desc').

        Returns:
            list: Conjunto de datos ordenado.
        """
        key_function = sort_key(order_by)
        reverse = direction == 'desc'
        try:
            return sorted(queryset, key=key_function, reverse=reverse)
        except KeyError:
            return sorted(queryset, key=lambda x: x["company_name"].lower(), reverse=reverse)

    def get_context_data(self, **kwargs):
        """
        Obtiene el contexto adicional para renderizar la plantilla.

        Args:
            **kwargs: Argumentos adicionales de contexto.

        Returns:
            dict: Contexto actualizado.
        """
        context = super().get_context_data(**kwargs)
        paginate_by = self.get_paginate_by(None)
        context["paginate_by"] = paginate_by
        page_number = context.get("page_obj").number if context.get("page_obj") else 1
        context["start_number"] = (page_number - 1) * paginate_by
        session_filters = self.request.session.get(f'filters_sorted_confidatasem_{self.request.user.id}', {})
        context['order_by'], context['direction'] = self.get_ordering_params(session_filters, self.get_request_params())
        return context

    @method_decorator(csrf_protect)
    def post(self, request, *args, **kwargs):
        """
        Maneja solicitudes POST para obtener y paginar el conjunto de datos.

        Args:
            request (HttpRequest): La solicitud HTTP.
            *args: Argumentos adicionales.
            **kwargs: Argumentos de palabra clave adicionales.

        Returns:
            HttpResponse: Respuesta HTTP con el contexto renderizado.
        """
        page_number = request.POST.get('page', 1)
        self.object_list = self.get_queryset()
        paginator = Paginator(self.object_list, self.get_paginate_by(None))
        page_obj = paginator.get_page(page_number)
        context = self.get_context_data(object_list=page_obj.object_list, page_obj=page_obj)
        return self.render_to_response(context)

class AddDataSemConfiguration(
    LoginRequiredMixin,
    CreateAuditLogAsyncMixin,
    generic.CreateView,
):
    """
    Vista para agregar un nuevo plan de datos.
    """

    model = Advanced_Analytical
    template_name = "checkpoints/powerbi/add_datasem.html"
    form_class = DataSemConfigurationForm

    def get_success_url(self):
        return reverse("realtime:confidatasem")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        companies = get_user_companies(user)
        context["form"].fields["company"].choices = companies
        
        button_color = self.request.user.company.theme_set.all().first().button_color
        context["button_color"] = button_color
        return context

    def form_valid(self, form):
        dataplan = form.save(commit=False)
        dataplan.modified_by = self.request.user
        dataplan.created_by = self.request.user
        dataplan.save()
        # Prepara una respuesta con redirección usando HTMX
        if self.request.htmx:
            return HttpResponse(headers={"HX-Redirect": self.get_success_url()})


class UpdateDataSemConfiguration(
    LoginRequiredMixin,
    UpdateAuditLogAsyncMixin,
    generic.UpdateView,
):
    """
    Esta clase es una vista basada en clase que permite actualizar los datos de un modelo
    "DataPlan" utilizando un formulario "DataPlanForm". Requiere de permisos para la vista y
    redirige al éxito al listar los planes de datos creados. Además, en el método
    "get_context_data", se actualiza el contexto con la información de la empresa del usuario
    actual y en "form_valid" se actualiza el campo "modified_by" del modelo y se guarda.
    Por último, retorna una respuesta HTTP vacía con un encabezado personalizado para actualizar
    la lista de planes de datos cambiados en tiempo real mediante tecnología HX.
    """

    model = Advanced_Analytical
    template_name = "checkpoints/powerbi/update_datasem.html"
    form_class = DataSemConfigurationForm
    success_url = reverse_lazy("realtime:list_dataplan_created")

    def get_success_url(self):
        # Asegúrate de que el nombre de la URL sea correcto y esté definido en tus archivos de URL.
        return reverse("realtime:dataplan")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        companies = get_user_companies(user)
        if user.company_id == 1:
            context["form"].fields["company"].choices = companies
        else:
            context["form"].fields["company"].queryset = companies
        button_color = self.request.user.company.theme_set.all().first().button_color
        context["button_color"] = button_color
        return context

    def form_valid(self, form):
        dataplan = form.save(commit=False)
        dataplan.modified_by = self.request.user
        dataplan.save()

        # Llama al método form_valid de la clase padre para registrar la acción en el log de auditoría
        response = super().form_valid(form)

        # Prepara una respuesta con redirección usando HTMX
        page_update = HttpResponse("")
        page_update["HX-Redirect"] = self.get_success_url()
        return page_update


class DeleteDataSemConfiguration(
    LoginRequiredMixin,
    DeleteAuditLogAsyncMixin,
    generic.UpdateView,
):
    """
    La clase DeleteDataPlanView es una vista de Django que hereda de las clases
    PermissionRequiredMixin, LoginRequiredMixin y  generic.UpdateView. Implementa
    la funcionalidad de ocultar un plan de datos (en lugar de eliminarlo) estableciendo
    el valor de la variable visible en False en el método form_valid(). Retorna una
    respuesta HTTP con el código 204 y la cabecera HX-Redirect para redirigir
    a la lista de planes de datos en la interfaz de usuario.
    """

    model = Advanced_Analytical
    template_name = "realtime/dataplan/delete_dataplan.html"
    permission_required = "realtime.delete_dataplan"
    fields = ["visible"]

    def get_success_url(self):
        # Asegúrate de que el nombre de la URL sea correcto y esté definido en tus archivos de URL.
        return reverse("realtime:dataplan")

    def form_valid(self, form):
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