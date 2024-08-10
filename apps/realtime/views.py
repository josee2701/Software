import json
from itertools import chain

from django.contrib import messages
from django.contrib.auth.mixins import (LoginRequiredMixin,
                                        PermissionRequiredMixin)
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views import View, generic
from django.views.generic import TemplateView
from rest_framework import generics

from apps.realtime.forms import (DataPlanForm, DeviceForm, SimcardForm,
                                 VehicleForm, VehicleGroupForm)
from apps.realtime.models import (DataPlan, Device, FamilyModelUEC,
                                  Manufacture, SimCard, Vehicle, VehicleGroup)
from apps.realtime.serializer import GeozonesSerializer, VehicleSerializer
from apps.whitelabel.models import Company
from config.pagination import get_paginate_by

from .apis import get_geozone_by_id, get_user_vehicles
from .forms import (ConfigurationReport, DataPlanForm, DeviceForm,
                    GeozonesForm, SendingCommandsFrom, SimcardForm,
                    VehicleForm, VehicleGroupForm)
from .models import (Command_response, DataPlan, Device, FamilyModelUEC,
                     Geozones, Io_items_report, Last_Avl, Manufacture,
                     Sending_Commands, SimCard, Vehicle, VehicleGroup)
from .sql import (ListDeviceByCompany, ListVehicleByUserAndCompany,
                  ListVehicleGroupsByCompany, fetch_all_dataplan,
                  fetch_all_geozones, fetch_all_response_commands,
                  fetch_all_sending_commands, fetch_all_simcards)


