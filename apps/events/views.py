import datetime

from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db.models import Q
from django.http import HttpResponse
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views import generic
from django.utils.decorators import method_decorator
from django.core.paginator import Paginator
from django.views.decorators.csrf import csrf_protect
from django.views.generic import ListView

from apps.authentication.models import User
from apps.log.mixins import (
    CreateAuditLogAsyncMixin,
    DeleteAuditLogAsyncMixin,
    UpdateAuditLogAsyncMixin,
)
from apps.realtime.apis import extract_number, get_user_companies, sort_key
from apps.whitelabel.models import Company
from config.pagination import get_paginate_by

from .forms import EventForm, EventUserForm
from .models import Event, EventFeature
from .sql import fetch_all_event, fetch_all_event_personalized


class ListEventsView(LoginRequiredMixin, ListView):
    """
    Vista como clase que renderiza el template HTML que contiene la lista de eventos
    predefinidos por AZ. Un usuario_administrador AZ puede editarlos ó eliminarlos.
    """

    model = Event
    template_name = "events/predefined_events/main_events.html"

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
                f"filters_sorted_eventpredefined_{self.request.user.id}", {}
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
        params = self.request.GET if self.request.method == 'GET' else self.request.POST
        query = params.get("query", "").lower()
        search = params.get("q", query).lower()
        if 'order_by' not in params and 'paginate_by' not in params and 'page' not in params:
            # Limpiar los filtros de la sesión
            if f"filters_sorted_eventpredefined_{user.id}" in self.request.session:
                del self.request.session[f"filters_sorted_eventpredefined_{user.id}"]
                self.request.session.modified = True
        # Recuperar filtros almacenados en la sesión
        session_filters = self.request.session.get(f'filters_sorted_eventpredefined_{user.id}', {})
        order_by = params.get('order_by', session_filters.get('order_by', ['number'])[0])
        direction = params.get('direction', session_filters.get('direction',['asc'])[0])
        # Actualizar los filtros con los parámetros actuales de la solicitud GET
        session_filters.update(params)

        # Actualizar los filtros de la sesión con los nuevos parámetros
        self.request.session[
            f"filters_sorted_eventpredefined_{user.id}"
        ] = session_filters
        self.request.session.modified = True
        queryset = fetch_all_event(search)
        # Función para convertir los valores a minúsculas y extraer números cuando sea necesario
        key_function = sort_key(order_by)
        reverse = direction == 'desc'
        try:
            sorted_queryset = sorted(queryset, key=key_function, reverse=reverse)
        except KeyError:
            # Ordenamiento por defecto si la clave no existe
            sorted_queryset = sorted(
                queryset, key=lambda x: x["number"].lower(), reverse=reverse
            )

        return sorted_queryset

    def get_context_data(self, **kwargs):
        """
        Obtiene el contexto de datos adicionales para la plantilla.

        Args:
            **kwargs: Argumentos clave adicionales.

        Returns:
            dict: El contexto de datos adicionales para la plantilla.
        """
        context = super().get_context_data(**kwargs)
        paginate_by = self.get_paginate_by(None)
        context["paginate_by"] = paginate_by
        # Calcula start_number más eficientemente
        page_number = context.get("page_obj").number if context.get("page_obj") else 1
        context["start_number"] = (page_number - 1) * self.get_paginate_by(None)
        session_filters = self.request.session.get(f'filters_sorted_eventpredefined_{self.request.user.id}', {})
        # Obtener el ordenamiento desde la solicitud actual
        order_by = self.request.GET.get('order_by') or self.request.POST.get('order_by') or session_filters.get('order_by', ['number'])[0]
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


class AddEventsView(LoginRequiredMixin, CreateAuditLogAsyncMixin, generic.CreateView):
    """
    Vista como clase que implementa la opción de añadir eventos predefinidos para el
    usuario-administrador AZ. Permite modificar los campos "number" y "name".
    """

    model = Event
    form_class = EventForm
    template_name = "events/predefined_events/add_events.html"
    success_url = "/events"

    def get_success_url(self):
        # Asegúrate de que el nombre de la URL sea correcto y esté definido en tus archivos de URL.
        return reverse("events:list_events_predefined")

    def form_valid(self, form):
        form.instance.modified_by = self.request.user
        form.save()
        # Llama al método form_valid de la clase padre para registrar la acción en el log de auditoría
        response = super().form_valid(form)
        # Prepara una respuesta con redirección usando HTMX
        page_update = HttpResponse("")
        page_update["HX-Redirect"] = self.get_success_url()
        return page_update


