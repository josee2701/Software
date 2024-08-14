import asyncio
import base64
import copy
import json
import os
from datetime import datetime
from decimal import Decimal, InvalidOperation

from asgiref.sync import async_to_sync
from django.contrib import messages
from django.contrib.admin.utils import NestedObjects
from django.contrib.auth.mixins import (LoginRequiredMixin,
                                        PermissionRequiredMixin)
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db import DEFAULT_DB_ALIAS, transaction
from django.db.models import F, OuterRef, Q, Subquery, Sum
from django.forms.models import model_to_dict
from django.http import (Http404, HttpResponse, HttpResponseNotAllowed,
                         HttpResponseRedirect, JsonResponse, QueryDict)
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views import generic
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.views.generic import ListView
from django.views.generic.list import MultipleObjectMixin
from rest_framework import generics

from apps.authentication.models import User
from apps.log.mixins import (AuditLogSyncMixin, CreateAuditLogAsyncMixin,
                             CreateAuditLogSyncMixin, DeleteAuditLogAsyncMixin,
                             UpdateAuditLogAsyncMixin, UpdateAuditLogSyncMixin,
                             obtener_ip_publica)
from apps.log.utils import log_action
from apps.realtime.apis import (extract_number, extract_number_tp,
                                get_user_companies)
from apps.whitelabel.forms import (AttachmentForm, CommentForm,
                                   CompanyCustomerForm, CompanyDeleteForm,
                                   CompanyLogoForm, DistributionCompanyForm,
                                   KeyMapForm, MessageForm, Moduleform,
                                   ProcessForm, ThemeForm, TicketForm)
from apps.whitelabel.models import (Attachment, Company, CompanyTypeMap,
                                    MapType, Module, Process, Theme, Ticket)
from config.filtro import General_Filters
from config.pagination import get_paginate_by

from .forms import (AttachmentForm, CommentForm, CompanyCustomerForm,
                    CompanyDeleteForm, CompanyLogoForm,
                    DistributionCompanyForm, KeyMapForm, MessageForm,
                    Moduleform, ProcessForm, ThemeForm, TicketCrearte,
                    TicketForm)
from .models import (Attachment, Company, CompanyTypeMap, MapType, Message,
                     Module, Process, Theme, Ticket)
from .serializer import ClienteSerializer
from .sql import (fetch_all_company, get_modules_by_user, get_ticket_by_user,
                  get_ticket_closed)


class CompaniesView(PermissionRequiredMixin,LoginRequiredMixin, ListView):
    """
    Vista para listar las compañías con paginación, ordenamiento y búsqueda.

    Atributos:
        template_name: Plantilla utilizada para renderizar la vista.
        login_url: URL de redirección para usuarios no autenticados.
        context_object_name: Nombre del contexto para la lista de objetos.
        model: Modelo asociado a la vista.
        paginate_by: Número de elementos por página por defecto.
    """
    template_name = "whitelabel/companies/company_main.html"
    permission_required= "whitelabel.view_company"
    login_url = "login"
    context_object_name = "company_info"
    model = Company
    paginate_by = 15  # Número de elementos por página por defecto

    def get_template_names(self):
        """
        Obtiene la plantilla a utilizar basada en el ID de la compañía del usuario.

        Returns:
            list: Lista de nombres de plantilla.
        """
        user = self.request.user
        if user.company_id:
            company_id = user.company_id
            if not Company.objects.filter(provider_id=company_id).exists():
                return ["whitelabel/companies/cliente_final_main.html"]
        return [self.template_name]

    def get_paginate_by(self, queryset):
        """
        Obtiene el número de elementos por página desde los parámetros GET o usa el valor por defecto.
        """
        paginate_by = self.request.GET.get('paginate_by', self.paginate_by)
        try:
            return int(paginate_by)
        except (ValueError, TypeError):
            return self.paginate_by

    def get_queryset(self):
        """
        Obtiene el queryset de compañías, con filtros de búsqueda y ordenamiento basados en parámetros GET.
        """
        user=self.request.user
        queryset = General_Filters.get_filtered_companies(user)

        # Parámetros de búsqueda
        search_query = self.request.GET.get('search', '').lower()

        # Traducción y filtrado de campos booleanos y tipo de cliente
        active_terms = _("Active").lower()
        inactive_terms = _("Inactive").lower()
        distributor_terms = _("Distributor").lower()
        final_client_terms = _("Final client").lower()

        filters = Q()  # Crea un objeto Q vacío
        if search_query:
            # Convertir la consulta de búsqueda a minúsculas
            search_query_lower = search_query.lower()
            # Filtrar los campos de texto
            filters |= Q(company_name__icontains=search_query) | \
                      Q(nit__icontains=search_query) | \
                      Q(legal_representative__icontains=search_query) 
            # Filtrar el campo booleano
            if search_query_lower in active_terms:
                filters |= Q(actived=True)
            elif search_query_lower in inactive_terms:
                filters |= Q(actived=False)
            # Filtrar por tipo de cliente
            if search_query_lower in distributor_terms:
                filters |= Q(provider__isnull=True)  # Distribuidor no tiene proveedor
            elif search_query_lower in final_client_terms:
                filters |= Q(provider__isnull=False)  # Cliente final tiene proveedor
        queryset = queryset.filter(filters)

        # Parámetros de ordenamiento
        order_by = self.request.GET.get('order_by', 'company_name')
        direction = self.request.GET.get('direction', 'asc')

        # Validación de campos de ordenamiento
        valid_order_by = ['nit', 'company_name', 'legal_representative', 'provider', 'actived']
        if order_by not in valid_order_by:
            order_by = 'company_name'

        if direction == 'desc':
            order_by = f'-{order_by}'

        return queryset.order_by(order_by)

    def get_context_data(self, **kwargs):
        """
        Agrega información adicional al contexto, como la paginación y el estado de ordenamiento.
        """
        context = super().get_context_data(**kwargs)

        # Obtener compañías de la página actual
        companies = context[self.context_object_name]
        paginator = context['paginator']
        page_number = self.request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)

        # Agregar el botón de mapa a las compañías
        company_ids = companies.values_list('id', flat=True)
        maps = CompanyTypeMap.objects.filter(company_id__in=company_ids)

        # Crear un diccionario donde cada company_id tiene una lista de map_type_id
        map_dict = {}
        for m in maps:
            if m.company_id not in map_dict:
                map_dict[m.company_id] = []
            map_dict[m.company_id].append(m.map_type_id)

        for company in companies:
            company_maps = map_dict.get(company.id, [])
            total_maps = len(company_maps)
            has_only_map1 = total_maps == 1 and 1 in company_maps
            company.show_map_button = not has_only_map1

        context.update({
            'page_obj': page_obj,
            'paginate_by': self.get_paginate_by(self.get_queryset()),
            'paginate_options': [15, 25, 50, 100],
            'order_by': self.request.GET.get('order_by', 'company_name'),
            'direction': self.request.GET.get('direction', 'asc'),
        })

        return context


class CreateDistributionCompanyView(
    PermissionRequiredMixin,
    LoginRequiredMixin,
    CreateAuditLogAsyncMixin,
    generic.CreateView,
):
    """
    Vista para crear una nueva compañía distribuidora. Utiliza permisos y registro de auditoría.

    Atributos:
        model (Model): El modelo asociado con la vista, en este caso `Company`.
        template_name (str): Nombre de la plantilla que se utiliza para renderizar la vista.
        permission_required (str): Permiso requerido para acceder a la vista.
        login_url (str): URL a la cual redirigir si el usuario no está autenticado.
        form_class (Form): El formulario asociado a la creación de la compañía.
        success_url (str): URL a la cual redirigir después de una creación exitosa.
    """
    model = Company
    template_name = "whitelabel/companies/add_company.html"
    permission_required = "whitelabel.add_company"
    login_url = "login"
    form_class = DistributionCompanyForm
    success_url = "companies:companies"

    def get_success_url(self):
        """
        Devuelve la URL de éxito para la redirección después de crear la compañía.

        Returns:
            str: La URL de redirección después de una creación exitosa.
        """
        return reverse("companies:companies")

    def get_context_data(self, **kwargs):
        """
        Añade al contexto información adicional para renderizar la plantilla,
        incluyendo mapas, módulos y la personalización del tema para la compañía.

        Args:
            **kwargs: Argumentos adicionales para el contexto.

        Returns:
            dict: Contexto actualizado con información adicional como mapas, módulos y temas.
        """
        context = super().get_context_data(**kwargs)
        user = self.request.user
        company_id = user.company_id

        # Obtener los mapas asociados a la compañía del usuario
        context["type_maps"] = CompanyTypeMap.objects.filter(company_id=company_id)
        
        # Obtener los módulos asociados a la compañía del usuario
        context["modules"] = Module.objects.filter(company__id=company_id)

        # Obtener el color del botón desde el tema asociado a la compañía
        theme = user.company.theme_set.first()
        context["button_color"] = theme.button_color if theme else "#000000"

        # Pasar el ID de la compañía al contexto
        context["company_id"] = company_id
        return context

    def form_valid(self, form):
        """
        Procesa el formulario cuando es válido. Activa la compañía por defecto, asigna
        valores al campo de creación y modificación, y maneja la redirección basada en 
        los mapas disponibles.

        Args:
            form (Form): El formulario validado.

        Returns:
            HttpResponse: Redirección a la URL de éxito o a la vista de `KeyMapView`.
        """
        # Activar la compañía por defecto
        form.instance.actived = True
        company = form.save(commit=False)

        # Asignar el usuario actual como creador y modificador
        company.modified_by = self.request.user
        company.created_by = self.request.user
        company.provider_id = None  # Es una distribuidora, por lo que no tiene proveedor

        # Guardar la compañía en la base de datos
        company.save()

        # Guardar las relaciones ManyToMany
        form.save_m2m()

        # Llamar al método de la clase base para el registro en el log de auditoría
        response = super().form_valid(form)

        # Si el ID de la compañía del usuario es 1, crear un tema por defecto si no existe
        if self.request.user.company_id == 1 and not Theme.objects.filter(company_id=company.id).exists():
            Theme.objects.create(company_id=company.id)

        # Comprobar si la compañía tiene solo "OpenStreetMap"
        has_openstreetmap_only = MapType.objects.filter(
            companytypemap__company=company, name="OpenStreetMap"
        ).exists()

        if has_openstreetmap_only:
            # Redirigir directamente a la URL de éxito si solo existe "OpenStreetMap"
            page_update = HttpResponse("")
            page_update["HX-Redirect"] = self.get_success_url()
            return page_update
        else:
            # Redirigir a la vista `KeyMapView` si hay otros mapas disponibles
            return redirect("companies:KeyMapView", pk=company.id)