class ListDataPlanTemplate(
    PermissionRequiredMixin, LoginRequiredMixin, generic.ListView
):
    """
    Vista como clase que renderiza el template HTML que contiene la lista de planes de datos.
    """

    model = DataPlan
    template_name = "realtime/dataplan/main_dataplan.html"
    permission_required = "realtime.view_dataplan"

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
        Obtiene el conjunto de datos de los planes de datos reales de la compañía asociada al
        usuario que realiza la solicitud.

        Returns:
            List[dict]: Lista de planes de datos ordenada por 'Company' en forma descendente.
        """
        user = self.request.user
        company = user.company
        # Obtener los planes de datos a través de la función fetch_all_dataplan.
        queryset = fetch_all_dataplan(company, user)

        # Ordenar los resultados por 'Company' de forma descendente.
        # Si queryset es una lista de diccionarios, Python no tiene un método `order_by`.
        # Se debe utilizar la función sorted para ordenar listas de diccionarios.
        queryset = sorted(queryset, key=lambda x: x["Company"], reverse=False)

        return queryset

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


class AddDataPlanView(PermissionRequiredMixin, LoginRequiredMixin, generic.CreateView):
    """
    Este código define una vista de clase llamada "AddDataPlanView" que hereda de otras dos
    vistas y utiliza un formulariollamado "DataPlanForm". También define un método
    "get_context_data" que agrega información adicional al contexto de lavista y un método
    "form_valid" que guarda los datos del formulario y devuelve una respuesta HTTP con un
    encabezado personalizado.
    """

    template_name = "realtime/dataplan/add_dataplan.html"
    permission_required = "realtime.add_dataplan"
    form_class = DataPlanForm

    def get_success_url(self):
        # Asegúrate de que el nombre de la URL sea correcto y esté definido en tus archivos de URL.
        return reverse("realtime:dataplan")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
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
        dataplan = form.save(commit=False)
        dataplan.modified_by = self.request.user
        dataplan.created_by = self.request.user
        dataplan.save()
        page_update = HttpResponse(
            ""
        )  # O puedes enviar algún contenido si es necesario.
        page_update["HX-Redirect"] = self.get_success_url()
        return page_update


class UpdateDataPlanView(
    PermissionRequiredMixin, LoginRequiredMixin, generic.UpdateView
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

    model = DataPlan
    template_name = "realtime/dataplan/update_dataplan.html"
    permission_required = "realtime.change_dataplan"
    form_class = DataPlanForm
    success_url = reverse_lazy("realtime:list_dataplan_created")

    def get_success_url(self):
        # Asegúrate de que el nombre de la URL sea correcto y esté definido en tus archivos de URL.
        return reverse("realtime:dataplan")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
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
        dataplan = form.save(commit=False)
        dataplan.modified_by = self.request.user
        dataplan.save()
        page_update = HttpResponse(
            ""
        )  # O puedes enviar algún contenido si es necesario.
        page_update["HX-Redirect"] = self.get_success_url()
        return page_update


class DeleteDataPlanView(
    PermissionRequiredMixin, LoginRequiredMixin, generic.UpdateView
):
    """
    La clase DeleteDataPlanView es una vista de Django que hereda de las clases P
    ermissionRequiredMixin, LoginRequiredMixin y generic.UpdateView. Implementa la funcionalidad
    de ocultar un plan de datos (en lugar de eliminarlo) estableciendo el valor de la variable
    visible en False en el método form_valid(). Retorna una respuesta HTTP con el código 204 y
    la cabecera HX-Trigger para actualizar la lista de planes de datos en la interfaz de usuario.
    """

    model = DataPlan
    template_name = "realtime/dataplan/delete_dataplan.html"
    permission_required = "realtime.delete_dataplan"
    fields = ["visible"]

    def get_success_url(self):
        # Asegúrate de que el nombre de la URL sea correcto y esté definido en tus archivos de URL.
        return reverse("realtime:dataplan")

    def form_valid(self, form):
        dataplan = form.save(commit=False)
        dataplan.modified_by = self.request.user
        dataplan.visible = False
        dataplan.save()
        page_update = HttpResponse(
            ""
        )  # O puedes enviar algún contenido si es necesario.
        page_update["HX-Redirect"] = self.get_success_url()
        return page_update


class ListSimcardTemplate(
    PermissionRequiredMixin, LoginRequiredMixin, generic.ListView
):
    """
    Vista como clase que renderiza el template HTML que contiene la lista de simcards.
    """

    model = SimCard
    template_name = "realtime/simcards/main_simcard.html"
    context_object_name = "simcards"
    permission_required = "realtime.view_simcard"

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
        company = user.company
        # Obtener los planes de datos a través de la función fetch_all_dataplan.
        queryset = fetch_all_simcards(company, user)

        # Ordenar los resultados por 'Company' de forma descendente.
        # Si queryset es una lista de diccionarios, Python no tiene un método `order_by`.
        # Se debe utilizar la función sorted para ordenar listas de diccionarios.
        queryset = sorted(queryset, key=lambda x: x["Company"], reverse=False)

        return queryset

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


class AddSimcardView(PermissionRequiredMixin, LoginRequiredMixin, generic.CreateView):
    """
    Clase que implementa la opción de crear tarjetas SIM. Permite añadir una configuración
    personalizada para los campos 'serial_number', 'phone_number', 'expiration_date' y 'data_plan'.
    También tiene métodos para obtener el queryset y el contexto de la vista, y el método
    form_valid que guarda la información de la tarjeta SIM y devuelve una respuesta HTTP.
    Esta clase requiere que el usuario tenga los permisos necesarios para acceder a ella y utiliza
    un formulario de tipo SimcardForm.
    """

    model = SimCard
    form_class = SimcardForm
    template_name = "realtime/simcards/add_simcard.html"
    permission_required = "realtime.add_simcard"

    def get_success_url(self):
        # Asegúrate de que el nombre de la URL sea correcto y esté definido en tus archivos de URL.
        return reverse("realtime:simcards")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_company = self.request.user.company_id
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
        context["simcard"] = user_company
        return context

    def form_valid(self, form):
        # form.clean_activate_date()
        form.instance.modified_by = self.request.user
        form.instance.created_by = self.request.user
        form.save()
        page_update = HttpResponse(
            ""
        )  # O puedes enviar algún contenido si es necesario.
        page_update["HX-Redirect"] = self.get_success_url()
        return page_update


class UpdateSimcardView(
    PermissionRequiredMixin, LoginRequiredMixin, generic.UpdateView
):
    """
    Esta es una clase de vista que implementa la opción de editar información de las Simcards.
    Modifica la configuración personalizada de los campos 'serial_number', 'phone_number',
    'expiration_date', 'data_plan'. También actualiza los planes de datos disponibles para el
    usuario en el contexto. Si el formulario es válido, se guarda la instancia de la Simcard y se
    devuelve una respuesta HTTP 204 con un encabezado HX-Trigger. Si el formulario no es válido,
    se muestra el formulario de nuevo.
    """

    model = SimCard
    template_name = "realtime/simcards/update_simcard.html"
    permission_required = "realtime.change_simcard"
    form_class = SimcardForm

    def get_success_url(self):
        # Asegúrate de que el nombre de la URL sea correcto y esté definido en tus archivos de URL.
        return reverse("realtime:simcards")

    def get_initial(self, *args, **kwargs):
        initial = super().get_initial(*args, **kwargs)
        initial["activate_date"] = self.object.activate_date.strftime("%Y-%m-%d")
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_company = self.request.user.company_id
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
        context["simcard"] = user_company
        return context

    def form_valid(self, form):
        # form.clean_activate_date()
        form.instance.modified_by = self.request.user
        form.save()
        page_update = HttpResponse(
            ""
        )  # O puedes enviar algún contenido si es necesario.
        page_update["HX-Redirect"] = self.get_success_url()
        return page_update

    def form_invalid(self, form):
        return super().form_invalid(form)


class DeleteSimcardView(
    PermissionRequiredMixin, LoginRequiredMixin, generic.UpdateView
):
    """
    Este código define una vista de Django que implementa la eliminación de una instancia del
    modelo "SimCard". En lugar de eliminar el objeto, se establece el valor de la propiedad
    "visible" en False, lo que oculta la información del objeto.El usuario debe estar autenticado
    y tener los permisos necesarios para acceder a esta vista. La vista utiliza un formulario con
    un campo "visible" y, una vez validado, redirige a la lista de objetos "SimCard" creados.
    """

    model = SimCard
    template_name = "realtime/simcards/delete_simcard.html"
    permission_required = "realtime.delete_simcard"
    success_url = reverse_lazy("realtime:list_simcard_created")
    fields = ["visible"]

    def get_success_url(self):
        # Asegúrate de que el nombre de la URL sea correcto y esté definido en tus archivos de URL.
        return reverse("realtime:simcards")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        object2 = (
            self.object.device_set.first()
        )  # Obtiene el primer Device asociado a la SimCard
        context.update({"object2": object2})
        return context

    def form_valid(self, form):
        simcard = form.save(commit=False)
        simcard.visible = False
        simcard.save()

        page_update = HttpResponse(
            ""
        )  # O puedes enviar algún contenido si es necesario.
        page_update["HX-Redirect"] = self.get_success_url()
        return page_update


class ListDeviceTemplate(PermissionRequiredMixin, LoginRequiredMixin, generic.ListView):
    """
    Vista como clase que renderiza el template HTML que contiene la lista de dispositivos.
    """

    model = Device
    template_name = "realtime/devices/main_devices.html"
    permission_required = "realtime.view_device"

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
        devices = ListDeviceByCompany(user.company_id, user.id)
        return devices

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


class AddDeviceView(PermissionRequiredMixin, LoginRequiredMixin, generic.CreateView):
    """
    Este código define una vista de Django para agregar un nuevo objeto "Device" en la base de
    datos. El usuario debe estar autenticado y tener los permisos necesarios para acceder a esta
    vista. La vista también agrega datos adicionales al contexto de la plantilla, como las
    tarjetas SIM, los fabricantes y los modelos de familia de UEC. El método "form_valid" se
    utiliza para guardar los datos del formulario y retorna una respuesta HTTP con el código de
    estado 204 y una cabecera personalizada para actualizar la lista de dispositivos.
    """

    model = Device
    template_name = "realtime/devices/add_device.html"
    permission_required = "realtime.add_device"
    form_class = DeviceForm

    def get_success_url(self):
        # Asegúrate de que el nombre de la URL sea correcto y esté definido en tus archivos de URL.
        return reverse("realtime:devices")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
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
        manufactures = Manufacture.objects.all()
        family_models = FamilyModelUEC.objects.all()
        selected_model = self.request.POST.get("model")
        int_selected_model = None
        if selected_model is not None:
            int_selected_model = int(selected_model)
        context.update(
            {
                "manufactures": manufactures,
                "family_models": family_models,
                "selected_model": int_selected_model,
            }
        )
        return context

    def form_valid(self, form):
        form.instance.modified_by = self.request.user
        form.instance.created_by = self.request.user

        form.save()

        page_update = HttpResponse(
            ""
        )  # O puedes enviar algún contenido si es necesario.
        page_update["HX-Redirect"] = self.get_success_url()
        return page_update

    def form_invalid(self, form):
        # Manejo personalizado de errores del formulario
        return self.render_to_response(self.get_context_data(form=form))


class UpdateDeviceView(PermissionRequiredMixin, LoginRequiredMixin, generic.UpdateView):
    """
    Este código define una vista de Django que se utiliza para editar un objeto "Device" en la
    base de datos.  El usuario debe estar autenticado y tener los permisos necesarios para acceder
    a esta vista. La vista también agrega datos adicionales al contexto de la plantilla, como las
    tarjetas SIM, los fabricantes y los modelos de familia de UEC.
    El método "form_valid" se utiliza para guardar los datos del formulario y retorna una respuesta
    HTTP con el código de estado 204 y una cabecera personalizada para actualizar la lista de dispositivos.
    """

    model = Device
    template_name = "realtime/devices/update_device.html"
    permission_required = "realtime.change_device"
    form_class = DeviceForm

    def get_success_url(self):
        # Asegúrate de que el nombre de la URL sea correcto y esté definido en tus archivos de URL.
        return reverse("realtime:devices")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
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
        user_device = self.object

        manufactures = Manufacture.objects.all()
        family_models = FamilyModelUEC.objects.all()
        selected_model = self.request.POST.get("model")
        int_selected_model = None
        if selected_model is not None:
            int_selected_model = int(selected_model)
        model_assigned = user_device.familymodel if user_device.familymodel else None
        context["model_assigned"] = model_assigned

        context.update(
            {
                "manufactures": manufactures,
                "family_models": family_models,
                "selected_model": int_selected_model,
            }
        )
        return context

    def form_valid(self, form):
        form.instance.modified_by = self.request.user
        form.save()
        page_update = HttpResponse(
            ""
        )  # O puedes enviar algún contenido si es necesario.
        page_update["HX-Redirect"] = self.get_success_url()
        return page_update

    def form_invalid(self, form):
        # Manejo personalizado de errores del formulario
        return self.render_to_response(self.get_context_data(form=form))


class DeleteDeviceView(PermissionRequiredMixin, LoginRequiredMixin, generic.UpdateView):
    """
    Este código define una vista de Django para eliminar un objeto "Device" de la base de datos y
    configurar su campo "visible" como falso. Se requiere que el usuario tenga ciertos permisos y
    esté autenticado para acceder a la vista, y se utiliza una plantilla específica y una ruta de
    éxito. El método "form_valid" se utiliza para guardar el objeto modificado y se retorna una
    respuesta HTTP con el código de estado 204 y una cabecera personalizada para actualizar la
    lista de dispositivos.
    """

    model = Device
    template_name = "realtime/devices/delete_devices.html"
    permission_required = "realtime.delete_device"
    success_url = reverse_lazy("realtime:list_devices")
    fields = ["visible"]

    def get_success_url(self):
        # Asegúrate de que el nombre de la URL sea correcto y esté definido en tus archivos de URL.
        return reverse("realtime:devices")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        device = self.get_object()
        vehicle = (
            device.vehicle_set.first()
        )  # Obtener el primer vehículo asociado al dispositivo
        context["vehicle"] = vehicle
        return context

    def form_valid(self, form):
        davice = form.save(commit=False)
        davice.visible = False
        davice.is_active = False
        davice.save()

        # Obtener el vehículo asociado al dispositivo
        vehicle = davice.vehicle_set.first()

        # Si hay un vehículo asociado, cambiar su estado a inactivo
        if vehicle:
            vehicle.is_active = False
            vehicle.device = None  # Limpiar el campo de dispositivo
            vehicle.save()

        page_update = HttpResponse(
            ""
        )  # O puedes enviar algún contenido si es necesario.
        page_update["HX-Redirect"] = self.get_success_url()
        return page_update


class ListVehicleTemplate(
    PermissionRequiredMixin, LoginRequiredMixin, generic.ListView
):
    """
    La clase ListVehicleTemplate es una vista que requiere permisos y autenticación, y que
    renderiza un template HTML para mostrar una lista de vehículos. la propiedad
    permission_required: Esta propiedad especifica el permiso requerido para acceder a la vista.
    """

    model = Vehicle
    template_name = "realtime/vehicles/main_vehicles.html"
    permission_required = "realtime.view_vehicle"

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
        vehicles = ListVehicleByUserAndCompany(
            self.request.user.company_id, self.request.user.id
        )
        return vehicles

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


# class ListVehiclesView(PermissionRequiredMixin, LoginRequiredMixin, generic.ListView):
#     """
#     Este código define una vista de Django para listar los objetos "Vehicle" en la base de datos.
#     La vista requiere que el usuario tenga ciertos permisos y esté autenticado para acceder a ella.
#     Se agrega una lista de vehículos visibles y pertenecientes a la compañía del usuario al
#     contexto de la plantilla y se devuelve un queryset de todos los vehículos pertenecientes a la
#     compañía del usuario.
#     """

