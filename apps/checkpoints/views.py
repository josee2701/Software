import json
from datetime import date, timedelta

from django import forms
from django.contrib.auth.mixins import (LoginRequiredMixin,
                                        PermissionRequiredMixin)
from django.core.paginator import Paginator
from django.db import connection
from django.db.models import Q
from django.http import (Http404, HttpResponse, HttpResponseRedirect,
                         JsonResponse)
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views import View, generic
from django.views.decorators import cache, csrf
from django.views.generic import (CreateView, FormView, ListView, TemplateView,
                                  UpdateView)
from django.views.generic.detail import SingleObjectMixin
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.events.models import Event, EventFeature
from apps.realtime.models import AVLData, Vehicle
from apps.realtime.serializer import AVLDataSerializer
from apps.whitelabel.models import Company

from .forms import (CompanyScoreForm, DriverAnalyticForm, DriverForm,
                    ItemScoreFormsets, ReportDriverForm, ReportTodayForm)
from .models import (CompanyScoreSetup, Driver, DriverAnalytic, FatigueControl,
                     ItemScore, ItemScoreSetup)
from .postgres import GeocodingService, connect_db
from .sql import get_drivers_list, getCompanyScoresByCompanyAndUser


class ListDriverTemplate(PermissionRequiredMixin, LoginRequiredMixin, TemplateView):
    """
    Vista como clase que renderiza el template HTML que contiene la lista de conductores
    creados por una empresa (distribuidor).
    """

    template_name = "checkpoints/driver/main_drivers.html"
    permission_required = "checkpoints.view_driver"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({"pk": self.request.user.company_id})
        return context


class ListDriversView(PermissionRequiredMixin, LoginRequiredMixin, ListView):
    """
    Vista como clase que permite al usuario (distribuidor) visualizar los conductores
    creados para sus clientes finales, su configuración  y acceder a las opción para
    editar, añadir y eliminar.
    """

    model = Driver
    template_name = "checkpoints/driver/list_drivers_company.html"
    permission_required = "checkpoints.view_driver"
    context_object_name = "list_drivers"

    def get_queryset(self):
        # Llamamos al metodo get_drivers_list y nos retorna la lista de conductores.
        queryset = get_drivers_list(self.request.user.company_id)

        return queryset


class AddDriverView(PermissionRequiredMixin, LoginRequiredMixin, CreateView):
    """
    Vista como clase que implementa la opción de crear conductores para las empresas
    distribuidoras y asignarlas a un cliente final.
    Permite añadir una configuración personalizada para los campos  'Personal ID', 'first_name',
    'last_name', 'address','date_joined', 'is_active', 'password'.
    """

    template_name = "checkpoints/driver/add_driver.html"
    permission_required = "checkpoints.add_driver"
    form_class = DriverForm

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
        context = super().get_context_data(**kwargs)
        company_id = self.request.user.company_id
        if self.request.user.company_id == 1:
            companies = Company.objects.filter(
            visible=True, actived=True)
        # Caso 2: Si el usuario tiene compañías para monitorear, mostrar solo esas
        elif self.request.user.companies_to_monitor.exists():
            companies = self.request.user.companies_to_monitor.filter(visible=True, actived=True)  
        else:
            companies = Company.objects.filter(
                Q(id=self.request.user.company_id)
                | Q(provider_id=self.request.user.company_id),
                visible=True,
                actived=True,
            )
        # Ordenar el queryset
        companies = companies.order_by('company_name')

        # Asignar el queryset ordenado al campo del formulario
        context["form"].fields["company"].queryset = companies
        return context

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.modified_by = self.request.user

        form.save()

        return HttpResponse(status=204, headers={"HX-Trigger": "ListDriverChanged"})


class UpdateDriverView(PermissionRequiredMixin, LoginRequiredMixin, UpdateView):
    """
    Vista como clase que implementa la opción de editar la configuración personalizada
    de conductores para las empresas distribuidoras.
    """

    model = Driver
    template_name = "checkpoints/driver/update_driver.html"
    permission_required = "checkpoints.change_driver"
    form_class = DriverForm
    success_url = "/checkpoints/drivers"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company_id = self.request.user.company_id
        if self.request.user.company_id == 1:
            companies = Company.objects.filter(
            visible=True, actived=True)
        # Caso 2: Si el usuario tiene compañías para monitorear, mostrar solo esas
        elif self.request.user.companies_to_monitor.exists():
            companies = self.request.user.companies_to_monitor.filter(visible=True, actived=True)  
        else:
            companies = Company.objects.filter(
                Q(id=self.request.user.company_id)
                | Q(provider_id=self.request.user.company_id),
                visible=True,
                actived=True,
            )
        # Ordenar el queryset
        companies = companies.order_by('company_name')

        # Asignar el queryset ordenado al campo del formulario
        context["form"].fields["company"].queryset = companies
        return context

    def form_valid(self, form):
        form.instance.modified_by = self.request.user
        form.save()
        return HttpResponse(status=204, headers={"HX-Trigger": "ListDriverChanged"})