class CreateCustomerCompanyView(
    PermissionRequiredMixin,
    LoginRequiredMixin,
    CreateAuditLogAsyncMixin,
    generic.CreateView,
):
    """
    Vista para crear una nueva compañía cliente. Utiliza permisos, autenticación y
    registro de auditoría.

    Atributos:
        model (Model): El modelo asociado con la vista, en este caso `Company`.
        template_name (str): Nombre de la plantilla utilizada para renderizar la vista.
        permission_required (str): Permiso necesario para acceder a esta vista.
        form_class (Form): El formulario utilizado para crear la compañía cliente.
        success_url (str): La URL de redirección tras una creación exitosa.
    """
    model = Company
    template_name = "whitelabel/companies/add_company.html"
    permission_required = "whitelabel.add_company"
    form_class = CompanyCustomerForm
    success_url = reverse_lazy("companies:companies")

    def get_success_url(self):
        """
        Devuelve la URL de éxito para redirigir tras la creación de la compañía.

        Returns:
            str: La URL de redirección tras una creación exitosa.
        """
        return reverse("companies:companies")

    def get_form_kwargs(self):
        """
        Pasa el `provider_id` de la compañía del usuario actual como argumento adicional al formulario.

        Returns:
            dict: Argumentos adicionales para inicializar el formulario.
        """
        kwargs = super().get_form_kwargs()
        provider_id = self.request.user.company_id  # El ID de la compañía del usuario actual
        kwargs["provider_id"] = provider_id
        return kwargs

    def get_context_data(self, **kwargs):
        """
        Agrega datos adicionales al contexto de la plantilla, como mapas, módulos
        y el color del botón del tema personalizado.

        Args:
            **kwargs: Argumentos adicionales para el contexto.

        Returns:
            dict: Contexto actualizado con la información adicional.
        """
        context = super().get_context_data(**kwargs)
        company_id = self.request.user.company_id

        # Añadir mapas y módulos relacionados a la compañía del usuario
        context["type_maps"] = CompanyTypeMap.objects.filter(company_id=company_id)
        context["modules"] = Module.objects.filter(company_id=company_id)

        # Obtener el tema personalizado para la compañía del usuario actual
        theme = self.request.user.company.theme_set.first()
        if theme:
            context["button_color"] = theme.button_color  # Asignar el color del botón

        # Añadir el ID de la compañía al contexto
        context.update({
            'company_id': company_id
        })
        return context

    def form_valid(self, form):
        """
        Guarda la nueva compañía y maneja la redirección dependiendo de los mapas
        asociados a la compañía.

        Args:
            form (Form): El formulario validado para crear la compañía.

        Returns:
            HttpResponse: Redirección a la URL de éxito o a la vista de KeyMapView.
        """
        with transaction.atomic():  # Ejecutar el proceso en una transacción atómica
            # Guardar la nueva compañía sin hacer commit
            company = form.save(commit=False)
            company.actived = True  # Activar la compañía por defecto
            company.provider_id = self.request.user.company_id  # Asignar proveedor
            company.modified_by = self.request.user  # Asignar el modificador
            company.created_by = self.request.user  # Asignar el creador

            # Si el usuario no es parte de la compañía principal (ID 1), asignar vendedor y consultor
            if self.request.user.company_id != 1:
                company.seller = self.request.user.company.seller
                company.consultant = self.request.user.company.consultant

            # Guardar la compañía en la base de datos
            company.save()
            form.save_m2m()  # Guardar las relaciones ManyToMany

            # Registrar en el log de auditoría llamando al form_valid de la clase base
            response = super().form_valid(form)

            # Verificar si la compañía tiene solo "OpenStreetMap"
            has_openstreetmap_only = MapType.objects.filter(
                companytypemap__company=company, name="OpenStreetMap"
            ).exists()

            if has_openstreetmap_only:
                # Si solo tiene "OpenStreetMap", redirigir directamente a la URL de éxito
                page_update = HttpResponse("")
                page_update["HX-Redirect"] = self.get_success_url()
                return page_update
            else:
                # Si hay otros mapas disponibles, redirigir a la vista `KeyMapView`
                return redirect("companies:KeyMapView", pk=company.pk)

class UpdateDistributionCompanyView(
    PermissionRequiredMixin,
    LoginRequiredMixin,
    UpdateAuditLogAsyncMixin,
    generic.UpdateView,
):
    """
    UpdateCompanyView es un generic.edit.UpdateView que usa el modelo Company,
    los campos enumerados,
    CompanyForm y el template_name_suffix para actualizar una empresa.
    """

    model = Company
    template_name = "whitelabel/companies/company_update.html"
    permission_required = "whitelabel.change_company"
    login_url = "login"
    form_class = DistributionCompanyForm

    def get_success_url(self):
        """
        Devuelve la URL de éxito para la redirección después de crear la compañía.

        Returns:
            str: La URL de redirección después de una creación exitosa.
        """
        return reverse("companies:companies")

    def get_context_data(self, **kwargs):
        """
        Añade al contexto información adicional para renderizar la plantilla,
        incluyendo mapas, módulos y la personalización del tema para la compañía.

        Args:
            **kwargs: Argumentos adicionales para el contexto.

        Returns:
            dict: Contexto actualizado con información adicional como mapas, módulos y temas.
        """
        context = super().get_context_data(**kwargs)
        user = self.request.user
        company_id = user.company_id

        # Obtener los mapas asociados a la compañía del usuario
        context["type_maps"] = CompanyTypeMap.objects.filter(company_id=company_id)
        
        # Obtener los módulos asociados a la compañía del usuario
        context["modules"] = Module.objects.filter(company__id=company_id)

        # Obtener el color del botón desde el tema asociado a la compañía
        theme = user.company.theme_set.first()
        context["button_color"] = theme.button_color if theme else "#000000"

        # Pasar el ID de la compañía al contexto
        context["company_id"] = company_id
        return context

    def form_valid(self, form):
        """
        Procesa el formulario cuando es válido. Activa la compañía por defecto, asigna
        valores al campo de creación y modificación, y maneja la redirección basada en 
        los mapas disponibles.

        Args:
            form (Form): El formulario validado.

        Returns:
            HttpResponse: Redirección a la URL de éxito o a la vista de `KeyMapView`.
        """
        # Activar la compañía por defecto
        form.instance.actived = True
        company = form.save(commit=False)

        # Asignar el usuario actual como creador y modificador
        company.modified_by = self.request.user
        company.created_by = self.request.user
        company.provider_id = None  # Es una distribuidora, por lo que no tiene proveedor

        # Guardar la compañía en la base de datos
        company.save()

        # Guardar las relaciones ManyToMany
        form.save_m2m()

        # Llamar al método de la clase base para el registro en el log de auditoría
        response = super().form_valid(form)

        # Si el ID de la compañía del usuario es 1, crear un tema por defecto si no existe
        if self.request.user.company_id == 1 and not Theme.objects.filter(company_id=company.id).exists():
            Theme.objects.create(company_id=company.id)

        # Comprobar si la compañía tiene solo "OpenStreetMap"
        has_openstreetmap_only = MapType.objects.filter(
            companytypemap__company=company, name="OpenStreetMap"
        ).exists()

        if has_openstreetmap_only:
            # Redirigir directamente a la URL de éxito si solo existe "OpenStreetMap"
            page_update = HttpResponse("")
            page_update["HX-Redirect"] = self.get_success_url()
            return page_update
        else:
            # Redirigir a la vista `KeyMapView` si hay otros mapas disponibles
            return redirect("companies:KeyMapView", pk=company.id)

class UpdateCustomerCompanyView(
    PermissionRequiredMixin,
    LoginRequiredMixin,
    UpdateAuditLogAsyncMixin,
    generic.UpdateView,
):
    """
    UpdateCompanyView es un generic.edit.UpdateView que usa el modelo Company,
    los campos enumerados,
    CompanyForm y el template_name_suffix para actualizar una empresa.
    """

    model = Company
    template_name = "whitelabel/companies/company_update.html"
    permission_required = "whitelabel.change_company"
    form_class = CompanyCustomerForm
    success_url = reverse_lazy("companies:companies")

    def get_success_url(self):
        """
        Devuelve la URL de éxito para redirigir tras la creación de la compañía.

        Returns:
            str: La URL de redirección tras una creación exitosa.
        """
        return reverse("companies:companies")

    def get_form_kwargs(self):
        """
        Pasa el `provider_id` de la compañía del usuario actual como argumento adicional al formulario.

        Returns:
            dict: Argumentos adicionales para inicializar el formulario.
        """
        kwargs = super().get_form_kwargs()
        provider_id = self.request.user.company_id  # El ID de la compañía del usuario actual
        kwargs["provider_id"] = provider_id
        return kwargs

    def get_context_data(self, **kwargs):
        """
        Agrega datos adicionales al contexto de la plantilla, como mapas, módulos
        y el color del botón del tema personalizado.

        Args:
            **kwargs: Argumentos adicionales para el contexto.

        Returns:
            dict: Contexto actualizado con la información adicional.
        """
        context = super().get_context_data(**kwargs)
        company_id = self.request.user.company_id

        # Añadir mapas y módulos relacionados a la compañía del usuario
        context["type_maps"] = CompanyTypeMap.objects.filter(company_id=company_id)
        context["modules"] = Module.objects.filter(company_id=company_id)

        # Obtener el tema personalizado para la compañía del usuario actual
        theme = self.request.user.company.theme_set.first()
        if theme:
            context["button_color"] = theme.button_color  # Asignar el color del botón

        # Añadir el ID de la compañía al contexto
        context.update({
            'company_id': company_id
        })
        return context

    def form_valid(self, form):
        """
        Guarda la nueva compañía y maneja la redirección dependiendo de los mapas
        asociados a la compañía.

        Args:
            form (Form): El formulario validado para crear la compañía.

        Returns:
            HttpResponse: Redirección a la URL de éxito o a la vista de KeyMapView.
        """
        with transaction.atomic():  # Ejecutar el proceso en una transacción atómica
            # Guardar la nueva compañía sin hacer commit
            company = form.save(commit=False)
            company.actived = True  # Activar la compañía por defecto
            company.provider_id = self.request.user.company_id  # Asignar proveedor
            company.modified_by = self.request.user  # Asignar el modificador
            company.created_by = self.request.user  # Asignar el creador

            # Si el usuario no es parte de la compañía principal (ID 1), asignar vendedor y consultor
            if self.request.user.company_id != 1:
                company.seller = self.request.user.company.seller
                company.consultant = self.request.user.company.consultant

            # Guardar la compañía en la base de datos
            company.save()
            form.save_m2m()  # Guardar las relaciones ManyToMany

            # Registrar en el log de auditoría llamando al form_valid de la clase base
            response = super().form_valid(form)

            # Verificar si la compañía tiene solo "OpenStreetMap"
            has_openstreetmap_only = MapType.objects.filter(
                companytypemap__company=company, name="OpenStreetMap"
            ).exists()

            if has_openstreetmap_only:
                # Si solo tiene "OpenStreetMap", redirigir directamente a la URL de éxito
                page_update = HttpResponse("")
                page_update["HX-Redirect"] = self.get_success_url()
                return page_update
            else:
                # Si hay otros mapas disponibles, redirigir a la vista `KeyMapView`
                return redirect("companies:KeyMapView", pk=company.pk)