#     model = Vehicle
#     template_name = "realtime/vehicles/list_vehicles_created.html"
#     context_object_name = "list_vehicles"
#     permission_required = "realtime.view_vehicle"

#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         user = self.request.user  # Obtener el usuario actual

#         user_company = user.company_id
#         companies_to_monitor = user.companies_to_monitor.all()
#         user_selected_vehicles = user.vehicles_to_monitor.all()
#         user_selected_group_vehicles = Vehicle.objects.filter(
#             vehiclegroup__in=user.group_vehicles.all()
#         )
#         provider_company_ids = Company.objects.filter(
#             provider_id=user_company
#         ).values_list("id", flat=True)
#         list_vehicles = Vehicle.objects.filter(
#             Q(company_id=user_company, visible=True)
#             | Q(company_id__in=list(provider_company_ids), visible=True)
#         )

#         if (
#             companies_to_monitor.exists()
#             or user_selected_vehicles.exists()
#             or user_selected_group_vehicles.exists()
#         ):
#             companies = companies_to_monitor.filter(visible=True)

#             list_vehicles = list_vehicles.filter(
#                 Q(id__in=user_selected_vehicles)
#                 | Q(id__in=user_selected_group_vehicles)
#             )
#             list_vehicles = Vehicle.objects.filter(
#                 company_id=user_company, visible=True
#             ) | Vehicle.objects.filter(company__in=companies, visible=True)

