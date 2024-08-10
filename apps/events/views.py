from django.contrib.auth.mixins import (LoginRequiredMixin,
                                        PermissionRequiredMixin)
from django.db.models import Q
from django.http import HttpResponse
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views import generic

from apps.authentication.models import User
from apps.whitelabel.models import Company
from config.pagination import get_paginate_by

from .forms import EventForm, EventUserForm
from .models import Event, EventFeature
from .sql import fetch_all_event, fetch_all_event_personalized


class ListEventsView(LoginRequiredMixin, generic.ListView):
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
        return get_paginate_by(self.request)

    def get_queryset(self):
        """
        Obtiene el conjunto de datos de los comandos de envío filtrados y ordenados.

        Returns:
            QuerySet: El conjunto de datos de los comandos de envío filtrados y ordenados.
        """
        user = self.request.user
        return fetch_all_event()

    def get_context_data(self, **kwargs):
        """
        Obtiene el contexto de datos adicionales para la plantilla.

        Args:
            **kwargs: Argumentos clave adicionales.

        Returns:
            dict: El contexto de datos adicionales para la plantilla.
        """
        context = super().get_context_data(**kwargs)
        # Calcula start_number más eficientemente
        page_number = context.get("page_obj").number if context.get("page_obj") else 1
        context["start_number"] = (page_number - 1) * self.get_paginate_by(None)
        return context


# class ListEventsView(PermissionRequiredMixin, generic.ListView):
#     """
#     Vista como clase que permite al usuario_administrador AZ visualizar los eventos predefinidos
#     así como acceder a las opciones para eliminar y editar dichos eventos.
#     """

#     template_name = "events/predefined_events/list_events_predefined.html"
#     permission_required = "events.view_event"
#     context_object_name = "list_events"

#     def get_queryset(self):
#         return Event.objects.all()


class AddEventsView(LoginRequiredMixin, generic.CreateView):
    """
    Vista como clase que implementa la opción de añadir eventos predefinidos para el
    usuario-administrador AZ. Permite modificar los campos "number" y "name".
    """

    model = Event
    form_class = EventForm
    template_name = "events/predefined_events/add_events.html"
    success_url = "/events"

    def form_valid(self, form):
        form.instance.modified_by = self.request.user
        form.save()
        return HttpResponse(status=204, headers={"HX-Trigger": "ListEventChanged"})


class UpdateEventsView(LoginRequiredMixin, generic.UpdateView):
    """
    Vista como clase que implementa la opción de edición de eventos predefinidos para el
    usuario-administrador AZ. Permite modificar los campos "number" y "name".
    """

    model = Event
    form_class = EventForm
    template_name = "events/predefined_events/update_events.html"
    success_url = "/events"

    def form_valid(self, form):
        form.instance.modified_by = self.request.user
        form.save()
        return HttpResponse(status=204, headers={"HX-Trigger": "ListEventChanged"})


class DeleteEventsView(LoginRequiredMixin, generic.DeleteView):
    """
    Vista como clase que implementa la opción de eliminar eventos predefinidos para el
    usuario-administrador AZS.
    """

    model = Event
    template_name = "events/predefined_events/delete_events.html"
    context_object_name = "delete"
    success_url = "/events"

    # def form_valid(self, form):
    #     return HttpResponse(status=204, headers={'HX-Trigger': 'ListEventChanged'})