class UpdateEventsView(
    LoginRequiredMixin, UpdateAuditLogAsyncMixin, generic.UpdateView
):
    """
    Vista como clase que implementa la opción de edición de eventos predefinidos para el
    usuario-administrador AZ. Permite modificar los campos "number" y "name".
    """

    model = Event
    form_class = EventForm
    template_name = "events/predefined_events/update_events.html"
    success_url = "/events"

    def get_success_url(self):
        # Asegúrate de que el nombre de la URL sea correcto y esté definido en tus archivos de URL.
        return reverse("events:list_events_predefined")

    def form_valid(self, form):
        form.instance.modified_by = self.request.user
        form.save()
        # Llama al método form_valid de la clase padre para registrar la acción en el log de auditoría
        response = super().form_valid(form)
        # Prepara una respuesta con redirección usando HTMX
        page_update = HttpResponse("")
        page_update["HX-Redirect"] = self.get_success_url()
        return page_update


class DeleteEventsView(
    LoginRequiredMixin, DeleteAuditLogAsyncMixin, generic.UpdateView
):
    """
    Vista como clase que implementa la opción de eliminar eventos predefinidos para el
    usuario-administrador AZS.
    """

    model = Event
    template_name = "events/predefined_events/delete_events.html"
    success_url = reverse_lazy("events:list_events_predefined")
    fields = ["visible"]

    def get_success_url(self):
        """
        Devuelve la URL a la que se redirige después de una eliminación exitosa.
        """
        return reverse("events:list_events_predefined")

    def form_valid(self, form):
        event_feature = form.save(commit=False)
        event_feature.visible = False  # Marcar el evento personalizado como no visible
        event_feature.save()

        # Llama al método form_valid de la clase padre para registrar la acción en el log de auditoría
        response = super().form_valid(form)

        # Prepara una respuesta con redirección usando HTMX
        page_update = HttpResponse("")
        page_update["HX-Redirect"] = self.get_success_url()
        return page_update


class ListUserEventsTemplate(
    PermissionRequiredMixin, LoginRequiredMixin, ListView
):
    """
    Vista como clase que renderiza el template HTML que contiene la lista de eventos
    predefinidos por AZ. Un usuario_administrador AZ puede editarlos ó eliminarlos.
    """

    model = EventFeature
    template_name = "events/user_events/main_user_events.html"
    permission_required = "events.view_eventfeature"

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
                f"filters_sorted_eventuser_{self.request.user.id}", {}
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
        # Parámetros de ordenamiento por defecto
        order_by = params.get("order_by", "id")
        direction = params.get("direction", "asc")
        if 'order_by' not in params and 'paginate_by' not in params and 'page' not in params:
            # Limpiar los filtros de la sesión
            if f"filters_sorted_eventuser_{user.id}" in self.request.session:
                del self.request.session[f"filters_sorted_eventuser_{user.id}"]
                self.request.session.modified = True
        # Recuperar filtros almacenados en la sesión
        session_filters = self.request.session.get(f'filters_sorted_eventuser_{user.id}', {})
        order_by = params.get('order_by', session_filters.get('order_by', ['company'])[0])
        direction = params.get('direction', session_filters.get('direction',['asc'])[0])
        # Actualizar los filtros con los parámetros actuales de la solicitud GET
        session_filters.update(params)

        # Actualizar los filtros de la sesión con los nuevos parámetros
        self.request.session[
            f"filters_sorted_eventuser_{user.id}"
        ] = session_filters
        self.request.session.modified = True
        queryset = fetch_all_event_personalized(company, user.id, search)

        # Función para convertir los valores a minúsculas y extraer números cuando sea necesario
        def sort_key(x):
            value = x.get(order_by)
            if value is None or value == "":
                return (4, "")  # Prioridad 4 para valores nulos o vacíos
            if isinstance(value, str):
                # Verificar si comienza con números, letras o caracteres especiales
                if value[0].isdigit():
                    return (2, extract_number(value))  # Prioridad 1 para números
                elif value[0].isalpha():
                    return (1, value.lower())  # Prioridad 2 para letras
                else:
                    return (3, value.lower())  # Prioridad 3 para caracteres especiales
            if isinstance(value, datetime.time):
                return (5, value)  # Prioridad 5 para objetos datetime.time
            return (6, value)  # Prioridad 6 para otros tipos

        # Determinar si es orden descendente
        reverse = direction == "desc"

        try:
            sorted_queryset = sorted(queryset, key=sort_key, reverse=reverse)
        except KeyError:
            # Ordenamiento por defecto si la clave no existe
            sorted_queryset = sorted(
                queryset, key=lambda x: x["company"].lower(), reverse=reverse
            )

        return sorted_queryset

    def get_context_data(self, **kwargs):
        """
        Obtiene el contexto de datos adicionales para la plantilla.

        Args:
            **kwargs: Argumentos clave adicionales.

        Returns:
            dict: El contexto de datos adicionales para la plantilla.
        """
        context = super().get_context_data(**kwargs)
        paginate_by = self.get_paginate_by(None)
        context["paginate_by"] = paginate_by
        # Calcula start_number más eficientemente
        user = self.request.user
        context["show_button"] = user.company_id == 1
        page_number = context.get("page_obj").number if context.get("page_obj") else 1
        context["start_number"] = (page_number - 1) * self.get_paginate_by(None)
        session_filters = self.request.session.get(f'filters_sorted_eventuser_{self.request.user.id}', {})
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