#         else:
#             companys_provider = Company.objects.filter(id=self.request.user.company_id)
#             list_vehicles = list_vehicles | Vehicle.objects.filter(
#                 company__in=companys_provider, visible=True
#             )

#         context["list_vehicles"] = list_vehicles
#         return context


class AddVehicleView(PermissionRequiredMixin, LoginRequiredMixin, generic.CreateView):

    """
    Este código define una vista de Django para agregar un objeto "Vehicle" a la base de datos.
    Se requiere que el usuario tenga ciertos permisos y esté autenticado para acceder a la vista.
    La vista agrega datos adicionales al formulario y devuelve una respuesta HTTP con el código de
    estado 204 y una cabecera personalizada para actualizar la lista de vehículos.
    """

    model = Vehicle
    template_name = "realtime/vehicles/add_vehicle.html"
    permission_required = "realtime.add_vehicle"
    form_class = VehicleForm

    def get_success_url(self):
        # Asegúrate de que el nombre de la URL sea correcto y esté definido en tus archivos de URL.
        return reverse("realtime:vehicles")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company_id = self.request.user.company_id

        # Filtrar los devices que ya están asignados a vehículos por company_id y son visibles
        assigned_devices = Device.objects.filter(
            company_id=company_id, vehicle__visible=True, is_active=True
        )

        # Obtener los dispositivos disponibles (que no están asignados a ningún vehículo y son visibles)
        available_devices = Device.objects.filter(
            company_id=company_id, visible=True, is_active=True
        ).exclude(pk__in=assigned_devices)

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
        # Obtener los dispositivos disponibles (que no están asignados a ningún vehículo)
        # available_devices = Device.objects.filter(company_id=company_id, visible=True, vehicle__isnull=True)
        # context["form"].fields["device"].queryset = available_devices

        return context

    def form_valid(self, form):
        vehicle = form.save(commit=False)
        vehicle.modified_by = self.request.user
        vehicle.created_by = self.request.user
        vehicle.icon = form.cleaned_data["icon"]
        vehicle.save()
        page_update = HttpResponse(
            ""
        )  # O puedes enviar algún contenido si es necesario.
        page_update["HX-Redirect"] = self.get_success_url()
        return page_update