class DeleteCompanyView(
    PermissionRequiredMixin,
    LoginRequiredMixin,
    generic.DeleteView,
):
    """
    Vista para eliminar una compañía. Requiere permisos y autenticación.

    Atributos:
        model (Model): El modelo que será eliminado, en este caso `Company`.
        template_name (str): Plantilla utilizada para confirmar la eliminación.
        permission_required (str): Permiso necesario para acceder a la vista.
        success_url (str): URL de redirección tras la eliminación exitosa.
    """
    model = Company
    template_name = "whitelabel/companies/company_delete.html"
    permission_required = "whitelabel.delete_company"
    success_url = reverse_lazy("companies:companies")

    def get_success_url(self):
        """
        Devuelve la URL de éxito para redirigir tras la eliminación de la compañía.

        Returns:
            str: La URL de redirección tras la eliminación exitosa.
        """
        return reverse("companies:companies")

    def form_valid(self, form):
        """
        Marca la respuesta como 204 (sin contenido) y agrega un encabezado HX-Redirect
        para redirigir tras la eliminación.

        Args:
            form (Form): El formulario de confirmación de eliminación.

        Returns:
            HttpResponse: La respuesta HTTP con el código 204 y encabezado HX-Redirect.
        """
        response = super().form_valid(form)
        response.status_code = 204  # Indica que la operación fue exitosa pero no hay contenido que devolver
        response['HX-Redirect'] = self.get_success_url()  # Redirige usando HTMX tras la eliminación
        return response

    def get_context_data(self, **kwargs):
        """
        Agrega al contexto los objetos relacionados que serán eliminados junto con la compañía.

        Args:
            **kwargs: Argumentos adicionales para el contexto.

        Returns:
            dict: Contexto actualizado con los objetos relacionados a la compañía.
        """
        context = super().get_context_data(**kwargs)
        company = self.get_object()  # Obtiene la compañía que se eliminará

        try:
            # Inicializa un recolector de objetos relacionados a eliminar
            collector = NestedObjects(using=DEFAULT_DB_ALIAS)
            collector.collect([company])  # Recolecta todos los objetos relacionados

            # Creamos un diccionario donde se almacenarán los objetos relacionados por modelo
            related_objects = {}

            # Recorremos los modelos y sus objetos relacionados
            for model, objects in collector.model_objs.items():
                model_name = model._meta.verbose_name_plural  # Nombre plural del modelo
                related_objects[model_name] = objects  # Asigna los objetos relacionados al diccionario

            # Agregamos los objetos relacionados al contexto para mostrarlos en la plantilla
            context['related_objects'] = related_objects

        except Exception as e:
            # En caso de error, mostrar el mensaje en la consola para depuración
            print(f"Error al obtener objetos relacionados: {e}")

        return context


class KeyMapView(LoginRequiredMixin, UpdateAuditLogAsyncMixin, generic.TemplateView):
    """
    Vista para actualizar las claves de los mapas de una compañía. 
    Requiere autenticación.
    """
    template_name = "whitelabel/companies/keymap.html"

    def get_success_url(self):
        """
        Devuelve la URL de éxito tras la actualización de los mapas.

        Returns:
            str: La URL a la que redirigir tras la actualización.
        """
        return reverse("companies:companies")

    def get_context_data(self, **kwargs):
        """
        Agrega los formularios para actualizar las claves de los mapas al contexto.

        Args:
            **kwargs: Argumentos adicionales de contexto.

        Returns:
            dict: Contexto actualizado con los formularios y la compañía.
        """
        context = super().get_context_data(**kwargs)
        company_id = self.kwargs.get("pk")
        company = get_object_or_404(Company, id=company_id)

        # Excluir los mapas con map_type_id=1 (p. ej., "OpenStreetMap")
        maps = CompanyTypeMap.objects.filter(company_id=company.id).exclude(map_type_id=1)

        # Crear un formulario para cada mapa, usando el prefijo del ID para diferenciarlos
        forms = [
            KeyMapForm(instance=map_instance, prefix=str(map_instance.id))
            for map_instance in maps
        ]

        # Actualizar el contexto con los formularios y la compañía
        context.update({"forms": forms, "company": company})
        return context

    def post(self, request, *args, **kwargs):
        """
        Maneja la lógica para actualizar las claves de los mapas.

        Args:
            request (HttpRequest): La solicitud HTTP.
            *args: Argumentos posicionales.
            **kwargs: Argumentos de palabra clave.

        Returns:
            HttpResponse: Respuesta con la redirección o renderizado en caso de error.
        """
        company_id = self.kwargs.get("pk")
        company = get_object_or_404(Company, id=company_id)

        # Filtrar los mapas de la compañía excluyendo map_type_id=1
        maps = CompanyTypeMap.objects.filter(company_id=company.id).exclude(map_type_id=1)

        # Cargar los formularios con los datos del POST
        forms = [
            KeyMapForm(request.POST, instance=map_instance, prefix=str(map_instance.id))
            for map_instance in maps
        ]

        # Verificar si todos los formularios son válidos
        all_valid = all([form.is_valid() for form in forms])

        if all_valid:
            # Guardar el estado anterior de los mapas para el registro de auditoría
            self.obj_before = list(maps)  
            self.obj_after = []  # Lista para almacenar el estado posterior de los objetos

            for form in forms:
                company_map = form.save(commit=False)  # Guardar sin hacer commit aún
                key_map = form.cleaned_data.get("key_map")

                if key_map:
                    # Encriptar la clave del mapa antes de guardarla
                    company_map.key_map = company_map.encrypt_key(key_map)

                company_map.save()  # Guardar el mapa actualizado en la base de datos
                self.obj_after.append(company_map)  # Agregar a la lista para la auditoría

            # Registrar la acción en el log de auditoría
            async_to_sync(self.log_action)()

            # Si todo es válido, redirigir usando HTMX
            page_update = HttpResponse("")
            page_update["HX-Redirect"] = self.get_success_url()
            return page_update
        else:
            # Si algún formulario no es válido, volver a renderizar la página con los errores
            context = {"forms": forms, "company": company}
            return render(request, self.template_name, context)

class UpdateCompanyLogoView(
    LoginRequiredMixin, UpdateAuditLogAsyncMixin, generic.UpdateView
):
    """
    Vista para actualizar el logotipo de una empresa. 

    Permite a los usuarios autenticados actualizar el logotipo de la empresa a la que tienen acceso.
    """
    model = Company
    template_name = "whitelabel/companies/company_update_logo.html"
    form_class = CompanyLogoForm

    def get_success_url(self):
        """
        Devuelve la URL a la que redirigir tras una actualización exitosa.

        Returns:
            str: La URL de redirección después de actualizar el logotipo.
        """
        return reverse("companies:companies")

    def form_valid(self, form):
        """
        Llamado cuando el formulario es válido.
        Actualiza el logotipo de la empresa y maneja la redirección usando HTMX.

        Args:
            form (CompanyLogoForm): El formulario con los datos válidos.

        Returns:
            HttpResponse: Respuesta con redirección HTMX.
        """
        # Asigna el usuario actual al campo 'modified_by' antes de guardar el formulario
        form.instance.modified_by = self.request.user
        form.save()  # Guarda los cambios en el logotipo

        # Llama al método form_valid de la clase padre para registrar la acción en el log de auditoría
        response = super().form_valid(form)

        # Respuesta HTMX para redirigir después de una actualización exitosa
        page_update = HttpResponse("")
        page_update["HX-Redirect"] = self.get_success_url()
        return page_update

    def form_invalid(self, form):
        """
        Llamado cuando el formulario es inválido.
        Renderiza nuevamente la página con el formulario que contiene errores.

        Args:
            form (CompanyLogoForm): El formulario con errores.

        Returns:
            HttpResponse: Respuesta con el formulario inválido renderizado.
        """
        return render(self.request, self.template_name, {"form": form})


class ThemeView(PermissionRequiredMixin, LoginRequiredMixin, UpdateAuditLogAsyncMixin, generic.UpdateView):
    """
    Vista que permite manejar la actualización y creación del tema de una empresa.

    Si el tema existe, renderiza la plantilla para actualizarlo.
    Si el tema no existe, lo crea y luego renderiza la plantilla para actualizarlo.

    Atributos:
        model (Model): El modelo de datos para el tema.
        template_name (str): La plantilla HTML que se usa para renderizar la vista.
        permission_required (str): El permiso necesario para acceder a esta vista.
        form_class (Form): El formulario para el tema.
        success_url (str): URL de redirección después de una actualización exitosa.
    """

    model = Theme
    template_name = "whitelabel/theme/theme.html"
    permission_required = ("whitelabel.add_theme", "whitelabel.change_theme")
    form_class = ThemeForm
    success_url = reverse_lazy("companies:companies")
    
    def get_context_data(self, **kwargs):
        """
        Proporciona datos adicionales al contexto de la plantilla.

        Args:
            **kwargs: Argumentos adicionales que se pasan a la función.

        Returns:
            dict: Contexto adicional para la plantilla, incluyendo el formulario con los valores iniciales.
        """
        context = super().get_context_data(**kwargs)
        theme = self.get_theme()
        context['form'].fields['opacity'].initial = self.convert_opacity_to_decimal(theme.opacity)
        return context

    def get_theme(self):
        """
        Obtiene el tema de la empresa actual del usuario.

        Returns:
            Theme: El objeto de tema correspondiente a la empresa del usuario.
        """
        return Theme.objects.get(company_id=self.request.user.company_id)

    def convert_opacity_to_decimal(self, opacity):
        """
        Convierte la opacidad de hexadecimal a decimal.

        Args:
            opacity (str): El valor de opacidad en formato hexadecimal.

        Returns:
            int: El valor de opacidad en formato decimal.
        """
        return int(opacity, 16)

    def post(self, request, *args, **kwargs):
        """
        Maneja la solicitud POST para actualizar o crear el tema.

        Args:
            request (HttpRequest): El objeto de solicitud HTTP.
            *args: Argumentos adicionales que se pasan a la función.
            **kwargs: Argumentos clave adicionales que se pasan a la función.

        Returns:
            HttpResponse: Redirección a la vista del tema actualizado o renderiza el formulario con errores.
        """
        theme = self.get_theme()
        form = self.form_class(request.POST, request.FILES, instance=theme)

        if form.is_valid():
            theme = form.save(commit=False)
            self.process_opacity(theme, form)
            self.process_images(theme, request)
            theme.save()
            return redirect(reverse("companies:theme", kwargs={"pk": theme.pk}))

        return render(request, self.template_name, {"form": form})

    def process_opacity(self, theme, form):
        """
        Procesa y valida el valor de opacidad proporcionado en el formulario.

        Args:
            theme (Theme): El objeto de tema que se está actualizando.
            form (Form): El formulario con los datos del tema.
        """
        opacity = theme.opacity
        try:
            opacity_decimal = int(opacity)
            if 0 <= opacity_decimal <= 255:
                form.instance.opacity = "{:02x}".format(opacity_decimal)
            else:
                raise ValueError("El valor está fuera del rango permitido (0-255).")
        except ValueError:
            try:
                opacity_decimal = int(opacity, 16)
                if 0 <= opacity_decimal <= 255:
                    form.instance.opacity = opacity
                else:
                    raise ValueError("El valor hexadecimal está fuera del rango permitido (00-FF).")
            except ValueError:
                raise ValueError("El valor proporcionado para la opacidad no es válido.")

    def process_images(self, theme, request):
        """
        Procesa y guarda las imágenes recortadas proporcionadas en el formulario.

        Args:
            theme (Theme): El objeto de tema que se está actualizando.
            request (HttpRequest): El objeto de solicitud HTTP.
        """
        for field in ["sidebar_image", "lock_screen_image"]:
            cropped_image_key = f"id_{field}_cropped"
            if cropped_image_key in request.POST and request.POST[cropped_image_key]:
                self.save_cropped_image(request, theme, field, cropped_image_key)

    def save_cropped_image(self, request, theme, field, cropped_image_key):
        """
        Guarda la imagen recortada proporcionada en el formulario.

        Args:
            request (HttpRequest): El objeto de solicitud HTTP.
            theme (Theme): El objeto de tema que se está actualizando.
            field (str): El campo de imagen que se está actualizando.
            cropped_image_key (str): La clave de la imagen recortada en la solicitud POST.
        """
        format, imgstr = request.POST[cropped_image_key].split(";base64,")
        ext = format.split("/")[-1]
        data = base64.b64decode(imgstr)

        file_name = f"{field}_{theme.company.id}.{ext}"
        file_path = os.path.join("uploads", file_name)

        old_image = getattr(theme, field)
        if old_image:
            file_name, file_path = self.check_image_usage(theme, field, old_image, file_name, ext)

        default_storage.save(file_path, ContentFile(data))
        setattr(theme, field, file_path)

    def check_image_usage(self, theme, field, old_image, file_name, ext):
        """
        Verifica si la imagen anterior está siendo usada por otros temas y actúa en consecuencia.

        Args:
            theme (Theme): El objeto de tema que se está actualizando.
            field (str): El campo de imagen que se está actualizando.
            old_image (File): La imagen anterior del campo.
            file_name (str): El nombre del archivo nuevo.
            ext (str): La extensión del archivo nuevo.

        Returns:
            tuple: El nombre y la ruta del archivo a guardar.
        """
        other_themes = Theme.objects.filter(**{f"{field}__name": old_image.name}).exclude(company=theme.company)
        if other_themes.exists():
            unique_suffix = f"_{theme.company.id}"
            file_name = f"{field}{unique_suffix}.{ext}"
            file_path = os.path.join("uploads", file_name)
        else:
            default_storage.delete(old_image.name)
            file_path = os.path.join("uploads", file_name)
        return file_name, file_path


