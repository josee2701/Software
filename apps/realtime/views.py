import json
from datetime import datetime

from django.contrib import messages
from django.contrib.auth.mixins import (LoginRequiredMixin,
                                        PermissionRequiredMixin)
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views import View, generic
from django.views.decorators.csrf import csrf_protect
from django.views.generic import ListView, TemplateView

from apps.log.mixins import (CreateAuditLogAsyncMixin,
                             DeleteAuditLogAsyncMixin,
                             UpdateAuditLogAsyncMixin, UpdateAuditLogSyncMixin)
from apps.realtime.forms import (DataPlanForm, DeviceForm, SimcardForm,
                                 VehicleForm, VehicleGroupForm)
from apps.realtime.models import (DataPlan, Device, FamilyModelUEC,
                                  Manufacture, SimCard, Vehicle, VehicleGroup)
from apps.whitelabel.models import Company
from config.filtro import General_Filters
from config.pagination import get_paginate_by

from .apis import (extract_number, get_user_companies, get_user_vehicles,
                   sort_key, sort_key_commands_datetime)
from .forms import (ConfigurationReport, DataPlanForm, DeviceForm,
                    GeozonesForm, SendingCommandsFrom, SimcardForm,
                    VehicleForm, VehicleGroupForm)
from .models import (Command_response, DataPlan, Device, FamilyModelUEC,
                     Geozones, Io_items_report, Last_Avl, Manufacture,
                     Sending_Commands, SimCard, Types_assets, Vehicle,
                     VehicleGroup)
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
        Obtiene el conjunto de datos de los comandos de envío filtrados y ordenados.

        Returns:
            QuerySet: El conjunto de datos de los comandos de envío filtrados y ordenados.
        """
        user = self.request.user
        return General_Filters.get_filtered_data(DataPlan, user).order_by("company")

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


class AddDataPlanView(
    PermissionRequiredMixin,
    LoginRequiredMixin,
    CreateAuditLogAsyncMixin,
    generic.CreateView,
):
    """
    Vista para agregar un nuevo plan de datos.
    """

    model = DataPlan
    template_name = "realtime/dataplan/add_dataplan.html"
    permission_required = "realtime.add_dataplan"
    form_class = DataPlanForm
    success_url = reverse_lazy("realtime:list_dataplan_created")

    def get_success_url(self):
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
        dataplan.created_by = self.request.user
        dataplan.save()

        # Llama al método form_valid de la clase padre para registrar la acción en el log de auditoría
        response = super().form_valid(form)

        # Prepara una respuesta con redirección usando HTMX
        if self.request.htmx:
            return HttpResponse(headers={"HX-Redirect": self.get_success_url()})
        else:
            return response


class UpdateDataPlanView(
    PermissionRequiredMixin,
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


class DeleteDataPlanView(
    PermissionRequiredMixin,
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

    model = DataPlan
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


class ListSimcardTemplate(
    PermissionRequiredMixin, LoginRequiredMixin, ListView
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
        paginate_by = self.request.POST.get('paginate_by', None)  # Obtener paginate_by de los parámetros POST

        if paginate_by is None:
            session_filters = self.request.session.get(
                f"filters_sorted_simcard_{self.request.user.id}", {}
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
            if f"filters_sorted_simcard_{user.id}" in self.request.session:
                del self.request.session[f"filters_sorted_simcard_{user.id}"]
                self.request.session.modified = True
        # Recuperar filtros almacenados en la sesión
        session_filters = self.request.session.get(f'filters_sorted_simcard_{user.id}', {})
        order_by = params.get('order_by', session_filters.get('order_by', ['Company'])[0])
        direction = params.get('direction', session_filters.get('direction',['asc'])[0])
        # Actualizar los filtros con los parámetros actuales de la solicitud GET
        session_filters.update(params)
        # Actualizar los filtros de la sesión con los nuevos parámetros
        self.request.session[
            f"filters_sorted_simcard_{user.id}"
        ] = session_filters
        self.request.session.modified = True
        queryset = fetch_all_simcards(company, user, search)
        # Función para convertir los valores a minúsculas y extraer números cuando sea necesario
        key_function = sort_key(order_by)
        reverse = direction == 'desc'
        try:
            sorted_queryset = sorted(queryset, key=key_function, reverse=reverse)
        except KeyError:
            # Ordenamiento por defecto si la clave no existe
            sorted_queryset = sorted(
                queryset, key=lambda x: x["Company"].lower(), reverse=reverse
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
        session_filters = self.request.session.get(f'filters_sorted_simcard_{self.request.user.id}', {})
        # Obtener el ordenamiento desde la solicitud actual
        order_by = self.request.GET.get('order_by') or self.request.POST.get('order_by') or session_filters.get('order_by', ['Company'])[0]
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


class AddSimcardView(
    PermissionRequiredMixin,
    LoginRequiredMixin,
    CreateAuditLogAsyncMixin,
    generic.CreateView,
):
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
        user = self.request.user
        companies = get_user_companies(user)
        if user.company_id == 1:
            context["form"].fields["company"].choices = companies
        else:
            context["form"].fields["company"].queryset = companies
        context["simcard"] = user_company
        button_color = self.request.user.company.theme_set.all().first().button_color
        context["button_color"] = button_color
        return context

    def form_valid(self, form):
        # form.clean_activate_date()
        form.instance.modified_by = self.request.user
        form.instance.created_by = self.request.user
        form.save()
        # Llama al método form_valid de la clase padre para registrar la acción en el log de auditoría
        response = super().form_valid(form)

        # Prepara una respuesta con redirección usando HTMX
        page_update = HttpResponse("")
        page_update["HX-Redirect"] = self.get_success_url()
        return page_update


class UpdateSimcardView(
    PermissionRequiredMixin,
    LoginRequiredMixin,
    UpdateAuditLogAsyncMixin,
    generic.UpdateView,
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
        user = self.request.user
        companies = get_user_companies(user)
        if user.company_id == 1:
            context["form"].fields["company"].choices = companies
        else:
            context["form"].fields["company"].queryset = companies
        context["simcard"] = user_company
        button_color = self.request.user.company.theme_set.all().first().button_color
        context["button_color"] = button_color
        return context

    def form_valid(self, form):
        # form.clean_activate_date()
        form.instance.modified_by = self.request.user
        form.save()
        # Llama al método form_valid de la clase padre para registrar la acción en el log de auditoría
        response = super().form_valid(form)

        # Prepara una respuesta con redirección usando HTMX
        page_update = HttpResponse("")
        page_update["HX-Redirect"] = self.get_success_url()
        return page_update

    def form_invalid(self, form):
        return super().form_invalid(form)


class DeleteSimcardView(
    PermissionRequiredMixin,
    LoginRequiredMixin,
    DeleteAuditLogAsyncMixin,
    generic.UpdateView,
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

        # Llama al método form_valid de la clase padre para registrar la acción en el log de auditoría
        response = super().form_valid(form)

        # Prepara una respuesta con redirección usando HTMX
        page_update = HttpResponse("")
        page_update["HX-Redirect"] = self.get_success_url()
        return page_update


class ListDeviceTemplate(PermissionRequiredMixin, LoginRequiredMixin, ListView):
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
        paginate_by = self.request.POST.get('paginate_by', None)  # Obtener paginate_by de los parámetros POST

        if paginate_by is None:
            session_filters = self.request.session.get(
                f"filters_sorted_device_{self.request.user.id}", {}
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
        params = self.request.GET if self.request.method == 'GET' else self.request.POST
        query = params.get("query", "").lower()
        search = params.get("q", query).lower()
        if 'order_by' not in params and 'paginate_by' not in params and 'page' not in params:
            # Limpiar los filtros de la sesión
            if f"filters_sorted_device_{user.id}" in self.request.session:
                del self.request.session[f"filters_sorted_device_{user.id}"]
                self.request.session.modified = True
        # Recuperar filtros almacenados en la sesión
        session_filters = self.request.session.get(f'filters_sorted_device_{user.id}', {})
        order_by = params.get('order_by', session_filters.get('order_by', ['company'])[0])
        direction = params.get('direction', session_filters.get('direction',['asc'])[0])
        # Actualizar los filtros con los parámetros actuales de la solicitud GET
        session_filters.update(params)
        # Actualizar los filtros de la sesión con los nuevos parámetros
        self.request.session[
            f"filters_sorted_device_{user.id}"
        ] = session_filters
        self.request.session.modified = True
        devices = ListDeviceByCompany(user.company_id, user.id, str(search))
        # Función para convertir los valores a minúsculas y extraer números cuando sea necesario
        key_function = sort_key(order_by)
        reverse = direction == 'desc'
        try:
            sorted_queryset = sorted(devices, key=key_function, reverse=reverse)
        except KeyError:
            # Ordenamiento por defecto si la clave no existe
            sorted_queryset = sorted(
                devices, key=lambda x: x["company"].lower(), reverse=reverse
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
        session_filters = self.request.session.get(f'filters_sorted_device_{self.request.user.id}', {})
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


class AddDeviceView(
    PermissionRequiredMixin,
    LoginRequiredMixin,
    CreateAuditLogAsyncMixin,
    generic.CreateView,
):
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
        user = self.request.user
        companies = get_user_companies(user)
        if user.company_id == 1:
            context["form"].fields["company"].choices = companies
        else:
            context["form"].fields["company"].queryset = companies
        
        context["form"].fields["familymodel"].queryset=FamilyModelUEC.objects.none()
        
        manufactures = Manufacture.objects.all()
        selected_model = self.request.POST.get("model")
        int_selected_model = None
        if selected_model is not None:
            int_selected_model = int(selected_model)
        context.update(
            {
                "manufactures": manufactures,
                "selected_model": int_selected_model,
            }
        )
        button_color = self.request.user.company.theme_set.all().first().button_color
        context["button_color"] = button_color
        return context

    def form_valid(self, form):
        form.instance.modified_by = self.request.user
        form.instance.created_by = self.request.user

        form.save()

        # Llama al método form_valid de la clase padre para registrar la acción en el log de auditoría
        response = super().form_valid(form)

        # Prepara una respuesta con redirección usando HTMX
        page_update = HttpResponse("")
        page_update["HX-Redirect"] = self.get_success_url()
        return page_update

    def form_invalid(self, form):
        # Manejo personalizado de errores del formulario
        return self.render_to_response(self.get_context_data(form=form))


class UpdateDeviceView(
    PermissionRequiredMixin,
    LoginRequiredMixin,
    UpdateAuditLogAsyncMixin,
    generic.UpdateView,
):
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
        user = self.request.user
        companies = get_user_companies(user)
        if user.company_id == 1:
            context["form"].fields["company"].choices = companies
        else:
            context["form"].fields["company"].queryset = companies
        manufactures = Manufacture.objects.all()
        context.update(
            {
                "manufactures": manufactures,
            }
        )
        button_color = self.request.user.company.theme_set.all().first().button_color
        context["button_color"] = button_color
        return context

    def form_valid(self, form):
        form.instance.modified_by = self.request.user
        form.save()
        # Llama al método form_valid de la clase padre para registrar la acción en el log de auditoría
        response = super().form_valid(form)

        # Prepara una respuesta con redirección usando HTMX
        page_update = HttpResponse("")
        page_update["HX-Redirect"] = self.get_success_url()
        return page_update

    def form_invalid(self, form):
        # Manejo personalizado de errores del formulario
        return self.render_to_response(self.get_context_data(form=form))


class DeleteDeviceView(
    PermissionRequiredMixin,
    LoginRequiredMixin,
    DeleteAuditLogAsyncMixin,
    generic.UpdateView,
):
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

        # Llama al método form_valid de la clase padre para registrar la acción en el log de auditoría
        response = super().form_valid(form)

        # Prepara una respuesta con redirección usando HTMX
        page_update = HttpResponse("")
        page_update["HX-Redirect"] = self.get_success_url()
        return page_update


class ListVehicleTemplate(
    PermissionRequiredMixin, LoginRequiredMixin, ListView
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
        paginate_by = self.request.POST.get('paginate_by', None)  # Obtener paginate_by de los parámetros POST

        if paginate_by is None:
            session_filters = self.request.session.get(
                f"filters_sorted_vehicle_{self.request.user.id}", {}
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
        params = self.request.GET if self.request.method == 'GET' else self.request.POST
        query = params.get("query", "").lower()
        search = params.get("q", query).lower()
        if 'order_by' not in params and 'paginate_by' not in params and 'page' not in params:
            # Limpiar los filtros de la sesión
            if f"filters_sorted_vehicle_{user.id}" in self.request.session:
                del self.request.session[f"filters_sorted_vehicle_{user.id}"]
                self.request.session.modified = True
        # Recuperar filtros almacenados en la sesión
        session_filters = self.request.session.get(f'filters_sorted_vehicle_{user.id}', {})
        order_by = params.get('order_by', session_filters.get('order_by', ['company'])[0])
        direction = params.get('direction', session_filters.get('direction',['asc'])[0])
        # Actualizar los filtros con los parámetros actuales de la solicitud GET
        session_filters.update(params)
        # Actualizar los filtros de la sesión con los nuevos parámetros
        self.request.session[
            f"filters_sorted_vehicle_{user.id}"
        ] = session_filters
        self.request.session.modified = True
        # Obtener los planes de datos a través de la función fetch_all_dataplan.
        vehicles = ListVehicleByUserAndCompany(
            self.request.user.company_id, self.request.user.id, str(search)
        )

        # Función para convertir los valores a minúsculas y extraer números cuando sea necesario
        key_function = sort_key(order_by)
        reverse = direction == 'desc'
        try:
            sorted_queryset = sorted(vehicles, key=key_function, reverse=reverse)
        except KeyError:
            # Ordenamiento por defecto si la clave no existe
            sorted_queryset = sorted(
                vehicles, key=lambda x: x["company"].lower(), reverse=reverse
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
        session_filters = self.request.session.get(f'filters_sorted_vehicle_{self.request.user.id}', {})
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


class AddVehicleView(
    PermissionRequiredMixin,
    LoginRequiredMixin,
    CreateAuditLogAsyncMixin,
    generic.CreateView,
):

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

        user = self.request.user
        companies = get_user_companies(user)
        if user.company_id == 1:
            context["form"].fields["company"].choices = companies
        else:
            context["form"].fields["company"].queryset = companies
        context["types_assets"] = Types_assets.objects.all()
        button_color = self.request.user.company.theme_set.all().first().button_color
        context["button_color"] = button_color

        return context

    def form_valid(self, form):
        vehicle = form.save(commit=False)
        vehicle.modified_by = self.request.user
        vehicle.created_by = self.request.user
        vehicle.is_active = True
        vehicle.icon = form.cleaned_data["icon"]
        vehicle.save()
        # Llama al método form_valid de la clase padre para registrar la acción en el log de auditoría
        response = super().form_valid(form)

        # Prepara una respuesta con redirección usando HTMX
        page_update = HttpResponse("")
        page_update["HX-Redirect"] = self.get_success_url()
        return page_update


class UpdateVehicleView(
    PermissionRequiredMixin,
    LoginRequiredMixin,
    UpdateAuditLogAsyncMixin,
    generic.UpdateView,
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
        user = self.request.user
        companies = get_user_companies(user)
        if user.company_id == 1:
            context["form"].fields["company"].choices = companies
        else:
            context["form"].fields["company"].queryset = companies
        assigned_devices = Device.objects.filter(vehicle=user_vehicle).values_list(
            "pk", flat=True
        )
        context["types_assets"] = Types_assets.objects.all()

        context["initial_vehicle_type"] = (
            user_vehicle.vehicle_type if user_vehicle.vehicle_type else ""
        )
        context["initial_brand"] = user_vehicle.brand if user_vehicle.brand else ""
        context["initial_line"] = user_vehicle.line if user_vehicle.line else ""

        context["form"].initial["icon"] = user_vehicle.icon
        context["button_color"] = (
            self.request.user.company.theme_set.all().first().button_color
        )
        return context

    def form_valid(self, form):
        vehicle = form.save(commit=False)
        vehicle.modified_by = self.request.user
        vehicle.icon = form.cleaned_data["icon"]
        vehicle.asset_type = form.cleaned_data["asset_type"]
        vehicle.save()
        # Llama al método form_valid de la clase padre para registrar la acción en el log de auditoría
        response = super().form_valid(form)

        # Prepara una respuesta con redirección usando HTMX
        page_update = HttpResponse("")
        page_update["HX-Redirect"] = self.get_success_url()
        return page_update


class DeleteVehicleView(
    PermissionRequiredMixin,
    LoginRequiredMixin,
    DeleteAuditLogAsyncMixin,
    generic.UpdateView,
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

        # Llama al método form_valid de la clase padre para registrar la acción en el log de auditoría
        response = super().form_valid(form)

        # Prepara una respuesta con redirección usando HTMX
        page_update = HttpResponse("")
        page_update["HX-Redirect"] = self.get_success_url()
        return page_update


class ListVehicleGroupTemplate(
    PermissionRequiredMixin, LoginRequiredMixin, ListView
):
    """
    La clase ListVehicleTemplate es una vista que requiere permisos y autenticación, y que
    renderiza un template HTML para mostrar una lista de vehículos. la propiedad
    permission_required: Esta propiedad especifica el permiso requerido para acceder a la vista.
    """

    template_name = "realtime/group_vehicles/main_group_vehicles.html"
    context_object_name = "list_group"
    permission_required = "realtime.view_vehiclegroup"
    paginate_by = 10  # Número de elementos por página

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
                f"filters_sorted_vehiclegroup_{self.request.user.id}", {}
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
        params = self.request.GET if self.request.method == 'GET' else self.request.POST
        query = params.get("query", "").lower()
        search = params.get("q", query).lower()
        if 'order_by' not in params and 'paginate_by' not in params and 'page' not in params:
            # Limpiar los filtros de la sesión
            if f"filters_sorted_vehiclegroup_{user.id}" in self.request.session:
                del self.request.session[f"filters_sorted_vehiclegroup_{user.id}"]
                self.request.session.modified = True
        # Recuperar filtros almacenados en la sesión
        session_filters = self.request.session.get(f'filters_sorted_vehiclegroup_{user.id}', {})
        order_by = params.get('order_by', session_filters.get('order_by', ['name'])[0])
        direction = params.get('direction', session_filters.get('direction',['asc'])[0])
        # Actualizar los filtros con los parámetros actuales de la solicitud GET
        session_filters.update(params)
        # Actualizar los filtros de la sesión con los nuevos parámetros
        self.request.session[
            f"filters_sorted_vehiclegroup_{user.id}"
        ] = session_filters
        self.request.session.modified = True
        groups = ListVehicleGroupsByCompany(self.request.user.company_id, search)
        # Función para convertir los valores a minúsculas y extraer números cuando sea necesario
        key_function = sort_key(order_by)
        reverse = direction == 'desc'
        try:
            sorted_queryset = sorted(groups, key=key_function, reverse=reverse)
        except KeyError:
            # Ordenamiento por defecto si la clave no existe
            sorted_queryset = sorted(
                groups, key=lambda x: x["name"].lower(), reverse=reverse
            )

        return sorted_queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        group_and_vehicle_count = self.get_queryset()

        # Paginación
        paginator = Paginator(group_and_vehicle_count, self.get_paginate_by(None))
        session_filters = self.request.session.get(f'filters_sorted_vehiclegroup_{self.request.user.id}', {})
        page = self.request.GET.get('page', session_filters.get('page', [1]))[0]
        page_obj = paginator.get_page(page)
        paginate_by = self.get_paginate_by(None)
        context["group_and_vehicle_count"] = page_obj
        context["page_obj"] = page_obj
        context["paginator"] = paginator
        context["paginate_by"] = paginate_by
        # Obtener el ordenamiento desde la solicitud actual
        order_by = self.request.GET.get('order_by') or self.request.POST.get('order_by') or session_filters.get('order_by', ['name'])[0]
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


class AddVehicleGroupView(
    PermissionRequiredMixin,
    LoginRequiredMixin,
    CreateAuditLogAsyncMixin,
    generic.CreateView,
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

    def get_success_url(self):
        # Asegúrate de que el nombre de la URL sea correcto y esté definido en tus archivos de URL.
        return reverse("realtime:group_vehicles")

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
        # Llama al método form_valid de la clase padre para registrar la acción en el log de auditoría
        response = super().form_valid(form)

        # Prepara una respuesta con redirección usando HTMX
        page_update = HttpResponse("")
        page_update["HX-Redirect"] = self.get_success_url()
        return page_update

    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data(form=form))


class UpdateVehicleGroupView(
    PermissionRequiredMixin,
    LoginRequiredMixin,
    UpdateAuditLogAsyncMixin,
    generic.UpdateView,
):
    model = VehicleGroup
    template_name = "realtime/group_vehicles/update_group_vehicles.html"
    permission_required = "realtime.change_vehiclegroup"
    form_class = VehicleGroupForm

    def get_success_url(self):
        # Asegúrate de que el nombre de la URL sea correcto y esté definido en tus archivos de URL.
        return reverse("realtime:group_vehicles")

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

        # Llama al método form_valid de la clase padre para registrar la acción en el log de auditoría
        response = super().form_valid(form)
        # Prepara una respuesta con redirección usando HTMX
        page_update = HttpResponse("")
        page_update["HX-Redirect"] = self.get_success_url()
        return page_update

    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data(form=form))


class DeleteVehicleGroupView(
    PermissionRequiredMixin,
    LoginRequiredMixin,
    DeleteAuditLogAsyncMixin,
    generic.UpdateView,
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

    def get_success_url(self):
        # Asegúrate de que el nombre de la URL sea correcto y esté definido en tus archivos de URL.
        return reverse("realtime:group_vehicles")

    def form_valid(self, form):
        vehicle = form.save(commit=False)
        vehicle.modified_by = self.request.user
        vehicle.visible = False
        vehicle.save()
        # Llama al método form_valid de la clase padre para registrar la acción en el log de auditoría
        response = super().form_valid(form)
        # Prepara una respuesta con redirección usando HTMX
        page_update = HttpResponse("")
        page_update["HX-Redirect"] = self.get_success_url()
        return page_update


class ListSendingCommandsTemplate(
    PermissionRequiredMixin, LoginRequiredMixin, ListView):
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
        paginate_by = self.request.POST.get('paginate_by', None)  # Obtener paginate_by de los parámetros GET

        if paginate_by is None:
            session_filters = self.request.session.get(
                f"filters_sorted_sendcommands_{self.request.user.id}", {}
            )
            paginate_by = session_filters.get("paginate_by", 20)
            # Convertir a entero si es una lista
            try:
                paginate_by = int(
                    paginate_by[0]
                )  # Convertir el primer elemento de la lista a entero
            except (TypeError, ValueError):
                paginate_by = int(paginate_by) if paginate_by else 20
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
        company = user.company_id
        params = self.request.GET if self.request.method == 'GET' else self.request.POST
        query = params.get("query", "").lower()
        search = params.get("q", query).lower()
        if 'order_by' not in params and 'paginate_by' not in params and 'page' not in params:
            # Limpiar los filtros de la sesión
            if f"filters_sorted_sendcommands_{user.id}" in self.request.session:
                del self.request.session[f"filters_sorted_sendcommands_{user.id}"]
                self.request.session.modified = True
        session_filters = self.request.session.get(f'filters_sorted_sendcommands_{user.id}', {})
        order_by = params.get('order_by', session_filters.get('order_by', ['id'])[0])
        direction = params.get('direction', session_filters.get('direction',['desc'])[0])
        # Actualizar los filtros con los parámetros actuales de la solicitud GET
        session_filters.update(params)
        # Actualizar los filtros de la sesión con los nuevos parámetros
        self.request.session[f'filters_sorted_sendcommands_{user.id}'] = session_filters
        self.request.session.modified = True
        # Obtener los planes de datos a través de la función fetch_all_dataplan.
        send_commands = fetch_all_sending_commands(company, user.id, search)
        # Determinar si es orden descendente
        reverse = direction == "desc"

        try:
            sorted_queryset = sorted(send_commands, key=sort_key_commands_datetime(order_by), reverse=reverse)
        except KeyError:
            # Ordenamiento por defecto si la clave no existe
            sorted_queryset = sorted(
                send_commands, key=lambda x: x["id"].lower(), reverse=reverse
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
        session_filters = self.request.session.get(f'filters_sorted_sendcommands_{self.request.user.id}', {})
        # Obtener el ordenamiento desde la solicitud actual
        order_by = self.request.GET.get('order_by') or self.request.POST.get('order_by') or session_filters.get('order_by', ['answer_date'])[0]
        direction = self.request.GET.get('direction') or self.request.POST.get('direction') or session_filters.get('direction', ['desc'])[0]
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


class AddSendingCommandsView(
    PermissionRequiredMixin,
    LoginRequiredMixin,
    CreateAuditLogAsyncMixin,
    generic.CreateView,
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

    def get_context_data(self, **kwargs):
        """
        Obtiene el contexto de datos para renderizar la vista.

        Args:
            **kwargs: Argumentos clave adicionales.

        Returns:
            dict: El contexto de datos para renderizar la vista.
        """
        context = super().get_context_data(**kwargs)
        button_color = self.request.user.company.theme_set.all().first().button_color
        context["button_color"] = button_color
        return context

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

        # Llama al método form_valid de la clase padre para registrar la acción en el log de auditoría
        response = super().form_valid(form)

        # Prepara una respuesta con redirección usando HTMX
        page_update = HttpResponse("")
        page_update["HX-Redirect"] = self.get_success_url()
        return page_update

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()

        kwargs["company_id"] = self.request.user.company_id
        kwargs["user"] = self.request.user

        return kwargs


class ListResponseCommandsTemplate(LoginRequiredMixin, ListView):

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
        paginate_by = self.request.POST.get('paginate_by', None)  # Obtener paginate_by de los parámetros GET

        if paginate_by is None:
            session_filters = self.request.session.get(
                f"filters_sorted_responsecommands_{self.request.user.id}", {}
            )
            paginate_by = session_filters.get("paginate_by", 20)
            # Convertir a entero si es una lista
            try:
                paginate_by = int(
                    paginate_by[0]
                )  # Convertir el primer elemento de la lista a entero
            except (TypeError, ValueError):
                paginate_by = int(paginate_by) if paginate_by else 20
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
        company = user.company_id
        params = self.request.GET if self.request.method == 'GET' else self.request.POST
        query = params.get("query", "").lower()
        search = params.get("q", query).lower()
        if 'order_by' not in params and 'paginate_by' not in params and 'page' not in params:
            # Limpiar los filtros de la sesión
            if f"filters_sorted_responsecommands_{user.id}" in self.request.session:
                del self.request.session[f"filters_sorted_responsecommands_{user.id}"]
                self.request.session.modified = True
        session_filters = self.request.session.get(f'filters_sorted_responsecommands_{user.id}', {})
        order_by = params.get('order_by', session_filters.get('order_by', ['answer_date'])[0])
        direction = params.get('direction', session_filters.get('direction',['desc'])[0])
        # Actualizar los filtros con los parámetros actuales de la solicitud GET
        session_filters.update(params)

        # Actualizar los filtros de la sesión con los nuevos parámetros
        self.request.session[f'filters_sorted_responsecommands_{user.id}'] = session_filters
        self.request.session.modified = True
        # Obtener los planes de datos a través de la función fetch_all_dataplan.
        response_commands = fetch_all_response_commands(company, user.id, search)

        # Función para convertir los valores a minúsculas y extraer números cuando sea necesario
        key_function = sort_key(order_by)
        # Determinar si es orden descendente
        reverse = direction == "desc"

        try:
            sorted_queryset = sorted(response_commands, key=key_function, reverse=reverse)
        except KeyError:
            # Ordenamiento por defecto si la clave no existe
            sorted_queryset = sorted(
                response_commands, key=lambda x: x["id"].lower(), reverse=reverse
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
        session_filters = self.request.session.get(f'filters_sorted_responsecommands_{self.request.user.id}', {})
        # Obtener el ordenamiento desde la solicitud actual
        order_by = self.request.GET.get('order_by') or self.request.POST.get('order_by') or session_filters.get('order_by', ['answer_date'])[0]
        direction = self.request.GET.get('direction') or self.request.POST.get('direction') or session_filters.get('direction', ['desc'])[0]
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


class ListGeozonesTemplate(
    PermissionRequiredMixin, LoginRequiredMixin, ListView
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
        paginate_by = self.request.POST.get('paginate_by', None)  # Obtener paginate_by de los parámetros POST

        if paginate_by is None:
            session_filters = self.request.session.get(
                f"filters_sorted_geofence_{self.request.user.id}", {}
            )
            paginate_by = session_filters.get("paginate_by", 20)
            # Convertir a entero si es una lista
            try:
                paginate_by = int(
                    paginate_by[0]
                )  # Convertir el primer elemento de la lista a entero
            except (TypeError, ValueError):
                paginate_by = int(paginate_by) if paginate_by else 20
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
        user_company_id = self.request.user.company_id
        params = self.request.GET if self.request.method == 'GET' else self.request.POST
        query = params.get("query", "").lower()
        search = params.get("q", query).lower()
        if 'order_by' not in params and 'paginate_by' not in params and 'page' not in params:
            # Limpiar los filtros de la sesión
            if f"filters_sorted_geofence_{user.id}" in self.request.session:
                del self.request.session[f"filters_sorted_geofence_{user.id}"]
                self.request.session.modified = True
        session_filters = self.request.session.get(f'filters_sorted_geofence_{user.id}', {})
        order_by = params.get('order_by', session_filters.get('order_by', ['company'])[0])
        direction = params.get('direction', session_filters.get('direction',['asc'])[0])
        # Actualizar los filtros con los parámetros actuales de la solicitud GET
        session_filters.update(params)

        # Actualizar los filtros de la sesión con los nuevos parámetros
        self.request.session[f'filters_sorted_geofence_{user.id}'] = session_filters
        self.request.session.modified = True
        # Obtener los planes de datos a través de la función fetch_all_dataplan.
        geofence = fetch_all_geozones(user_company_id, user.id, search)

        # Función para convertir los valores a minúsculas y extraer números cuando sea necesario
        key_function = sort_key(order_by)
        # Determinar si es orden descendente
        reverse = direction == "desc"

        try:
            sorted_queryset = sorted(geofence, key=key_function, reverse=reverse)
        except KeyError:
            # Ordenamiento por defecto si la clave no existe
            sorted_queryset = sorted(
                geofence, key=lambda x: x["company"].lower(), reverse=reverse
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
        session_filters = self.request.session.get(f'filters_sorted_geofence_{self.request.user.id}', {})
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

import os

import environ


class AddGeozonesView(PermissionRequiredMixin, LoginRequiredMixin, CreateAuditLogAsyncMixin, generic.CreateView):
    """ """

    template_name = "realtime/geozones/add_geozone.html"
    permission_required = "realtime.add_geozones"
    success_url = reverse_lazy("index")
    login_url = reverse_lazy("index")
    form_class = GeozonesForm

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
        context["key"] = os.environ.get('GOOGLE_MAPS_API_KEY')
        return context

    def get_success_url(self):
        # Asegúrate de que el nombre de la URL sea correcto y esté definido en tus archivos de URL.
        return reverse("realtime:geozones")

    def form_valid(self, form):
        save = form.save(commit=False)
        save.created_by = self.request.user
        save.modified_by = self.request.user
        save.save()
        # Llama al método form_valid de la clase padre para registrar la acción en el log de auditoría
        response = super().form_valid(form)

        # Prepara una respuesta con redirección usando HTMX
        page_update = HttpResponse("")
        page_update["HX-Redirect"] = self.get_success_url()
        return page_update


class UpdateGeozonesView(
    PermissionRequiredMixin, LoginRequiredMixin, generic.UpdateView
):

    """ """

    model = Geozones
    template_name = "realtime/geozones/update_geozone.html"
    login_url = reverse_lazy("login")
    permission_required = "realtime.change_geozones"
    success_url = reverse_lazy("login")
    form_class = GeozonesForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company_id = self.request.user.company_id
        context["form"].fields["company"].queryset = Company.objects.filter(
            Q(id=company_id) | Q(provider_id=company_id), visible=True, actived=True
        )
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


class DeleteGeozonesView(LoginRequiredMixin, generic.UpdateView):
    """ """

    model = Geozones
    template_name = "realtime/geozones/delete_geozone.html"
    fields = ["visible"]

    def get_success_url(self):
        # Asegúrate de que el nombre de la URL sea correcto y esté definido en tus archivos de URL.
        return reverse("realtime:geozones")

    def form_valid(self, form):
        vehicle = form.save(commit=False)
        vehicle.visible = False
        vehicle.save()
        # Llama al método form_valid de la clase padre para registrar la acción en el log de auditoría
        response = super().form_valid(form)

        # Prepara una respuesta con redirección usando HTMX
        page_update = HttpResponse("")
        page_update["HX-Redirect"] = self.get_success_url()
        return page_update


class ConfigurationReportView(
    PermissionRequiredMixin, LoginRequiredMixin, TemplateView
):
    model = Io_items_report
    template_name = "realtime/custom_report/main_configuration_report.html"
    permission_required = "realtime.view_io_items_report"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        companies = get_user_companies(user)
        if user.company_id == 1:
            context["companies"] = companies
        else:
            # Convertir el queryset en una lista de tuplas (id, company_name)
            companies_list = list(companies.values_list("id", "company_name"))
            context["companies"] = companies_list
        context["button_color"] = (
            self.request.user.company.theme_set.all().first().button_color
        )
        return context


class UpdateConfigurationReportView(
    PermissionRequiredMixin, LoginRequiredMixin, UpdateAuditLogSyncMixin, View
):
    template_name = "realtime/custom_report/update_configuration_report.html"
    permission_required = "realtime.change_io_items_report"

    def get(self, request, company_id, *args, **kwargs):
        # Obtener o crear una instancia de Io_elements para la compañía actual
        instance, created = Io_items_report.objects.get_or_create(company_id=company_id)

        selected_widgets = (
            json.loads(instance.info_widgets) if instance.info_widgets else []
        )
        selected_reports = (
            json.loads(instance.info_reports) if instance.info_reports else []
        )

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

        # Guardar el estado antes de actualizar la instancia
        self.obj_before = instance.__class__.objects.get(pk=instance.pk)

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

        # Guardar el estado anterior antes de actualizar la instancia
        self.obj_before = instance.__class__.objects.get(pk=instance.pk)

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

        # Guardar el estado después de actualizar la instancia
        self.obj_after = instance

        self.log_action()

        messages.success(request, f"{company_name} actualizada correctamente.")
        return redirect("realtime:add_configuration_report")

    def form_valid(self, form):
        response = super().form_valid(form)
        if self.action == "create" or self.action == "update":
            self.obj_after = form.instance
        elif self.action == "delete":
            self.obj_after = {}

        self.log_action()
        return response