class UpdateVehicleView(
    PermissionRequiredMixin, LoginRequiredMixin, generic.UpdateView
):

    """
    Este código define una vista de Django para actualizar un objeto "Vehicle" en la base de datos.
    Se requiere que el usuario tenga ciertos permisos y esté autenticado para acceder a la vista.
    La vista agrega datos adicionales al contexto de la plantilla y devuelve una respuesta HTTP
    con el código de estado 204 y una cabecera personalizada para actualizar la lista de vehículos.
    """

    model = Vehicle
    template_name = "realtime/vehicles/update_vehicle.html"
    permission_required = "realtime.change_vehicle"
    form_class = VehicleForm

    def get_success_url(self):
        # Asegúrate de que el nombre de la URL sea correcto y esté definido en tus archivos de URL.
        return reverse("realtime:vehicles")

    def get_initial(self, *args, **kwargs):
        initial = super().get_initial(*args, **kwargs)
        if self.object.installation_date is not None:
            initial["installation_date"] = self.object.installation_date.strftime(
                "%Y-%m-%d"
            )
        if self.object.icon:
            initial["icon"] = self.object.icon
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_vehicle = self.object
        # Configurar el valor seleccionado para el campo 'icon'
        selected_icon = user_vehicle.icon
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
        assigned_devices = Device.objects.filter(vehicle=user_vehicle).values_list(
            "pk", flat=True
        )

        context["form"].initial["icon"] = selected_icon
        return context

    def form_valid(self, form):
        vehicle = form.save(commit=False)
        vehicle.modified_by = self.request.user
        vehicle.icon = form.cleaned_data["icon"]
        vehicle.save()
        page_update = HttpResponse(
            ""
        )  # O puedes enviar algún contenido si es necesario.
        page_update["HX-Redirect"] = self.get_success_url()
        return page_update


class DeleteVehicleView(
    PermissionRequiredMixin, LoginRequiredMixin, generic.UpdateView
):
    """
    Es una vista de Django para eliminar un objeto "Vehicle" de la base de datos y configurar su
    campo "visible" como falso. Se requiere que el usuario tenga ciertos permisos y esté
    autenticado para acceder a la vista, y se utiliza una plantilla específica y una ruta de éxito.
    El método "form_valid" se utiliza para guardar el objeto modificado y se retorna una respuesta
    HTTP con el código de estado 204 y una cabecera personalizada para actualizar la lista de
    vehículos.
    """

    model = Vehicle
    template_name = "realtime/vehicles/delete_vehicle.html"
    permission_required = "realtime.delete_vehicle"
    success_url = reverse_lazy("realtime:list_vehicles_created")
    fields = ["visible"]

    def get_success_url(self):
        # Asegúrate de que el nombre de la URL sea correcto y esté definido en tus archivos de URL.
        return reverse("realtime:vehicles")

    def form_valid(self, form):
        # Obtener el objeto Vehicle que se va a eliminar
        vehicle = form.instance

        # Guardar referencias a la Licencia y el dispositivo/imei del vehículo
        license_to_reuse = vehicle.license
        device_to_reuse = vehicle.device

        # Configurar el campo "visible" como falso para eliminar el vehículo
        vehicle.visible = False
        vehicle.is_active = False  # Cambiar el estado del vehículo a inactivo
        vehicle.device_id = None  # Limpiar el campo de dispositivo
        vehicle.modified_by = self.request.user
        vehicle.save()

        # Asignar la Licencia y el dispositivo/imei a otro vehículo, si es necesario
        # Por ejemplo, si deseas asignarlos al primer vehículo disponible
        # Puedes ajustar esta lógica según tus necesidades específicas
        if license_to_reuse and device_to_reuse:
            # Encuentra el primer vehículo disponible
            new_vehicle = Vehicle.objects.filter(
                license__isnull=True, device__isnull=True
            ).first()
            if new_vehicle:
                new_vehicle.license = license_to_reuse
                new_vehicle.device = device_to_reuse
                new_vehicle.save()

        page_update = HttpResponse(
            ""
        )  # O puedes enviar algún contenido si es necesario.
        page_update["HX-Redirect"] = self.get_success_url()
        return page_update


class ListVehicleGroupTemplate(
    PermissionRequiredMixin, LoginRequiredMixin, generic.TemplateView
):
    """
    La clase ListVehicleTemplate es una vista que requiere permisos y autenticación, y que
    renderiza un template HTML para mostrar una lista de vehículos. la propiedad
    permission_required: Esta propiedad especifica el permiso requerido para acceder a la vista.
    """

    template_name = "realtime/group_vehicles/main_group_vehicles.html"
    permission_required = "realtime.view_vehiclegroup"


class ListVehiclesGroupView(
    PermissionRequiredMixin, LoginRequiredMixin, generic.ListView
):
    """
    Este código define una vista de Django para listar los objetos "Vehicle" en la base de datos.
    La vista requiere que el usuario tenga ciertos permisos y esté autenticado para acceder a ella.
    Se agrega una lista de vehículos visibles y pertenecientes a la compañía del usuario al
    contexto de la plantilla y se devuelve un queryset de todos los vehículos pertenecientes a la
    compañía del usuario.
    """

    template_name = "realtime/group_vehicles/list_group_vehicles_created.html"
    context_object_name = "list_group"
    permission_required = "realtime.view_vehiclegroup"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Crear una lista para almacenar las tuplas de grupo y conteo de vehículos
        group_and_vehicle_count = []
        # Iterar sobre la lista de grupos
        Groups = ListVehicleGroupsByCompany(self.request.user.company_id)

        for group_data in Groups:
            group_name = group_data["VehicleGroup"]
            vehicle_count = group_data["VehicleCount"]

            # Busca la instancia de VehicleGroup por su nombre
            group_instance = VehicleGroup.objects.get(name=group_name, visible=True)

            # Agrega la tupla a la lista usando la instancia y el recuento de vehículos
            group_and_vehicle_count.append((group_instance, vehicle_count))

        # Agrega la lista de tuplas al contexto
        context["group_and_vehicle_count"] = group_and_vehicle_count
        return context

    def get_queryset(self):
        return