class ModuleTemplateView(PermissionRequiredMixin, LoginRequiredMixin, ListView):
    """
    Vista como clase que renderiza el template HTML que contiene la lista de modulos de cada empresa.
    """

    model = Module
    template_name = "whitelabel/module/main_module.html"
    login_url = "login"
    permission_required = "whitelabel.view_module"

    def get_paginate_by(self, queryset):
        """
        Obtiene el número de elementos a mostrar por página.

        Args:
            queryset (QuerySet): El conjunto de datos de la consulta.

        Returns:
            int: El número de elementos a mostrar por página.
        """
        user = self.request.user
        params = self.request.GET if self.request.method == 'GET' else self.request.POST
        if 'order_by' not in params and 'paginate_by' not in params and 'page' not in params:
            # Limpiar los filtros de la sesión
            if f"filters_sorted_module_{user.id}" in self.request.session:
                del self.request.session[f"filters_sorted_module_{user.id}"]
                self.request.session.modified = True
        paginate_by = self.request.POST.get('paginate_by', None)  # Obtener paginate_by de los parámetros GET

        if paginate_by is None:
            session_filters = self.request.session.get(
                f"filters_sorted_module_{self.request.user.id}", {}
            )
            paginate_by = session_filters.get("paginate_by", 10)
            # Convertir a entero si es una lista
            try:
                paginate_by = int(
                    paginate_by[0]
                )  # Convertir el primer elemento de la lista a entero
            except (TypeError, ValueError):
                paginate_by = int(paginate_by) if paginate_by else 10
            # Añadir paginate_by a self.request.GET para asegurar que esté presente
            self.request.POST = self.request.POST.copy()
            self.request.POST['paginate_by'] = paginate_by
        return int(self.request.POST['paginate_by'])
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        list_price = []
        params = self.request.GET if self.request.method == 'GET' else self.request.POST
        query = params.get("query", "").lower()
        search = params.get("q", query).lower()
        if 'order_by' not in params and 'paginate_by' not in params and 'page' not in params:
            # Limpiar los filtros de la sesión
            if f"filters_sorted_module_{user.id}" in self.request.session:
                del self.request.session[f"filters_sorted_module_{user.id}"]
                self.request.session.modified = True
        session_filters = self.request.session.get(
                f"filters_sorted_module_{self.request.user.id}", {})
        paginate_by = self.request.POST.get('paginate_by', None)
        if paginate_by is None:
            paginate_by = session_filters.get("paginate_by", 10)
            # Convertir a entero si es una lista
            try:
                paginate_by = int(
                    paginate_by[0]
                )  # Convertir el primer elemento de la lista a entero
            except (TypeError, ValueError):
                paginate_by = int(paginate_by) if paginate_by else 10
            # Añadir paginate_by a self.request.GET para asegurar que esté presente
            self.request.POST = self.request.POST.copy()
            self.request.POST['paginate_by'] = paginate_by
        # Parámetros de ordenamiento por defecto
        order_by = self.request.GET.get('order_by') or self.request.POST.get('order_by') or session_filters.get('order_by', ['company_name'])[0]
        direction = self.request.GET.get('direction') or self.request.POST.get('direction') or session_filters.get('direction', ['asc'])[0]
        # Actualizar los filtros con los parámetros actuales de la solicitud GET
        session_filters.update(params)
        # Actualizar los filtros de la sesión con los nuevos parámetros
        self.request.session[
            f"filters_sorted_module_{user.id}"
        ] = session_filters
        self.request.session.modified = True
        queryset = get_modules_by_user(user.company_id, user.id, search)
        # Subconsulta para calcular el total_price por compañía
        total_price_subquery = (
            Module.objects.filter(company_id=OuterRef("id"))
            .values("company_id")
            .annotate(total_price=Sum("price"))
            .values("total_price")
        )

        # Anotar el nombre de la moneda y el total_price
        annotated_queryset = Company.objects.filter(
            visible=True, actived=True, id__in=[company["id"] for company in queryset]
        ).annotate(
            coin_name=F("coin__name"),  # Asegúrate de que la relación esté correcta
            total_price=Subquery(total_price_subquery),
        )

        # Mapeo de los campos de ordenamiento permitidos
        order_by_mapping = {
            "company_name": "company_name",
            "coin": "coin_name",
            "total_price": "total_price",
        }

        # Validar el campo de ordenamiento
        order_field = order_by_mapping.get(order_by, "company_name")

        # Determinar el prefijo de ordenamiento
        order_prefix = "-" if direction == "desc" else ""

        # Ordenar por el campo especificado y dirección
        sorted_queryset = annotated_queryset.order_by(f"{order_prefix}{order_field}")

        # Paginación de compañías
        paginator = Paginator(sorted_queryset, paginate_by)
        page_number = self.request.POST.get('page', 1)
        page_obj = paginator.get_page(page_number)
        context["page_obj"] = page_obj

        # Cargar módulos asociados y calcular precios
        for company in page_obj:
            modules = Module.objects.filter(company_id=company.id)
            total_price = (
                modules.aggregate(total_price=Sum("price"))["total_price"] or 0
            )
            list_price.append({"company_id": company.id, "total_price": total_price})

        context["list_price"] = list_price
        context["company"] = page_obj
        context["paginate_by"] = paginate_by
        context['order_by'] = order_by
        context['direction'] = direction
        context["object_list"] = Module.objects.filter(
            company_id__in=[company.id for company in page_obj]
        )
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

class UpdateModuleView(PermissionRequiredMixin, LoginRequiredMixin, generic.UpdateView):
    model = Module
    template_name = "whitelabel/module/update_module.html"
    permission_required = "whitelabel.change_module"
    form_class = Moduleform
    success_url = reverse_lazy("companies:module")
    action = "update"

    def get_success_url(self):
        return reverse("companies:module")

    def get(self, request, *args, **kwargs):
        company_id = self.kwargs.get("pk")
        company = get_object_or_404(Company, id=company_id)
        modules = Module.objects.filter(company_id=company.id)

        self.obj_before = copy.deepcopy(list(modules))
        forms = [self.form_class(instance=module) for module in modules]

        return render(request, self.template_name, {"forms": forms, "company": company})

    def post(self, request, *args, **kwargs):
        company_id = self.kwargs.get("pk")
        company = get_object_or_404(Company, id=company_id)
        price_list = request.POST.getlist("price")
        id_list = request.POST.getlist("id")
        count = 0

        errors = []
        self.obj_before = []
        self.obj_after = []

        for pk in id_list:
            try:
                module = Module.objects.get(id=pk)
            except Module.DoesNotExist:
                raise Http404(f"Module with id {pk} does not exist")

            try:
                self.obj_before.append(copy.deepcopy(module))
                module.price = Decimal(price_list[count])
                module.modified_by = request.user
                module.save()
                self.obj_after.append(copy.deepcopy(module))
            except (InvalidOperation, ValueError) as e:
                errors.append(f"El valor '{price_list[count]}' no es un número decimal válido. Error: {str(e)}")
            count += 1

        if errors:
            modules = Module.objects.filter(company_id=company.id)
            forms = [self.form_class(instance=module) for module in modules]
            return render(request, self.template_name, {"forms": forms, "company": company, "errors": errors})

        response = HttpResponse("")
        response["HX-Redirect"] = self.get_success_url()
        # Se revisa la existencia del método log_action
        if hasattr(self, 'log_action'):
            async_to_sync(self.log_action)()
        else:
            print("log_action no está definido en la clase.")
        return response

    def form_valid(self, form):
        self.obj_after = form.instance
        if hasattr(self, 'log_action'):
            async_to_sync(self.log_action)()
        else:
            print("log_action no está definido en la clase.")
        return super().form_valid(form)