class DeleteDriverView(PermissionRequiredMixin, LoginRequiredMixin, generic.UpdateView):
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

    def form_valid(self, form):
        driver = form.save(commit=False)
        driver.modified_by = self.request.user
        driver.visible = False
        driver.save()
        return HttpResponse(status=204, headers={"HX-Trigger": "ListDriverChanged"})


class BottonView(LoginRequiredMixin, TemplateView):
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
        except Exception:
            return reverse_lazy("checkpoints:list_drivers")


class AddAssignDriverView(LoginRequiredMixin, CreateView):
    """
    Vista como clase que permite a los usuarios (distribuidores) asignar un vehículo a un conductor
    por primera vez.
    """

    model = DriverAnalytic
    form_class = DriverAnalyticForm
    template_name = "checkpoints/driver_analytic/assign_driver.html"

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
        return context

    def form_valid(self, DriverAnalitycForm):
        DriverAnalitycForm.instance.driver_id = self.kwargs.get("pk")
        DriverAnalitycForm.instance.created_by = self.request.user
        DriverAnalitycForm.instance.modified_by = self.request.user
        DriverAnalitycForm.save()
        return HttpResponse(status=204, headers={"HX-Trigger": "ListDriverChanged"})


class UpdateAssignDriverView(LoginRequiredMixin, CreateView):
    """
    Vista como clase que permite a los usuarios (distribuidores) añadir más vehículos a un
    conductor que ya cuenta con un vehículo asignado.
    """

    model = DriverAnalytic
    form_class = DriverAnalyticForm
    template_name = "checkpoints/driver_analytic/update_assign.html"

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
        return HttpResponse(status=204, headers={"HX-Trigger": "ListDriverChanged"})

    def form_invalid(self, form):
        """
        Eleva la condición de error para la que fue llamada en la función
        form_valid, renderizando el mensaje de error así como el formulario.
        """
        return self.render_to_response(self.get_context_data(form=form))


class UpdateVehicleAssignView(LoginRequiredMixin, UpdateView):
    model = DriverAnalytic
    form_class = DriverAnalyticForm
    template_name = "checkpoints/driver_analytic/update_vehicle_assign.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

    def form_valid(self, form):
        form.instance.modified_by = self.request.user
        # Aquí deberías actualizar el objeto existente en lugar de crear uno nuevo
        return super().form_valid(form)

    def get_success_url(self):
        driver_analytic = (
            self.object
        )  # Usar self.object en lugar de consultar la base de datos nuevamente
        driver = driver_analytic.driver
        return reverse("checkpoints:update_assign", args=(driver.id,))


class ListScoreCompanyTemplate(
    PermissionRequiredMixin, LoginRequiredMixin, TemplateView
):
    """
    Vista como clase que renderiza el template HTML que contiene la lista de
    empresas (clientes finales) a las que tiene acceso un distribuidor
    para configurar su calificación de conductores.
    """

    template_name = "checkpoints/score_configuration/main_score_configuration.html"
    permission_required = "checkpoints.view_companyscoresetup"


class ListScoreCompaniesView(PermissionRequiredMixin, LoginRequiredMixin, ListView):
    """
    Vista como clase que muestra a las empresas (distribuidoras) sus clientes finales
    así como la opción de acceder a la configuración de calificación.
    """

    template_name = (
        "checkpoints/score_configuration/list_score_configuration_companies.html"
    )
    context_object_name = "list_score_configuration"
    permission_required = "checkpoints.view_companyscoresetup"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Obtener todas las empresas
        list_score_configuration = getCompanyScoresByCompanyAndUser(self.request.user.company_id, self.request.user.id)
        
        context["list_score_configuration"] = list_score_configuration

        return context

    def get_queryset(self):
        return CompanyScoreSetup.objects.all()