class AddVehicleGroupView(
    PermissionRequiredMixin, LoginRequiredMixin, generic.CreateView
):

    """
    Este código define una vista de Django para agregar un objeto "Vehicle" a la base de datos.
    Se requiere que el usuario tenga ciertos permisos y esté autenticado para acceder a la vista.
    La vista agrega datos adicionales al formulario y devuelve una respuesta HTTP con el código de
    estado 204 y una cabecera personalizada para actualizar la lista de vehículos.
    """

    template_name = "realtime/group_vehicles/add_group_vehicles.html"
    permission_required = "realtime.add_vehiclegroup"
    form_class = VehicleGroupForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_vehicles = get_user_vehicles(
            self.request.user.company_id, self.request.user
        )
        if self.request.user.company_id == 1:
            context["form"].fields["vehicles"].queryset = Vehicle.objects.filter(
                visible=True, is_active=True
            )
        else:
            # Filtrar los vehículos basados en los identificadores de user_vehicles
            queryset = Vehicle.objects.filter(
                Q(company__provider_id=self.request.user.company_id)
                | Q(company_id=self.request.user.company_id),
                visible=True,
                is_active=True,
                license__in=[tupla[1] for tupla in user_vehicles],
            ).distinct()
            context["form"].fields["vehicles"].queryset = queryset
        return context

    def form_valid(self, form):
        vehicle_group = form.save(
            commit=False
        )  # Guarda la instancia sin aplicar aún la relación ManyToMany
        vehicle_group.modified_by = self.request.user
        vehicle_group.created_by = self.request.user
        vehicle_group.save()  # Primero se guarda el objeto para obtener un ID

        form.save_m2m()  # Ahora se pueden guardar las relaciones ManyToMany

        return HttpResponse(status=204, headers={"HX-Trigger": "ListgroupChanged"})
    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data(form=form))


class UpdateVehicleGroupView(
    PermissionRequiredMixin, LoginRequiredMixin, generic.UpdateView
):
    model = VehicleGroup
    template_name = "realtime/group_vehicles/update_group_vehicles.html"
    permission_required = "realtime.change_vehiclegroup"
    form_class = VehicleGroupForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_vehicles = get_user_vehicles(
            self.request.user.company_id, self.request.user
        )
        if self.request.user.company_id == 1:
            context["form"].fields["vehicles"].queryset = Vehicle.objects.filter(
                visible=True, is_active=True
            )
        else:
            queryset = Vehicle.objects.filter(
                Q(company__provider_id=self.request.user.company_id)
                | Q(company_id=self.request.user.company_id),
                visible=True,
                is_active=True,
                license__in=[tupla[1] for tupla in user_vehicles],
            ).distinct()
            context["form"].fields["vehicles"].queryset = queryset
        return context

    def form_valid(self, form):
        vehicle = form.save(commit=False)
        vehicle.modified_by = self.request.user
        vehicle.save()
        form.save_m2m()
        return HttpResponse(status=204, headers={"HX-Trigger": "ListgroupChanged"})
    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data(form=form))

class DeleteVehicleGroupView(
    PermissionRequiredMixin, LoginRequiredMixin, generic.UpdateView
):
    """
    Es una vista de Django para eliminar un objeto "Vehicle" de la base de datos y configurar su
    campo "visible" como falso. Se requiere que el usuario tenga ciertos permisos y esté
    autenticado para acceder a la vista, y se utiliza una plantilla específica y una ruta de éxito.
    El método "form_valid" se utiliza para guardar el objeto modificado y se retorna una respuesta
    HTTP con el código de estado 204 y una cabecera personalizada para actualizar la lista de
    vehículos.
    """

    model = VehicleGroup
    template_name = "realtime/group_vehicles/delete_group_vehicles.html"
    permission_required = "realtime.delete_vehiclegroup"
    success_url = reverse_lazy("realtime:list_group_vehicles_created")
    fields = ["visible"]

    def form_valid(self, form):
        vehicle = form.save(commit=False)
        vehicle.modified_by = self.request.user
        vehicle.visible = False
        vehicle.save()

        return HttpResponse(status=204, headers={"HX-Trigger": "ListgroupChanged"})


class VehicleListAPIView(generics.ListAPIView):
    serializer_class = VehicleSerializer

    def get_queryset(self):
        company_id = self.kwargs["company_id"]
        company = get_object_or_404(Company, id=company_id)
        return Vehicle.objects.filter(company=company, visible=True)


class ListSendingCommandsTemplate(
    PermissionRequiredMixin, LoginRequiredMixin, generic.ListView
):
    """
    Vista de lista para mostrar los comandos de envío.

    Esta vista muestra una lista de comandos de envío y aplica permisos de usuario
    y autenticación para acceder a ella.

    Atributos:
        model (Model): El modelo de datos utilizado para la vista.
        template_name (str): El nombre de la plantilla HTML utilizada para renderizar la vista.
        permission_required (str): El permiso requerido para acceder a la vista.
    """

    model = Sending_Commands
    template_name = "realtime/sending_commands/main_sending_commands.html"
    permission_required = "realtime.view_sending_commands"

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
        company = user.company_id
        return fetch_all_sending_commands(company, user.id)

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