class ListProcessAddView(
    PermissionRequiredMixin,
    LoginRequiredMixin,
    CreateAuditLogAsyncMixin,
    generic.CreateView,
    generic.ListView,
):
    template_name = "whitelabel/process/main_process.html"
    permission_required = "whitelabel.add_company"
    form_class = ProcessForm
    model = Process
    paginate_by = 10  # Establece un valor por defecto para la paginación

    def get_success_url(self):
        return reverse("companies:process")

    def get_paginate_by(self, queryset):
        paginate_by = self.request.GET.get("paginate_by", self.paginate_by)
        try:
            return int(paginate_by)
        except (ValueError, TypeError):
            return self.paginate_by

    def get_queryset(self):
        user = self.request.user
        return Process.objects.filter(company=user.company, visible=True).order_by(
            "process_type"
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        first_process = (
            Process.objects.filter(company=user.company, visible=True)
            .order_by("id")
            .first()
        )
        companies = get_user_companies(user)
        if user.company_id == 1:
            context["form"].fields["company"].choices = companies
        else:
            context["form"].fields["company"].queryset = companies

        paginator = Paginator(self.get_queryset(), self.get_paginate_by(None))
        page = self.request.GET.get("page")
        context["page_obj"] = paginator.get_page(page)
        context["object_list"] = context["page_obj"].object_list

        page_number = context["page_obj"].number if context["page_obj"] else 1
        context["start_number"] = (page_number - 1) * self.get_paginate_by(None)
        button_color = self.request.user.company.theme_set.all().first().button_color
        context["button_color"] = button_color
        
        context["process_admin"] = first_process.id
        return context

    def form_valid(self, form):
        form.instance.modified_by = self.request.user
        form.instance.created_by = self.request.user
        form.save()
        return redirect(self.get_success_url())


class UpdateProcessView(
    PermissionRequiredMixin,
    LoginRequiredMixin,
    UpdateAuditLogAsyncMixin,
    generic.UpdateView,
):
    """
    Vista de actualización de proceso.

    Esta vista permite actualizar un proceso existente en el sistema.
    Requiere permisos de cambio de proceso y autenticación de inicio de sesión.
    Utiliza el formulario ProcessForm para validar y guardar los datos del proceso.
    Después de una actualización exitosa, redirige a la lista de procesos.

    Atributos:
        template_name (str): Nombre de la plantilla HTML para renderizar la vista.
        permission_required (str): Permiso requerido para acceder a la vista.
        form_class (Form): Clase del formulario utilizado para validar los datos del proceso.
        model (Model): Modelo del proceso que se va a actualizar.
        success_url (str): URL a la que se redirige después de una actualización exitosa.

    Métodos:
        get_context_data(**kwargs): Retorna el contexto de datos para renderizar la vista.
        form_valid(form): Guarda los datos del formulario y retorna una respuesta HTTP.

    """

    template_name = "whitelabel/process/update_process.html"
    permission_required = "whitelabel.change_company"
    form_class = ProcessForm
    model = Process

    def get_success_url(self):
        return reverse("companies:process")

    def get_context_data(self, **kwargs):
        """
        Retorna el contexto de datos para renderizar la vista.

        Args:
            **kwargs: Argumentos clave adicionales.

        Returns:
            dict: Contexto de datos para renderizar la vista.

        """
        context = super().get_context_data(**kwargs)
        companies = get_user_companies(self.request.user)
        if self.request.user.company_id == 1:
            context["form"].fields["company"].choices = companies
        else:
            context["form"].fields["company"].queryset = companies
        button_color = self.request.user.company.theme_set.all().first().button_color
        context["button_color"] = button_color
        return context

    def form_valid(self, form):
        """
        Guarda los datos del formulario y retorna una respuesta HTTP.

        Args:
            form (Form): Formulario con los datos del proceso.

        Returns:
            HttpResponse: Respuesta HTTP con estado 204 (Sin contenido) y encabezados adicionales.

        """

        form.instance.modified_by = self.request.user
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        return redirect(self.get_success_url())


class DeleteProcessView(
    PermissionRequiredMixin,
    LoginRequiredMixin,
    DeleteAuditLogAsyncMixin,
    generic.UpdateView,
):
    """
    Vista de clase para eliminar un proceso.

    Esta vista se utiliza para eliminar un proceso existente en la aplicación.
    Requiere permisos de eliminación y autenticación del usuario.

    Atributos:
        model (Model): El modelo de datos asociado a la vista.
        template_name (str): El nombre de la plantilla HTML utilizada para renderizar la vista.
        permission_required (str): El permiso requerido para acceder a la vista.
        fields (list): La lista de campos del modelo que se mostrarán en el formulario.

    Métodos:
        form_valid(form): Método que se ejecuta cuando el formulario es válido.
            Actualiza el campo 'visible' del proceso a False y guarda los cambios.
            Retorna una respuesta HTTP con el código de estado 204 y el encabezado "HX-Trigger: ListprocessChanged".
    """

    model = Process
    template_name = "whitelabel/process/delete_process.html"
    permission_required = "whitelabel.delete_company"
    fields = ["visible"]

    def get_success_url(self):
        return reverse("companies:process")

    def form_valid(self, form):
        """
        Método que se ejecuta cuando el formulario es válido.

        Actualiza el campo 'visible' del proceso a False y guarda los cambios.
        Retorna una respuesta HTTP con el código de estado 204 y el encabezado "HX-Trigger:
        ListprocessChanged".

        Parámetros:
            form (Form): El formulario válido.

        Retorna:
            HttpResponse: La respuesta HTTP con el código de estado 204 y el encabezado "HX-Trigger
            : ListprocessChanged".
        """
        form.instance.visible = False
        # Llama al método form_valid de la clase padre para registrar la acción en el log de auditoría
        response = super().form_valid(form)
        return redirect(self.get_success_url())


class ListTicketTemplate(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """
    Class-based view that renders the HTML template containing the list of tickets.
    """

    model = Ticket
    template_name = "whitelabel/tickets/main_ticket.html"
    permission_required = "whitelabel.view_ticket"

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
                f"filters_sorted_ticketsopen_{self.request.user.id}", {}
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
        tickets = get_ticket_by_user(user.id)
        params = self.request.GET if self.request.method == 'GET' else self.request.POST
        query = params.get("query", "").lower()
        search = params.get("q", "").lower()

        if "query" in params:
            tickets = [
                ticket
                for ticket in tickets
                if (
                    query in str(ticket.get("id", "")).lower()
                    or query in str(ticket.get("subject", "")).lower()
                    or query in str(ticket.get("company", "")).lower()
                    or query in str(ticket.get("process_type", "")).lower()
                    or query in str(ticket.get("created_by", "")).lower()
                )
            ]
        if search:
            tickets = [
                ticket
                for ticket in tickets
                if (
                    query in str(ticket.get("id", "")).lower()
                    or query in str(ticket.get("subject", "")).lower()
                    or query in str(ticket.get("company", "")).lower()
                    or query in str(ticket.get("process_type", "")).lower()
                    or query in str(ticket.get("created_by", "")).lower()
                )
            ]

        tickets.sort(
            key=lambda ticket: ticket["last_comment"] or datetime.min, reverse=True
        )

        # Parámetros de ordenamiento por defecto
        order_by = params.get("order_by", "last_comment")
        direction = params.get("direction", "desc")
        if 'order_by' not in params and 'paginate_by' not in params and 'page' not in params:
            # Limpiar los filtros de la sesión
            if f"filters_sorted_ticketsopen_{user.id}" in self.request.session:
                del self.request.session[f"filters_sorted_ticketsopen_{user.id}"]
                self.request.session.modified = True
        # Recuperar filtros almacenados en la sesión
        session_filters = self.request.session.get(f'filters_sorted_ticketsopen_{user.id}', {})
        order_by = params.get('order_by', session_filters.get('order_by', ['last_comment'])[0])
        direction = params.get('direction', session_filters.get('direction',['desc'])[0])
        # Actualizar los filtros con los parámetros actuales de la solicitud GET
        session_filters.update(params)
        # Actualizar los filtros de la sesión con los nuevos parámetros
        self.request.session[
            f"filters_sorted_ticketsopen_{user.id}"
        ] = session_filters
        self.request.session.modified = True
        # Función para convertir los valores a minúsculas y extraer números cuando sea necesario
        def sort_key(x):
            value = x.get(order_by)
            if value is None or value == "":
                return (4, "")  # Prioridad 4 para valores nulos o vacíos
            if isinstance(value, str):
                # Verificar si comienza con números, letras o caracteres especiales
                if value[0].isdigit():
                    return (1, extract_number(value))  # Prioridad 1 para números
                elif value[0].isalpha():
                    return (2, value.lower())  # Prioridad 2 para letras
                else:
                    return (3, value.lower())  # Prioridad 3 para caracteres especiales
            return value

        # Determinar si es orden descendente
        reverse = direction == "desc"

        try:
            sorted_queryset = sorted(tickets, key=sort_key, reverse=reverse)
        except KeyError:
            # Ordenamiento por defecto si la clave no existe
            sorted_queryset = sorted(
                tickets, key=lambda x: x["last_comment"].lower(), reverse=reverse
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
        session_filters = self.request.session.get(f'filters_sorted_ticketsopen_{self.request.user.id}', {})
        # Obtener el ordenamiento desde la solicitud actual
        order_by = self.request.GET.get('order_by') or self.request.POST.get('order_by') or session_filters.get('order_by', ['last_comment'])[0]
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
    
from django.core.mail import EmailMessage
from django.template.loader import render_to_string

from config.settings import EMAIL_HOST_USER


def sending_mail(email, ticket,asunto, message, user, prioridad, attachments=None):
    # Renderizar el mensaje HTML con los datos proporcionados
    confirmation_html_message = render_to_string('whitelabel/tickets/confirmation_email.html', {'message': message, 'ticket': ticket, 'asunto': asunto})
    
    # Crear el correo
    confirmation_email = EmailMessage(
        f"{ticket} {asunto} {prioridad}",  # Asunto del correo
        confirmation_html_message,  # Mensaje HTML
        EMAIL_HOST_USER,  # Remitente
        [email]  # Destinatario
    )
    confirmation_email.content_subtype = 'html'
    
    # Añadir adjuntos
    if attachments:
        for attachment in attachments:
            confirmation_email.attach(attachment.name, attachment.read(), attachment.content_type)
    
    confirmation_email.send()
    
class CreateTicketView(
    PermissionRequiredMixin,
    LoginRequiredMixin,
    CreateAuditLogSyncMixin,
    generic.CreateView,
):
    """
    Vista de creación de tickets.

    Esta vista permite a los usuarios crear nuevos tickets. Hereda de la clase CreateView de Django
    y utiliza el formulario TicketCrearte para la validación de datos.

    Atributos:
        template_name (str): El nombre de la plantilla HTML utilizada para renderizar la vista.
        form_class (Form): La clase del formulario utilizado para la validación de datos.

    Métodos:
        get_success_url(): Retorna la URL a la que se redirige después de crear exitosamente un ticket.
        get_context_data(**kwargs): Retorna el contexto de datos utilizado para renderizar la vista.
        handle_attachment_errors(form, attachment_form): Maneja los errores relacionados con los archivos adjuntos.
        form_valid(form): Maneja la lógica cuando el formulario es válido.
    """

    template_name = "whitelabel/tickets/add_ticket.html"
    form_class = TicketCrearte
    permission_required = "whitelabel.add_ticket"

    def get_success_url(self):
        """
        Retorna la URL a la que se redirige después de crear exitosamente un ticket.
        """
        return reverse_lazy("companies:main_ticket")

    def get_context_data(self, **kwargs):
        """
        Retorna el contexto de datos utilizado para renderizar la vista.

        Args:
            **kwargs: Argumentos clave adicionales.

        Returns:
            dict: El contexto de datos utilizado para renderizar la vista.
        """
        context = super().get_context_data(**kwargs)
        user = self.request.user
        company = self.request.user.company
        provider = company.provider_id
        if provider is None:
            provider = 1
        context["company"] = company.id
        context["provider"] = provider
        context["message_form"] = MessageForm()
        context["attachment_form"] = AttachmentForm()
        button_color = self.request.user.company.theme_set.all().first().button_color
        context["button_color"] = button_color
        return context

    def handle_attachment_errors(self, form, attachment_form):
        """
        Maneja los errores relacionados con los archivos adjuntos.

        Verifica el tamaño y el formato de los archivos adjuntos y muestra mensajes de error si es necesario.

        Args:
            form (Form): El formulario principal.
            attachment_form (Form): El formulario de archivos adjuntos.

        Returns:
            None: Si no hay errores relacionados con los archivos adjuntos.
            HttpResponse: Si hay errores relacionados con los archivos adjuntos y se devuelve una respuesta HTTP.
        """
        files = self.request.FILES.getlist("file")
        total_size = sum(file.size for file in files) / (1024 * 1024)
        if total_size > 7:
            messages.error(
                self.request,
                "El tamaño total de los archivos adjuntos no puede superar los 7 MB.",
            )
            return self.form_invalid(form)

        allowed_formats = [
            "cfg",
            "csv",
            "doc",
            "docx",
            "eml",
            "exe",
            "jpeg",
            "jpg",
            "mp4",
            "msg",
            "pdf",
            "png",
            "rar",
            "txt",
            "xim",
            "xls",
            "xlsx",
            "xml",
            "zip",
        ]
        for file in files:
            file_extension = file.name.split(".")[-1].lower()
            if file_extension not in allowed_formats:
                messages.error(
                    self.request,
                    f"El formato de archivo '{file.name}' no está permitido.",
                )
                return self.form_invalid(form)

        return None

    def form_valid(self, form):
        """
        Maneja la lógica cuando el formulario es válido.

        Realiza las siguientes acciones:
        - Asigna el usuario actual y la compañía al ticket.
        - Asigna la compañía proveedora seleccionada al ticket si se proporciona.
        - Maneja los errores relacionados con los archivos adjuntos.
        - Guarda el ticket.
        - Guarda el mensaje asociado al ticket.
        - Guarda los archivos adjuntos asociados al ticket.

        Args:
            form (Form): El formulario válido.

        Returns:
            HttpResponse: Una respuesta HTTP vacía con una cabecera de redirección a la URL de éxito.
        """
        company = self.request.user.company
        form.instance.created_by = self.request.user
        form.instance.company = company
        selected_provider_id = self.request.POST.get("id_distributor")

        if selected_provider_id:
            selected_provider = get_object_or_404(Company, id=selected_provider_id)
            form.instance.provider_company = selected_provider
            form.instance.company = selected_provider

        if not selected_provider_id and "id_interns" in self.request.POST:
            # Verifica si company_id_tk existe en la columna provider del modelo Company
            is_provider = Company.objects.filter(provider=company.id).exists()
            if is_provider:
                form.instance.provider_company = company
            else:
                form.instance.customer_company = company
            form.instance.company = company

        attachment_form = AttachmentForm(self.request.POST, self.request.FILES)
        attachment_error = self.handle_attachment_errors(form, attachment_form)
        if attachment_error:
            return attachment_error

        # Verificar si el formulario es válido
        if not form.is_valid():
            print("Form is not valid:", form.errors)
            return self.form_invalid(form)

        # Guardar el ticket primero
        ticket = super().form_valid(form)
        # Obtener el número de mensajes del ticket
        message_count = self.object.messages.count()

        # Guardar el mensaje
        message_form = MessageForm(self.request.POST)
        if message_form.is_valid():
            message = message_form.save(commit=False)
            message.user = self.request.user
            message.ticket = self.object
            message_count += 1
            message.number = message_count
            message.save()
        else:
            print("Message form is not valid:", message_form.errors)

        # Guardar los adjuntos
        files = self.request.FILES.getlist("file")
        attachments = []
        for file in files:
            new_file_name = f"{self.object.id}_{message_count}_{file.name}"
            file.name = new_file_name
            attachment = Attachment.objects.create(
                ticket=self.object, file=file, message=message
            )
            attachments.append(attachment)

        # Registrar la acción en el log de auditoría con datos adicionales
        self.log_additional_data(form, message_form, attachments)
        
        # # Llamar a la función de envío de correo
        # sending_mail(
        # email=self.request.user.email,
        # ticket=str(self.object.id),
        # asunto=form.cleaned_data['subject'],
        # message=message.text,
        # user=self.request.user,
        # prioridad=form.cleaned_data['priority'],
        # attachments=files
        # )
        # Prepara una respuesta con redirección usando HTMX
        page_update = HttpResponse("")
        page_update["HX-Redirect"] = self.get_success_url()
        return page_update

    def log_additional_data(self, ticket_form, message_form, attachments):
        """
        Registra los datos adicionales en el log de auditoría.
        """
        user = self.request.user
        company_id = getattr(user, "company_id", None)
        view_name = self.__class__.__name__
        ip_address = asyncio.run(obtener_ip_publica(self.request))

        before = {}
        after = {
            "ticket": model_to_dict(ticket_form.instance),
            "message": model_to_dict(message_form.instance)
            if message_form.is_valid()
            else {},
            "attachments": [model_to_dict(att) for att in attachments],
        }

        before_json = json.dumps(before, default=str)
        after_json = json.dumps(after, default=str)

        log_action(
            user=user,
            company_id=company_id,
            view_name=view_name,
            action="create",
            before=before_json,
            after=after_json,
            ip_address=ip_address,
        )


class ViewTicketView(
    LoginRequiredMixin,
    PermissionRequiredMixin,
    CreateAuditLogSyncMixin,
    generic.DetailView,
):
    model = Ticket
    template_name = "whitelabel/tickets/view_ticket.html"
    context_object_name = "ticket"
    permission_required = "whitelabel.change_ticket"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user  # Obtener el usuario actual
        company = self.request.user.company
        company_queryset = Company.objects.filter(
            id=company.id, visible=True, actived=True
        )

        # Obtener las compañías proveedoras y clientes finales
        if user.company.id == 1:  # Si la empresa es la principal (Condicional para AZ)
            # Obtener todos los clientes distribuidores y clientes finales
            provider_companies = Company.objects.filter(
                provider=None, visible=True, actived=True
            )
            customer_companies = Company.objects.filter(
                provider=user.company, visible=True, actived=True
            )

        # Lógica para que le muestre a la empresa distribuidora solo a su proveedor
        elif self.object.company.provider is None:
            # Obtener las compañías proveedoras y las compañías de clientes del usuario actual
            provider_companies = Company.objects.filter(
                id=1, visible=True, actived=True
            )
            customer_companies = Company.objects.filter(
                provider=user.company, visible=True, actived=True
            ).exclude(id=user.company_id)

        # Lógica para que le muestre a la empresa final solo a su proveedor
        elif self.object.company.provider is not None:
            provider_companies = Company.objects.filter(
                customer=user.company, visible=True, actived=True
            )
            customer_companies = Company.objects.filter(
                provider=user.company, visible=True, actived=True
            ).exclude(customer=user.company)
        first_process = (
            Process.objects.filter(company=user.company, visible=True)
            .order_by("id")
            .first()
        )
        if first_process == user.process_type:
            context["process_user"] = 1
        else:
            context["process_user"] = 0
        context["has_provider"] = company.provider is not None
        if user.company.id == 1:
            company_all = Company.objects.filter(visible=True, actived=True)
            combined_companies = []
            for company in company_all:
                if company.provider_id:
                    provider_company = Company.objects.filter(
                        id=company.provider_id, visible=True, actived=True
                    ).first()
                    modified_name = (
                        f"{company.company_name} -- {provider_company.company_name}"
                        if provider_company
                        else company.company_name
                    )
                else:
                    modified_name = company.company_name
                combined_companies.append((company.id, modified_name))
        else:
            combined_companies = list(
                (provider_companies | customer_companies | company_queryset)
                .distinct()
                .values_list("id", "company_name")
            )

        combined_companies = sorted(combined_companies, key=lambda x: x[1])
        context["provider_companies"] = combined_companies

        # Obtener la compañía y el proceso del ticket
        company_tk = self.object.company
        process = self.object.process_type

        context["form"] = TicketForm(
            instance=self.object,
            company=company,
            company_tk=company_tk,
            process=process,
        )

        context["messages"] = self.object.messages.all().order_by(
            "-created_at"
        )  # Agregar los mensajes al contexto

        context["attachments"] = (
            self.object.attachments.all() if self.object.attachments.exists() else []
        )  # Agregar los adjuntos al contexto
        context[
            "message_form"
        ] = MessageForm()  # Agregar el formulario de comentario al contexto
        context[
            "attachment_form"
        ] = AttachmentForm()  # Agregar el formulario de adjunto al contexto

        # Nueva variable para indicar si el ticket está cerrado
        context["ticket_closed"] = not self.object.status

        context["process"] = process
        context["company"] = company_tk

        return context

    def post(self, request, *args, **kwargs):
        send = False
        close_ticket = False
        if request.POST.get("Send"):
            send = True
        if request.POST.get("close_ticket"):
            close_ticket = True
        self.object = self.get_object()
        id_ticket = self.object.id
        user_tk = self.object.assign_to_id

        if request.POST.get("Reopen"):
            # Actualiza el estado del ticket y guarda los cambios (Reabrir)
            self.object.status = True
            self.object.closed_at = None
            self.object.save()
            page_update = HttpResponse("")
            page_update["HX-Redirect"] = self.get_success_url_closed()

            return page_update

        # Obtén el objeto Ticket con el id específico
        ticket = Ticket.objects.get(id=id_ticket)

        # Accede al campo company_id del objeto Ticket
        company_id_tk = ticket.company_id

        # Verifica si company_id_tk existe en la columna provider del modelo Company
        is_provider = Company.objects.filter(
            provider=company_id_tk, visible=True, actived=True
        ).exists()

        # Procesamiento del formulario TicketForm
        ticket_form = TicketForm(request.POST, instance=self.object)

        # Verificar si se ha enviado el valor de company_id desde JavaScript
        company_id = request.POST.get("provider_company")
        if company_id:
            processes = Process.objects.filter(
                company_id=company_id, visible=True
            ).values("id", "process_type")
            if not send and not close_ticket:
                return JsonResponse({"success": True, "processes": list(processes)})

        # Verificar si se ha enviado el valor de process_type desde JavaScript
        process_type_id = request.POST.get("process_type")
        if process_type_id:
            process_type = Process.objects.get(id=process_type_id)
            if process_type != self.object.process_type:
                self.object.process_type = process_type
                self.object.assign_to = None  # Desasigna el usuario
                if send:
                    self.object.save()

            # Obtener la lista de usuarios asignados para este proceso
            users = User.objects.filter(
                process_type=process_type,
                company=self.request.user.company,
                visible=True,
            ).values("id", "username")
            if not send and not close_ticket:
                return JsonResponse({"success": True, "users": list(users)})

        if ticket_form.is_valid():
            ticket = ticket_form.save(commit=False)
            ticket.modified_by = request.user  # Asigna el usuario logueado al ticket
            ticket.save()  # Guarda el ticket en la base de datos

            # Crear una nueva instancia del formulario TicketForm con los datos actualizados
            company = self.request.user.company
            company_tk = ticket.company
            process = ticket.process_type
            form = TicketForm(
                instance=ticket, company=company, company_tk=company_tk, process=process
            )

            # Actualizar el contexto con el nuevo formulario
            context = self.get_context_data(**kwargs)
            context["form"] = form

        # Obtener el ID del usuario seleccionado
        user_id = request.POST.get("assign_to")

        # Obtener el ID de la compañía proveedora y cliente seleccionada
        provider_company_id = request.POST.get("provider_company")
        customer_company_id = request.POST.get("customer_company")
        is_provider = Company.objects.filter(
            provider=provider_company_id, visible=True, actived=True
        ).exists()
        provider_company_id_int = int
        if provider_company_id:
            provider_company_id_int = int(provider_company_id)

        # Procesamiento de los formularios del mensaje y adjuntos

        message_form = MessageForm(request.POST)
        attachment_form = AttachmentForm(request.POST, request.FILES)

        # Verificar el tamaño y formato de los archivos adjuntos
        attachment_error = None
        max_size_mb = 7
        allowed_formats = [
            "cfg",
            "csv",
            "doc",
            "docx",
            "eml",
            "exe",
            "jpeg",
            "jpg",
            "mp4",
            "msg",
            "pdf",
            "png",
            "rar",
            "txt",
            "xim",
            "xls",
            "xlsx",
            "xml",
            "zip",
        ]

        files = request.FILES.getlist("file")
        total_size_mb = sum(file.size / (1024 * 1024) for file in files)
        if total_size_mb > max_size_mb:
            attachment_error = f"El tamaño total de los archivos adjuntos no puede superar los {max_size_mb} MB."
        else:
            for file in files:
                file_extension = file.name.split(".")[-1].lower()
                if file_extension not in allowed_formats:
                    attachment_error = f"Los formatos de archivo permitidos son: {', '.join(allowed_formats)}."
                    break

        if attachment_error:
            context = self.get_context_data(**kwargs)
            context["attachment_error"] = attachment_error
            return self.render_to_response(context)

        # Obtener el número de mensajes del ticket
        message_count = self.object.messages.count()
        message_form = MessageForm(request.POST)
        # Procesar el formulario de mensaje
        if message_form.is_valid():
            message = message_form.save(commit=False)
            message.user = request.user
            message.ticket = self.object
            # Incrementar el contador de mensajes antes de guardar el mensaje
            message_count += 1

            # Asignar el número de mensaje al mensaje actual
            message.number = message_count
            message.save()

        files = request.FILES.getlist("file")
        attachments = []
        for file in files:
            # Generar nuevo nombre de archivo
            new_file_name = f"{self.object.id}_{message_count}_{file.name}"

            # Guardar el archivo con el nuevo nombre
            file.name = new_file_name

            attachment = Attachment.objects.create(
                ticket=self.object, file=file, message=message
            )
            attachments.append(attachment)

        # Registrar la acción en el log de auditoría con datos adicionales
        self.log_additional_data(ticket_form, message_form, attachments)

        # Verifica si se hizo clic en el botón para cerrar el ticket
        if "close_ticket" in request.POST:
            self.object.status = False  # Marca el ticket como cerrado
            self.object.closed_at = timezone.now()
            self.object.save()
        # Asignar el ticket al usuario seleccionado
        if user_id is not None and user_id != "" and user_id:
            self.object.assign_to_id = user_id
            self.object.save()

        elif company_id_tk != provider_company_id_int:
            self.object.assign_to_id = None
            self.object.save()
        else:
            if company_id_tk == provider_company_id_int:
                if user_id is None:
                    self.object.assign_to_id = None
                    self.object.save()
            else:
                self.object.assign_to_id = user_tk
                self.object.save()

        # Asignar la compañía proveedora y cliente seleccionada al ticket
        if provider_company_id or customer_company_id:
            provider_company = Company.objects.get(id=provider_company_id)
            if provider_company_id:
                if self.request.user.company_id != provider_company_id:
                    self.object.company = provider_company
                    # Actualizar la compañía del ticket si la compañía que asigna es diferente a la compañía proveedora
                if is_provider:
                    self.object.customer_company = None
                    self.object.provider_company = provider_company
            if not is_provider:
                self.object.provider_company = None
                if self.request.user.company_id != customer_company_id:
                    self.object.company = provider_company
                    # Actualizar la compañía del ticket si la compañía que asigna es diferente a la compañía cliente
                self.object.customer_company = provider_company
            self.object.save()
        page_update = HttpResponse(
            ""
        )  # O puedes enviar algún contenido si es necesario.
        page_update["HX-Redirect"] = self.get_success_url()

        return page_update

    def get_success_url_closed(self):
        return reverse_lazy("companies:closed_tickets")

    def get_success_url(self):
        return reverse_lazy("companies:main_ticket")

    def log_additional_data(self, ticket_form, message_form, attachments):
        """
        Registra los datos adicionales en el log de auditoría.
        """
        user = self.request.user
        company_id = getattr(user, "company_id", None)
        view_name = self.__class__.__name__
        ip_address = asyncio.run(obtener_ip_publica(self.request))

        before = model_to_dict(self.object)  # Cambios antes de la actualización
        after = {
            "ticket": model_to_dict(ticket_form.instance),
            "message": model_to_dict(message_form.instance)
            if message_form.is_valid()
            else {},
            "attachments": [model_to_dict(att) for att in attachments],
        }

        before_json = json.dumps(before, default=str)
        after_json = json.dumps(after, default=str)

        log_action(
            user=user,
            company_id=company_id,
            view_name=view_name,
            action="update",
            before=before_json,
            after=after_json,
            ip_address=ip_address,
        )


class CommentTicketView(LoginRequiredMixin, generic.CreateView):
    model = Ticket
    template_name = "whitelabel/tickets/comment_ticket.html"
    form_class = CommentForm
    permission_required = "whitelabel.comment_ticket"

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.ticket = get_object_or_404(
            Ticket, pk=self.kwargs["pk"]
        )  # Asocia el comentario con el ticket
        response = super().form_valid(form)
        # Puedes cambiar el estado del ticket aquí si es necesario
        ticket = form.instance.ticket
        ticket.status = True  # O lo que necesites para "cambiar el estado del ticket"
        ticket.save()
        return response

    def get_success_url(self):
        # Redirecciona de nuevo a la vista del ticket después de comentar
        return reverse(
            "whitelabel/tickets/view_ticket.html", kwargs={"pk": self.object.ticket.pk}
        )


@method_decorator(csrf_exempt, name="dispatch")
class ClosedTicketsView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Ticket
    template_name = "whitelabel/tickets/closed_tickets.html"
    context_object_name = "closed_tickets"
    permission_required = "whitelabel.view_ticket"

    def get_paginate_by(self, queryset):
        paginate_by = self.request.POST.get('paginate_by', None)  # Obtener paginate_by de los parámetros POST
        if paginate_by is None:
            session_filters = self.request.session.get(
                f"filters_{self.request.user.id}", {}
            )
            paginate_by = session_filters.get("paginate_by", 15)
            # Convertir a entero si es una lista
            try:
                paginate_by = int(paginate_by) or int(
                    paginate_by[0]
                )  # Convertir el primer elemento de la lista a entero
            except (TypeError, ValueError):
                paginate_by = int(paginate_by) if paginate_by else 15
            # Añadir paginate_by a self.request.GET para asegurar que esté presente
            self.request.POST = self.request.POST.copy()
            self.request.POST['paginate_by'] = paginate_by
        return int(self.request.POST['paginate_by'])

    def get_filtered_tickets(self, user_company, user, params, is_post=False):
        tickets = get_ticket_closed(user_company, user)
        tickets_all = tickets
        for ticket in tickets:
            ticket["rating_range"] = range(ticket["rating"] or 0)

            if ticket["duration"]:
                duration_parts = ticket["duration"].split(",")
                ticket["days"] = int(duration_parts[0])
                ticket["hours"] = int(duration_parts[1])
                ticket["minutes"] = int(duration_parts[2])
                ticket["seconds"] = int(duration_parts[3])
            else:
                ticket["days"] = 0
                ticket["hours"] = 0
                ticket["minutes"] = 0
                ticket["seconds"] = 0

            ticket["user_created"] = (
                1 if self.request.user.username == ticket["created_by"] else 0
            )

        date_from = params.get("date_from", "")
        date_to = params.get("date_to", "")
        company_id = params.get("company", "")
        assignment = params.get("assignment", "")
        filter_pressed = params.get("filter", "")
        status = params.get("status", "")
        query = params.get("query", "").lower()
        search = params.get("q", "").lower()

        if "query" in params:
            tickets = [
                ticket
                for ticket in tickets
                if (
                    query in str(ticket.get("id", "")).lower()
                    or query in str(ticket.get("subject", "")).lower()
                    or query in str(ticket.get("company", "")).lower()
                    or query in str(ticket.get("process_type", "")).lower()
                    or query in str(ticket.get("created_by", "")).lower()
                )
            ]
        if search and filter_pressed:
            tickets = [
                ticket
                for ticket in tickets
                if (
                    query in str(ticket.get("id", "")).lower()
                    or query in str(ticket.get("subject", "")).lower()
                    or query in str(ticket.get("company", "")).lower()
                    or query in str(ticket.get("process_type", "")).lower()
                    or query in str(ticket.get("created_by", "")).lower()
                )
            ]

        if status:
            if status == "open":
                tickets = [ticket for ticket in tickets if ticket["status"]]
            elif status == "closed":
                tickets = [ticket for ticket in tickets if not ticket["status"]]
        if date_from:
            date_from_date = parse_datetime(date_from)
            tickets = [
                ticket for ticket in tickets if ticket["created_at"] >= date_from_date
            ]
        if date_to:
            date_to_date = parse_datetime(date_to)
            tickets = [
                ticket for ticket in tickets if ticket["created_at"] <= date_to_date
            ]
        if company_id:
            users_in_company = User.objects.filter(company_id=company_id)
            tickets_commented_by_users = (
                Message.objects.filter(user__in=users_in_company)
                .values_list("ticket_id", flat=True)
                .distinct()
            )

            tickets = [
                ticket
                for ticket in tickets
                if ticket["created_by"] in users_in_company
                or ticket["id"] in tickets_commented_by_users
            ]
        if assignment:
            if assignment == "assigned":
                tickets = [ticket for ticket in tickets if ticket["assign_to"]]
            elif assignment == "unassigned":
                tickets = [ticket for ticket in tickets if not ticket["assign_to"]]

        if (
            not company_id
            and not status
            and not assignment
            and not date_from
            and not date_to
            and not search
            and not "paginate_by" in params
            and not query
            and (filter_pressed or not filter_pressed)
        ):
            # Limpiar los filtros de la sesión
            if f"filters_{user}" in self.request.session:
                del self.request.session[f"filters_{user}"]
                self.request.session.modified = True
            return tickets_all

        tickets.sort(
            key=lambda ticket: ticket["last_comment"] or datetime.min, reverse=True
        )
        
        return tickets

    def get_queryset(self):
        user_company = self.request.user.company_id
        user = self.request.user.id
        params = self.request.GET if self.request.method == 'GET' else self.request.POST
        # Verificar si alguno de los parámetros requeridos no está presente
        if not ("paginate_by" in params or "page" in params or "order_by" in params):
            # Limpiar los filtros de la sesión
            if f"filters_{user}" in self.request.session:
                del self.request.session[f"filters_{user}"]
                self.request.session.modified = True
        # Recuperar filtros almacenados en la sesión
        session_filters = self.request.session.get(f"filters_{user}", {})
        # Crear un nuevo QueryDict para almacenar los filtros combinados
        combined_params = QueryDict("", mutable=True)
        combined_params.update(session_filters)

        # Actualizar con los parámetros de la solicitud
        for key, value in params.items():
            if value:
                combined_params[key] = value
        # Actualizar los filtros de la sesión con los nuevos parámetros
        self.request.session[f"filters_{user}"] = combined_params.dict()
        self.request.session.modified = True
        # Manejo especial para el parámetro 'q'
        if "q" in params:
            if combined_params.get("query", "") == "":
                combined_params["query"] = params["q"]
        # Actualizar params con el valor de 'query' de combined_params si está vacío
        if "query" in combined_params:
            if params.get("query", [""])[0] == "":
                params = params.copy()  # Hacer una copia mutable de params si es necesario
                params["query"] = combined_params["query"]
        session_filters = self.request.session[f"filters_{user}"]
        # Manejo del parámetro 'paginate_by'
        if "paginate_by" not in params or params["paginate_by"] == "":
            combined_params["paginate_by"] = session_filters.get("paginate_by", 15)
        # Eliminar csrfmiddlewaretoken de los parámetros combinados
        if "csrfmiddlewaretoken" in combined_params:
            del combined_params["csrfmiddlewaretoken"]
        tickets = self.get_filtered_tickets(user_company, user, combined_params)
        # Parámetros de ordenamiento por defecto
        order_by = self.request.GET.get('order_by') or self.request.POST.get('order_by') or session_filters.get('order_by', ['last_comment'])[0]
        direction = self.request.GET.get('direction') or self.request.POST.get('direction') or session_filters.get('direction', ['desc'])[0]
        # Aplicar ordenamiento si hay filtro de ordenamiento activo
        if "order_by" in params:
            try:
                tickets_order = sorted(
                    tickets,
                    key=lambda x: self.sort_key(x[order_by]),
                    reverse=(direction == "desc"),
                )
            except KeyError:
                # Ordenamiento por defecto si la clave no existe
                tickets_order = sorted(
                    tickets,
                    key=lambda x: x["last_comment"],
                    reverse=(direction == "desc"),
                )
            return tickets_order

        return tickets  # Devolver tickets sin ordenamiento si no hay filtro de ordenamiento activo

    def sort_key(self, value):
        if value is None or value == "":
            return (4, "")  # Prioridad 4 para valores nulos o vacíos
        if isinstance(value, str):
            # Verificar si comienza con números, letras o caracteres especiales
            if value[0].isdigit():
                return (1, extract_number(value))  # Prioridad 1 para números
            elif value[0].isalpha():
                return (2, value.lower())  # Prioridad 2 para letras
            else:
                return (3, value.lower())  # Prioridad 3 para caracteres especiales
        return value

    def get_context_data(self, **kwargs):
        # Asegúrate de que el queryset esté definido
        if not hasattr(self, 'object_list'):
            self.object_list = self.get_queryset()
        context = super().get_context_data(**kwargs)
        user = self.request.user
        companies = get_user_companies(user)
        if user.company_id == 1:
            context["companies"] = companies
        else:
            companies_list = list(companies.values_list("id", "company_name"))
            context["companies"] = companies_list

        tickets = self.get_queryset()
        session_filters = self.request.session.get(f"filters_{user.id}", {})
        page_size = session_filters.get("paginate_by", 15)
        paginator = Paginator(tickets, page_size)
        page_number = 1

        if "page" in self.request.POST:
            page_number = self.request.GET.get('page', session_filters.get('page', [1]))[0]
        try:
            page = paginator.page(page_number)
        except PageNotAnInteger:
            page = paginator.page(1)
        except EmptyPage:
            page = paginator.page(paginator.num_pages)
        context["paginator"] = paginator
        context["page_obj"] = page
        context[self.context_object_name] = page.object_list
        context["is_paginated"] = page.has_other_pages()
        paginate_by = session_filters.get("paginate_by", 15)
        context["paginate_by"] = paginate_by

        querydict = self.request.POST.copy()
        # Eliminar parámetros de paginación de la URL visible
        if "page" in querydict:
            querydict.pop("page")

        if "paginate_by" in querydict:
            querydict.pop("page", None)

        # Recuperar los filtros combinados para la URL
        combined_params = self.request.session.get(f"filters_{user.id}", {})
        if "csrfmiddlewaretoken" in combined_params:
            del combined_params["csrfmiddlewaretoken"]
        if "csrfmiddlewaretoken" in querydict:
            del querydict["csrfmiddlewaretoken"]
        for key, value in combined_params.items():
            if key != "page":  # No volver a incluir 'page' en la URL
                querydict.setlist(key, value if isinstance(value, list) else [value])
        context["query_string"] = querydict.urlencode()
        # Añadir los filtros combinados al contexto para el formulario
        context["combined_params"] = combined_params

        # Añadir el número de página actual al contexto (oculto)
        context["hidden_params"] = {"page": page_number}

        page_number = context.get("page_obj").number if context.get("page_obj") else 1
        context["start_number"] = (page_number - 1) * self.get_paginate_by(None)
        session_filters = self.request.session.get(f'filters_{self.request.user.id}', {})
        # Obtener el ordenamiento desde la solicitud actual
        order_by = self.request.GET.get('order_by') or self.request.POST.get('order_by') or session_filters.get('order_by', ['last_comment'])[0]
        direction = self.request.GET.get('direction') or self.request.POST.get('direction') or session_filters.get('direction', ['desc'])[0]
        context['order_by'] = order_by
        context['direction'] = direction
        return context

    @method_decorator(csrf_protect)
    def post(self, request, *args, **kwargs):
        if "rate_ticket" in request.POST:
            ticket_id = request.POST.get("ticket_id")
            rating = request.POST.get("rating")
            try:
                ticket = Ticket.objects.get(id=ticket_id)
                if (
                    ticket.status == False and ticket.rating is None
                ):  # Solo permitir calificación si el ticket está cerrado
                    ticket.rating = rating
                    ticket.save()
                    return JsonResponse({"success": True})
                else:
                    return JsonResponse(
                        {"success": False, "error": "Ticket not eligible for rating"}
                    )
            except Ticket.DoesNotExist:
                return JsonResponse({"success": False, "error": "Ticket not found"})
        
        elif "order_by" in request.POST or "paginate_by" in request.POST or "page" in request.POST:
            # Lógica para renderizar la página

            # Obtén el número de página desde la solicitud POST
            page_number = request.POST.get('page', 1)
            # Actualizar los filtros almacenados en la sesión
            user = request.user.id
            session_filters = self.request.session.get(f"filters_{user}", {})
            params = request.POST.copy()
            for key, value in params.items():
                if value:
                    session_filters[key] = value
            self.request.session[f"filters_{user}"] = session_filters
            self.request.session.modified = True
            # Obtener datos filtrados
            tickets = self.get_filtered_tickets(request.user.company_id, user, session_filters)
            
            # Ordenar los tickets
            order_by = self.request.GET.get('order_by') or self.request.POST.get('order_by') or session_filters.get('order_by', ['last_comment'])[0]
            direction = self.request.GET.get('direction') or self.request.POST.get('direction') or session_filters.get('direction', ['desc'])[0]
            def sort_key(x):
                value = x.get(order_by)
                if value is None or value == "":
                    return (4, "")  # Prioridad 4 para valores nulos o vacíos
                if isinstance(value, str):
                    # Verificar si comienza con números, letras o caracteres especiales
                    if value[0].isdigit():
                        return (1, extract_number(value))  # Prioridad 1 para números
                    elif value[0].isalpha():
                        return (2, value.lower())  # Prioridad 2 para letras
                    else:
                        return (3, value.lower())  # Prioridad 3 para caracteres especiales
                return value

            # Determinar si es orden descendente
            reverse = direction == "desc"

            try:
                tickets_order = sorted(tickets, key=sort_key, reverse=reverse)
            except KeyError:
                # Ordenamiento por defecto si la clave no existe
                tickets_order = sorted(
                    tickets, key=lambda x: x["last_comment"].lower(), reverse=reverse
                )

            # Configurar la paginación
            paginator = Paginator(tickets_order, session_filters.get("paginate_by", 15))
            page_number = request.POST.get('page', 1)
            try:
                tickets_page = paginator.page(page_number)
            except PageNotAnInteger:
                tickets_page = paginator.page(1)
            except EmptyPage:
                tickets_page = paginator.page(paginator.num_pages)
            # Preparar el contexto para renderizar la plantilla
            context = self.get_context_data()
            context.update({
            "tickets_page": tickets_page,
            "is_paginated": tickets_page.has_other_pages(),
            "order_by": order_by,
            "direction": direction,
            "paginate_by": session_filters.get("paginate_by", 15),
            })

            return self.render_to_response(context)
        
        else:
            user_company = request.user.company_id
            user = request.user.id
            params = request.POST.copy()
            # Recuperar filtros almacenados en la sesión
            session_filters = self.request.session.get(f"filters_{user}", {})
            for key, value in session_filters.items():
                if key not in params:
                    params[key] = value
            # Actualizar los filtros de la sesión con los nuevos parámetros
            self.request.session[f"filters_{user}"] = params.dict()
            self.request.session.modified = True
            tickets = self.get_filtered_tickets(user_company, user, params)
            # Paginar los tickets antes de pasar a get_pagination_data
            page_size = session_filters.get("paginate_by", 15)
            paginator = Paginator(tickets, page_size)
            page_number = request.POST.get('page', session_filters.get('page', [1]))[0]
            try:
                tickets_page = paginator.page(page_number)
            except PageNotAnInteger:
                tickets_page = paginator.page(1)
            except EmptyPage:
                tickets_page = paginator.page(paginator.num_pages)

            # Convertir el objeto `range` a una lista
            for ticket in tickets_page:
                if "rating_range" in ticket:
                    ticket["rating_range"] = list(ticket["rating_range"])

            formatted_results = []
            for ticket in tickets_page:
                formatted_results.append(
                    {
                        "id": ticket["id"],
                        "created_by": ticket["created_by"] or "",
                        "subject": ticket["subject"] or "",
                        "priority": ticket["priority"] or "",
                        "process_type": ticket["process_type"] or "",
                        "assign_to": ticket.get("assign_to") or "Unassigned",
                        "status": "Open" if ticket["status"] else "Closed",
                        "created_at": ticket["created_at"].strftime('%Y-%m-%d %H:%M:%S') or "",
                        "last_comment": ticket["last_comment"].strftime('%Y-%m-%d %H:%M:%S') or "",
                        "rating": ticket["rating"] or "",
                        "user_created": ticket["user_created"],
                        "days": ticket["days"],
                        "hours": ticket["hours"],
                        "minutes": ticket["minutes"],
                    }
                )

            page_data = self.get_pagination_data(tickets_page)
            return JsonResponse(
                {"success": True, "results": formatted_results, "page": page_data}
            )

    def get_pagination_data(self, tickets_page):
        paginator = tickets_page.paginator
        page = tickets_page

        return {
            "has_previous": page.has_previous(),
            "has_next": page.has_next(),
            "number": page.number,
            "num_pages": paginator.num_pages,
            "start_index": page.start_index(),
            "end_index": page.end_index(),
            "total_items": paginator.count,
            "query_string": self.request.GET.urlencode()
            if self.request.method == "GET"
            else self.request.POST.urlencode(),
        }