class ListUserEventsTemplate(
    PermissionRequiredMixin, LoginRequiredMixin, generic.ListView
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
        return get_paginate_by(self.request)

    def get_queryset(self):
        """
        Obtiene el conjunto de datos de los comandos de envío filtrados y ordenados.

        Returns:
            QuerySet: El conjunto de datos de los comandos de envío filtrados y ordenados.
        """
        user = self.request.user
        company= user.company
        return fetch_all_event_personalized(company, user.id)

    def get_context_data(self, **kwargs):
        """
        Obtiene el contexto de datos adicionales para la plantilla.

        Args:
            **kwargs: Argumentos clave adicionales.

        Returns:
            dict: El contexto de datos adicionales para la plantilla.
        """
        context = super().get_context_data(**kwargs)
        # Calcula start_number más eficientemente
        user = self.request.user
        context["show_button"] = user.company_id == 1
        page_number = context.get("page_obj").number if context.get("page_obj") else 1
        context["start_number"] = (page_number - 1) * self.get_paginate_by(None)
        return context


class AddUserEventsView(
    PermissionRequiredMixin, LoginRequiredMixin, generic.CreateView
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
        context["companies"] = companies
        events_id = set()
        familymodel = set()
        events = []

        # devices_company = Device.objects.filter(company=self.request.user.company_id)
        # for device in devices_company:
        #     familymodel.add(device.familymodel_id)
        # for device_id in familymodel:
        #     number_event = UEC.objects.filter(familymodel=device_id)
        #     for event in number_event:
        #         events_id.add(event.event_number_id)
        # for i in events_id:
        #     events.append([i, Event.objects.get(id=i)])
        # context["events"] = events

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

        # Verifica si ya existe un EventFeature visible para el mismo evento y empresa
        existing_visible_event_feature = EventFeature.objects.filter(
            event_id=p_event_query,
            company_id=query_company.company,
            visible=True,  # Asegúrate de buscar los visibles
        ).first()

        if existing_visible_event_feature:
            # Si existe uno visible, muestra un mensaje de error
            msg = _(
                """You already have this event visible, can't create it again!!
                Select another one"""
            )
            form.add_error("event", msg)
            return self.form_invalid(form)

        # Buscar si ya existe un EventFeature oculto para el mismo evento y empresa
        existing_event_feature = EventFeature.objects.filter(
            event_id=p_event_query,
            company_id=query_company.company,
            visible=False,  # Asegúrate de buscar los ocultos
        ).first()

        if existing_event_feature:
            # Si existe uno oculto, actualiza sus campos y establece visible en True
            existing_event_feature.alias = form.cleaned_data["alias"]
            existing_event_feature.central_alarm = form.cleaned_data["central_alarm"]
            existing_event_feature.user_alarm = form.cleaned_data["user_alarm"]
            # Actualiza otros campos según sea necesario
            existing_event_feature.visible = True
            existing_event_feature.save()
        else:
            # Si no existe, crea uno nuevo

            form.save()
        page_update = HttpResponse(
            ""
        )  # O puedes enviar algún contenido si es necesario.
        page_update["HX-Redirect"] = self.get_success_url()
        return page_update

    def form_invalid(self, form):
        """
        Eleva la condición de error para la que fue llamada en la función
        form_valid, renderizando el mensaje de error así como el formulario.
        """
        return self.render_to_response(self.get_context_data(form=form))


class UpdateUserEventsViews(PermissionRequiredMixin, generic.UpdateView):
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
        feature_event = EventFeature.objects.get(id=self.kwargs.get("pk"))
        event = Event.objects.filter(id=feature_event.event_id)
        context["event_created"] = event
        context["companies"] = companies
        return context

    def form_valid(self, form):
        company_id = self.request.POST.get("company")
        form.instance.company = Company.objects.get(id=company_id)
        form.clean_user_alarm()
        form.clean_end_time()
        form.instance.modified_by = self.request.user
        form.save()
        page_update = HttpResponse(
            ""
        )  # O puedes enviar algún contenido si es necesario.
        page_update["HX-Redirect"] = self.get_success_url()
        return page_update


class DeleteUserEventsView(
    PermissionRequiredMixin, LoginRequiredMixin, generic.UpdateView
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

        page_update = HttpResponse(
            ""
        )  # O puedes enviar algún contenido si es necesario.
        page_update["HX-Redirect"] = self.get_success_url()
        return page_update