class AddUserEventsView(
    PermissionRequiredMixin,
    LoginRequiredMixin,
    CreateAuditLogAsyncMixin,
    generic.CreateView,
):
    """
    Vista como clase que implementa la opción para los usuarios de añadir eventos a partir de los
    eventos predefinidos otorgados por el admin a través del dispositivo.
    Permite añadir una configuración personalizada para los campos  'alias', 'central_alarm',
    'user_alarm', 'start_time','end_time', 'color', 'email_alarm', 'alarm_sound', 'sound_priority',
    'type_alarm_sound'.
    """

    form_class = EventUserForm
    template_name = "events/user_events/add_user_events.html"
    permission_required = "events.add_eventfeature"
    success_url = "/events/users"

    def get_success_url(self):
        # Asegúrate de que el nombre de la URL sea correcto y esté definido en tus archivos de URL.
        return reverse("events:list_user_events")

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
        company_id = self.request.POST.get("company")
        form.instance.company = Company.objects.get(id=company_id)
        form.clean_event()
        form.clean_user_alarm()
        form.clean_end_time()
        query_company = User.objects.get(id=self.request.user.id)
        form.instance.modified_by = self.request.user
        p_event_query = form.instance.event
        
        # Verificar si ya existe un EventFeature visible para el mismo evento y empresa
        existing_visible_event_feature = EventFeature.objects.filter(
            event_id=p_event_query,
            company_id=query_company.company,
            visible=True
        ).first()

        if existing_visible_event_feature:
            # Si existe uno visible, muestra un mensaje de error y no guarda el formulario
            msg = _(
                "You already have this event created, can't create it again! Select another one"
            )
            form.add_error("event", msg)
            return self.form_invalid(form)

        # Si no existe un evento visible, buscar si ya existe uno oculto
        existing_event_feature = EventFeature.objects.filter(
            event_id=p_event_query,
            company_id=query_company.company,
            visible=False
        ).first()

        if existing_event_feature:
            # Si existe uno oculto, actualiza sus campos y establece visible en True
            existing_event_feature.alias = form.cleaned_data["alias"]
            existing_event_feature.central_alarm = form.cleaned_data["central_alarm"]
            existing_event_feature.user_alarm = form.cleaned_data["user_alarm"]
            existing_event_feature.visible = True
            response = super().form_valid(form)
            existing_event_feature.save()
        else:
            # Si no existe, guarda el nuevo EventFeature
            form.instance.visible = True  # Asegúrate de que el nuevo EventFeature sea visible
            response = super().form_valid(form)
            form.save()

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


class UpdateUserEventsViews(
    PermissionRequiredMixin,
    LoginRequiredMixin,
    UpdateAuditLogAsyncMixin,
    generic.UpdateView,
):
    """
    Vista como clase que implementa la opción de edición de eventos predefinidos para el
    usuario. Permite modificar los campos  'alias', 'central_alarm', 'user_alarm', 'start_time',
    'end_time', 'color', 'email_alarm', 'alarm_sound', 'sound_priority', 'type_alarm_sound'.
    """

    model = EventFeature
    form_class = EventUserForm
    template_name = "events/user_events/update_user_events.html"
    permission_required = "events.change_eventfeature"
    success_url = "/events/users"

    def get_success_url(self):
        # Asegúrate de que el nombre de la URL sea correcto y esté definido en tus archivos de URL.
        return reverse("events:list_user_events")

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
        company_id = self.request.POST.get("company")
        form.instance.company = Company.objects.get(id=company_id)
        form.clean_user_alarm()
        form.clean_end_time()
        form.instance.modified_by = self.request.user
        form.save()
        # Llama al método form_valid de la clase padre para registrar la acción en el log de auditoría
        response = super().form_valid(form)

        # Prepara una respuesta con redirección usando HTMX
        page_update = HttpResponse("")
        page_update["HX-Redirect"] = self.get_success_url()
        return page_update


class DeleteUserEventsView(
    PermissionRequiredMixin,
    LoginRequiredMixin,
    DeleteAuditLogAsyncMixin,
    generic.UpdateView,
):
    """
    Vista como clase que implementa la opción de eliminar eventos personalizados para la
    empresa cliente.
    """

    model = EventFeature
    template_name = "events/user_events/delete_user_events.html"
    permission_required = "events.delete_eventfeature"
    success_url = reverse_lazy("events:list_user_events_created")
    fields = ["visible"]

    def get_success_url(self):
        # Asegúrate de que el nombre de la URL sea correcto y esté definido en tus archivos de URL.
        return reverse("events:list_user_events")

    def form_valid(self, form):
        event_feature = form.save(commit=False)
        event_feature.visible = False  # Marcar el evento personalizado como no visible
        event_feature.save()

        # Llama al método form_valid de la clase padre para registrar la acción en el log de auditoría
        response = super().form_valid(form)

        # Prepara una respuesta con redirección usando HTMX
        page_update = HttpResponse("")
        page_update["HX-Redirect"] = self.get_success_url()
        return page_update