class ScoreConfigurationView(
    PermissionRequiredMixin, LoginRequiredMixin, SingleObjectMixin, FormView
):
    """
    Vista como clase que permite a las empresas (distribuidoras) configurar
    los parámetros sobre los que van a evaluarse los conductores de sus clientes
    """

    model = CompanyScoreSetup
    template_name = "checkpoints/score_configuration/update_score_configuration.html"
    permission_required = "checkpoints.add_companyscoresetup"

    def get_queryset(self):
        # Se crea una lista con los itemss
        query_items = ItemScore.objects.all()
        items = [item for item in query_items]
        return items

    def get_score_forms(self, items, score_form):
        # Se crea la funcion donde trae la lista de los items, crea una lista de tuplas,
        # ada una con un ítem y el formulario correspondiente (score_form) para ese ítem.
        # Recibe la lista de ítems y la lista de formularios de puntuación como parámetros y
        # retorna una lista de tuplas.
        forms = [(items[i], score_form[i]) for i in range(len(items))]
        return forms

    def get_object(self):
        try:
            company = self.kwargs.get("pk")
            get_object_or_404(CompanyScoreSetup, company_id=company)
            query_items = ItemScore.objects.all()
            query_company = CompanyScoreSetup.objects.get(company_id=company)
            len_item = ItemScoreSetup.objects.filter(company_score_id=query_company.pk)
            # Si no o los itemes son diferentes en el objetos ItemScoreSetup asociados a este
            # CompanyScoreSetup,
            # creamos configuraciones predeterminadas para cada ítem en la base de datos.
            if len(query_items) != len_item.count():
                # Si no hay objetos ItemScoreSetup, creamos configuraciones predeterminadas para
                # todos los ítems.
                if len(len_item) == 0:
                    for item in query_items:
                        ItemScoreSetup.objects.create(
                            company_score_id=query_company.pk,
                            item_id=item.pk,
                            created_by=self.request.user,
                            modified_by=self.request.user,
                        )
                    obj = query_company
                else:
                    # Si faltan algunos ítems, identificamos cuáles faltan y creamos las
                    # configuraciones faltantes.
                    existing_items = {item.item_id for item in len_item}
                    missing_items = [
                        item for item in query_items if item.pk not in existing_items
                    ]
                    for item in missing_items:
                        ItemScoreSetup.objects.create(
                            company_score_id=query_company.pk,
                            item_id=item.pk,
                            created_by=self.request.user,
                            modified_by=self.request.user,
                        )
                    obj = query_company
            else:
                obj = query_company
        except CompanyScoreSetup.DoesNotExist:
            # Si no se encuentra un objeto CompanyScoreSetup con el "company_id" lanzamos un error
            # 404
            raise Http404
        return obj

    def get(self, request, *args, **kwargs):
        # Obtiene el objeto CompanyScoreSetup usando el método get_object() y lo almacena en
        # self.object
        self.object = self.get_object()
        # Crea un formulario CompanyScoreForm usando el objeto CompanyScoreSetup almacenado
        # en self.object
        form = CompanyScoreForm(instance=self.object)
        # Crea un conjunto de formularios ItemScoreFormsets usando el objeto CompanyScoreSetup
        # almacenado en self.object
        score_form = ItemScoreFormsets(instance=self.object)
        # Obtiene una lista de ítems (nombres de los ítems) usando el método get_queryset()
        items = self.get_queryset()
        # Crea una lista de tuplas que contiene cada ítem junto con su formulario de puntuación
        # correspondiente utilizando la función get_score_forms() y las listas de ítems y
        # formularios de puntuación
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = CompanyScoreForm(request.POST, instance=self.object)
        score_formset = ItemScoreFormsets(request.POST, instance=self.object)

        if form.is_valid() and score_formset.is_valid():
            return self.form_valid(form, score_formset)
        else:
            return self.form_invalid(form, score_formset)

    def form_valid(self, form, score_formset):
        # Guardamos el CompanyScoreSetup con los campos modificados
        company_score_setup = form.save(commit=False)
        company_score_setup.modified_by = self.request.user
        if not company_score_setup.created_by_id:
            company_score_setup.created_by = self.request.user
        company_score_setup.save()

        # Guardamos los formularios de ItemScoreSetup
        instances = score_formset.save(commit=False)
        for instance in instances:
            instance.modified_by = self.request.user
            if not instance.created_by_id:
                instance.created_by = self.request.user
            instance.save()

        # Guardamos las relaciones ManyToMany si hay alguna
        score_formset.save_m2m()

        return HttpResponse(status=204, headers={"HX-Trigger": "ListScoreChanged"})

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


# class ReportFormView(View):
#     template_name = 'checkpoints/reportes/report_from.html'

#     def get(self, request):
#         form = ReportFilterForm()
#         return render(request, self.template_name, {'form': form})