class AddSendingCommandsView(
    PermissionRequiredMixin, LoginRequiredMixin, generic.CreateView
):
    """
    Vista de creación para agregar comandos de envío.

    Esta vista permite a los usuarios con los permisos adecuados agregar comandos de envío.
    Los comandos de envío se crean a partir de un formulario y se guardan en la base de datos.

    Atributos:
        model (Model): El modelo de datos utilizado para crear los comandos de envío.
        template_name (str): El nombre de la plantilla HTML utilizada para mostrar el formulario de
        creación.
        permission_required (str): El permiso requerido para acceder a esta vista.
        form_class (Form): La clase de formulario utilizada para crear los comandos de envío.
        success_url (str): La URL a la que se redirige después de que se haya guardado
        correctamente un comando de envío.

    Métodos:
        get_context_data(**kwargs): Obtiene los datos del contexto para mostrar en la plantilla.
        form_valid(form): Guarda el comando de envío en la base de datos y devuelve una respuesta
        HTTP.

    """

    model = Sending_Commands
    template_name = "realtime/sending_commands/add_sending_commands.html"
    permission_required = "realtime.add_sending_commands"
    form_class = SendingCommandsFrom
    success_url = "/realtime/Commands"

    def get_success_url(self):
        # Asegúrate de que el nombre de la URL sea correcto y esté definido en tus archivos de URL.
        return reverse("realtime:commands")

    def form_valid(self, form):
        """
        Guarda el comando de envío en la base de datos y devuelve una respuesta HTTP.

        Este método se llama cuando el formulario es válido y se va a guardar.
        Asigna el usuario actual como el creador del comando de envío y guarda el comando en la
        base de datos.
        Devuelve una respuesta HTTP con un código de estado 204 (Sin contenido) y un encabezado
        HX-Trigger para indicar que la lista de comandos de envío ha cambiado.

        Args:
            form (Form): El formulario válido.

        Returns:
            HttpResponse: Una respuesta HTTP con un código de estado 204 y un encabezado HX-Trigger

        """

        Commands = form.save(commit=False)
        Commands.created_by = self.request.user
        Commands.save()

        page_update = HttpResponse(
            ""
        )  # O puedes enviar algún contenido si es necesario.
        page_update["HX-Redirect"] = self.get_success_url()
        return page_update

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()

        kwargs["company_id"] = self.request.user.company_id
        kwargs["user"] = self.request.user

        return kwargs


class ListResponseCommandsTemplate(LoginRequiredMixin, generic.ListView):

    """
    Vista como clase que renderiza el template HTML que contiene el lsitado de comando enviados
    """

    model = Command_response
    template_name = "realtime/response_commands/main_response_commands.html"

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
        company = user.company_id
        return fetch_all_response_commands(company, user.id)

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


class ApiGeozonesView(LoginRequiredMixin, generic.TemplateView):
    """
    A class-based view that displays a list of geozones.
    It requires the 'realtime.view_geozones' permission and filters geozones by the company of the
    currently authenticated user.
    """

    template_name = "realtime/geozones/API_geozone.html"


class GeozoneListCreateAPIView(generics.ListCreateAPIView):
    queryset = Geozones.objects.all()
    serializer_class = GeozonesSerializer


class GeozoneRetrieveUpdateAPIView(generics.RetrieveUpdateAPIView):
    queryset = Geozones.objects.all()
    serializer_class = GeozonesSerializer


class GeozonesListAPIView(generics.ListAPIView):
    serializer_class = GeozonesSerializer

    def get_queryset(self):
        company_id = self.kwargs["company_id"]
        return Geozones.objects.filter(company_id=company_id)


class ListGeozonesTemplate(
    PermissionRequiredMixin, LoginRequiredMixin, generic.ListView
):
    """
    Vista como clase que renderiza el template HTML que contiene la lista de planes de datos.
    """

    model = Geozones
    template_name = "realtime/geozones/main_geozone.html"
    permission_required = "realtime.view_geozones"

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
        user_company_id = self.request.user.company_id
        return fetch_all_geozones(user_company_id, user.id)

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


class ListGeozonesView(PermissionRequiredMixin, LoginRequiredMixin, generic.ListView):
    """
    Este código define una vista de clase que muestra los planes de datos creados, permitiendo la
    edición y adición. Requiere que el usuario tenga el permiso 'realtime.view_dataplan'.
    La lista de planes de datos se filtra para mostrar solo los planes pertenecientes a la
    compañía del usuario actualmente autenticado.
    """

    template_name = "realtime/geozones/list_geozone_created.html"
    context_object_name = "list_geozone"
    login_url = "login"
    success_url = reverse_lazy("index")
    permission_required = "realtime.view_geozones"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        user_company_id = self.request.user.company_id
        list_geozone = fetch_all_geozones(user_company_id, user.id)
        # Usa la función personalizada para obtener las geozonas
        context["list_geozone"] = list_geozone
        return context

    def get_queryset(self):
        return Geozones.objects.filter(company=self.request.user.company_id)


class AddGeozonesView(PermissionRequiredMixin, LoginRequiredMixin, generic.CreateView):
    """ """

    template_name = "realtime/geozones/add_geozone.html"
    permission_required = "realtime.add_geozones"
    success_url = reverse_lazy("index")
    login_url = reverse_lazy("index")
    form_class = GeozonesForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
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

    def get_success_url(self):
        # Asegúrate de que el nombre de la URL sea correcto y esté definido en tus archivos de URL.
        return reverse("realtime:geozones")

    def form_valid(self, form):
        save = form.save(commit=False)
        save.created_by = self.request.user
        save.modified_by = self.request.user
        save.save()
        response = HttpResponse("")  # O puedes enviar algún contenido si es necesario.
        response["HX-Redirect"] = self.get_success_url()
        return response