#     def post(self, request):
#         print(self.request.POST)
#         form = ReportFilterForm(request.POST)
#         if form.is_valid():
#             company = form.cleaned_data['company']
#             drivers = form.cleaned_data['driver']
#             start_date = form.cleaned_data['start_date']
#             end_date = form.cleaned_data['end_date']
#             # Aquí puedes redirigir a ReportResultsView o filtrar los datos directamente
#             # y mostrar los resultados en el mismo template.
#             # Por ahora, redirigiremos a ReportResultsView con los datos filtrados.
#         for driver in drivers:
#             driver_ids = []
#             if isinstance(drivers, str):
#                 driver_ids = [int(id) for id in drivers.split(",") if id.isdigit()]
#             else:
#                 # Si drivers es un número entero, simplemente agrégalo a la lista
#                 driver_ids = [drivers]
#             return redirect('checkpoints:report_results', company=company.id, drivers=driver_ids,
# start_date=start_date, end_date=end_date)


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

    def get_companies(self):
        """
        Filtro el cual valida si el usuario está autenticado y me trae las empresas de acuerdo
        al id de la compañía del usuario.

        Returns:
            QuerySet: Un conjunto de objetos Company que cumplen con los criterios de filtrado.

        Raises:
            Http404: Si el usuario no está autenticado.
        """
        user = self.request.user
        if not user.is_authenticated:
            raise Http404("User not authenticated")

        company_id = user.company_id
        if company_id == 1:
            companies = Company.objects.filter(visible=True, actived=True)
        else:
            provider_company_ids = Company.objects.filter(
                provider_id=company_id
            ).values_list("id", flat=True)
            companies = Company.objects.filter(
                Q(id=company_id) | Q(provider_id=company_id), visible=True
            )
        return companies

    def execute_stored_procedure(
        self, company_id, imei, fecha_inicial, fecha_final, paginate_by, page
    ):
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
        companies = self.get_companies()
        form.fields["Company_id"].queryset = companies
        return render(request, self.template_name, {"form": form})

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
        form = ReportTodayForm(request.POST)
        companies = self.get_companies()
        form.fields["Company_id"].queryset = companies

        if form.is_valid():
            page_str = request.POST.get("page", "1").strip()
            page = int(page_str) if page_str.isdigit() else 1

            paginate_by_str = request.POST.get("paginate_by", "").strip()
            paginate_by = (
                int(paginate_by_str)
                if paginate_by_str.isdigit()
                else request.session.get("paginate_by", 10)
            )
            request.session["paginate_by"] = paginate_by

            company_id = form.cleaned_data["Company_id"].id
            imei = form.cleaned_data["Imei"].imei
            timezone_offset = int(request.POST.get("timezone_offset", 0))

            fecha_inicial = form.cleaned_data["FechaInicial"] - timedelta(
                minutes=timezone_offset
            )
            fecha_final = form.cleaned_data["FechaFinal"] - timedelta(
                minutes=timezone_offset
            )

            fecha_inicial_str = fecha_inicial.strftime("%Y-%m-%d %H:%M:%S")
            fecha_final_str = fecha_final.strftime("%Y-%m-%d %H:%M:%S")

            json_data = self.execute_stored_procedure(
                company_id, imei, fecha_inicial_str, fecha_final_str, paginate_by, page
            )
            json_data = self.update_dates_and_location(json_data, timezone_offset)

            additional_keys = [
                key
                for item in json_data
                for key in item.keys()
                if key
                not in [
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
            ]
            additional_keys = list(set(additional_keys))
            total_registros = (
                int(json_data[0].get("TotalRecords", 0)) if json_data else 0
            )
            (
                page_obj,
                current_start_item,
                current_end_item,
                total_registros,
            ) = self.get_paginated_data(json_data, paginate_by, page)

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
                },
            )
        else:
            return render(
                request, self.template_name, {"form": form, "errors": form.errors}
            )


class ReportToday(View):
    template_name = "checkpoints/reportes/report_today_copy.html"

    def get(self, request):
        form = ReportTodayForm()  # Inicializa el formulario vacío
        return render(request, self.template_name, {"form": form})


class ReportDataAPIView(APIView):
    def get(self, request):
        # Recoge los parámetros de la solicitud GET
        company_id = request.query_params.get("company_id")
        vehicle = request.query_params.get(
            "vehicles"
        )  # Asegúrate que esto coincide con cómo se envía en el formulario
        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")
        # event_id = request.query_params.get('event')

        # Construye el queryset basado en los parámetros recibidos
        queryset = AVLData.objects.all()
        # if company_id:
        #     queryset = queryset.filter(company_id=company_id)
        if vehicle:
            queryset = queryset.filter(device=vehicle)
        # if event_id:
        #     queryset = queryset.filter(event_id=event_id)
        if start_date and end_date:
            queryset = queryset.filter(server_date__range=[start_date, end_date])

        # Serializa los datos
        serializer = AVLDataSerializer(queryset, many=True)
        return Response(serializer.data)