class UpdateGeozonesView(
    PermissionRequiredMixin, LoginRequiredMixin, generic.UpdateView
):
    model = Geozones
    template_name = "realtime/geozones/update_geozone.html"
    login_url = reverse_lazy("login")
    permission_required = "realtime.change_geozones"
    success_url = reverse_lazy("login")
    form_class = GeozonesForm

    def get_initial(self):
        initial = super().get_initial()
        # Obtener el ID desde los kwargs del URL
        geozone_id = self.kwargs.get("pk")
        # Utilizar la función para obtener los datos de la geozone
        geozone_data = get_geozone_by_id(geozone_id)
        if geozone_data:
            initial.update(geozone_data)
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
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
        # Asegúrate de que la instancia del formulario se guarda correctamente
        self.object = form.save(commit=False)
        self.object.modified_by = (
            self.request.user
        )  # Actualizar el usuario que modificó
        self.object.save()
        response = HttpResponse("")  # O puedes enviar algún contenido si es necesario.
        response["HX-Redirect"] = self.get_success_url()
        return response


class DeleteGeozonesView(LoginRequiredMixin, generic.UpdateView):
    """ """

    model = VehicleGroup
    template_name = "realtime/group_vehicles/delete_group_vehicles.html"
    success_url = reverse_lazy("realtime:list_group_vehicles_created")
    fields = ["visible"]

    def form_valid(self, form):
        vehicle = form.save(commit=False)
        vehicle.visible = False
        vehicle.save()
        return HttpResponse(status=204, headers={"HX-Trigger": "ListgroupChanged"})


class ConfigurationReportView(
    PermissionRequiredMixin, LoginRequiredMixin, TemplateView
):
    model = Io_items_report
    template_name = "realtime/custom_report/add_configuration_report.html"
    permission_required = "realtime.view_io_items_report"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
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
        companies = list(companies)
        companies.sort(key=lambda x: x.company_name)

        context["companies"] = companies

        return context


class UpdateConfigurationReportView(View):
    template_name = "realtime/custom_report/update_configuration_report.html"
    permission_required = "realtime.add_io_items_report"

    def get(self, request, company_id, *args, **kwargs):
        # Obtener o crear una instancia de Io_elements para la compañía actual
        instance, created = Io_items_report.objects.get_or_create(company_id=company_id)

        # Cargar la información de instance.info_widgets si está presente, de lo contrario, asignar una lista vacía
        selected_widgets = json.loads(instance.info_widgets)

        # Cargar la información de instance.info_reports si está presente, de lo contrario, asignar una lista vacía
        selected_reports = json.loads(instance.info_reports)

        # Obtener los datos de Last_Avl para la compañía actual
        last_avls = Last_Avl.objects.filter(company=company_id)
        # Crear un conjunto para almacenar eventos únicos
        unique_events = set()
        # Iterar sobre los registros de Last_Avl y agregar eventos únicos al conjunto
        for avl in last_avls:
            info_events = avl.info_events
            if info_events:
                info_events_dict = json.loads(info_events)
                unique_events.update(info_events_dict.keys())
            # Procesar status_events y agregar eventos únicos al conjunto
            status_events = avl.status_events
            if status_events:
                # Convertir status_events de string a lista de Python
                status_events_list = json.loads(status_events)
                # Eliminar la última palabra de cada evento y agregarlo al conjunto
                processed_events = {
                    event.rsplit(" ", 1)[0] for event in status_events_list
                }
                unique_events.update(processed_events)

        # Actualizar info_io con unique_events sin duplicados y sin reemplazar los existentes
        existing_events = json.loads(instance.info_io) if instance.info_io else []
        updated_events = list(set(existing_events + list(unique_events)))
        instance.info_io = json.dumps(updated_events)
        unique_events.update(updated_events)

        # Guardar la instancia
        instance.save()

        # Crear la lista de opciones para los campos widgets y reports
        widget_choices = []
        report_choices = []

        # Iterar sobre selected_widgets para mantener el orden deseado
        for event in selected_widgets:
            if event in unique_events:
                widget_choices.append((event, event, True))
            else:
                widget_choices.append((event, event, False))
        # Iterar sobre unique_events para asegurar que todos los eventos estén incluidos
        for event in unique_events:
            if event not in selected_widgets:
                widget_choices.append((event, event, False))

        # Repetir el mismo proceso para selected_reports
        for event in selected_reports:
            if event in unique_events:
                report_choices.append((event, event, True))
            else:
                report_choices.append((event, event, False))

        for event in unique_events:
            if event not in selected_reports:
                report_choices.append((event, event, False))

        # Crear el formulario con la instancia existente y las opciones de la lista
        form = ConfigurationReport(
            instance=instance,
            company_id=company_id,
            initial={"widgets": selected_widgets, "reports": selected_reports},
        )

        context = {
            "form": form,
            "widget_choices": widget_choices,
            "report_choices": report_choices,
            "company_name": Company.objects.get(id=company_id).company_name,
        }

        return render(request, self.template_name, context)

    def post(self, request, company_id, *args, **kwargs):
        # Obtener o crear una instancia de Io_elements para la compañía actual
        instance, created = Io_items_report.objects.get_or_create(company_id=company_id)
        company_name = Company.objects.get(id=company_id).company_name
        # Procesar los datos del formulario
        widgets = request.POST.getlist("widgets")
        reports = request.POST.getlist("reports")

        # Convertir las listas de widgets y reports a JSON
        widgets_json = json.dumps(widgets)
        reports_json = json.dumps(reports)

        # Asignar los datos al modelo Io_elements
        instance.info_widgets = widgets_json
        instance.info_reports = reports_json

        # Guardar la instancia
        instance.save()

        messages.success(request, f"{company_name}")
        return redirect("realtime:add_configuration_report")
