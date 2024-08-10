from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views import generic
from django.views.generic.list import MultipleObjectMixin
from rest_framework import generics

from apps.whitelabel.forms import (
    AttachmentForm,
    CommentForm,
    CompanyCustomerForm,
    CompanyDeleteForm,
    CompanyLogoForm,
    DistributionCompanyForm,
    KeyMapForm,
    MessageForm,
    Moduleform,
    ProcessForm,
    ThemeForm,
    TicketForm,
)
from apps.whitelabel.models import (
    Attachment,
    Company,
    CompanyTypeMap,
    MapType,
    Module,
    Process,
    Theme,
    Ticket,
)
from config.pagination import get_paginate_by

from .forms import (
    AttachmentForm,
    CommentForm,
    CompanyCustomerForm,
    CompanyDeleteForm,
    CompanyLogoForm,
    DistributionCompanyForm,
    KeyMapForm,
    MessageForm,
    Moduleform,
    ProcessForm,
    ThemeForm,
    TicketForm,
)
from .models import (
    Attachment,
    Company,
    CompanyTypeMap,
    MapType,
    Module,
    Process,
    Theme,
    Ticket,
)
from .serializer import ClienteSerializer
from .sql import fetch_all_company, get_ticket_by_user


class CompaniesView(PermissionRequiredMixin, LoginRequiredMixin, generic.ListView):
    """
    Esta clase es una vista de lista del modelo de empresas y representará la plantilla
    company_main.html.

    Atributos:
        template_name (str): El nombre de la plantilla HTML que se utilizará para renderizar la vista.
        permission_required (str): El permiso requerido para acceder a esta vista.
        login_url (str): La URL a la que se redirigirá si el usuario no está autenticado.
        context_object_name (str): El nombre del objeto de contexto que se utilizará en la plantilla.
        model (Model): El modelo de la empresa que se utilizará para obtener los datos.

    Métodos:
        get_paginate_by(queryset): Obtiene el número de elementos a mostrar por página.
        get_queryset(): Obtiene el conjunto de datos de los comandos de envío filtrados y ordenados.
        get_context_data(**kwargs): Obtiene el contexto de datos adicionales para la plantilla.
    """

    template_name = "whitelabel/companies/company_main.html"
    permission_required = "whitelabel.view_company"
    login_url = "login"
    context_object_name = "company_info"
    model = Company

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
        queryset = fetch_all_company(company, user)

        # Ordenar los resultados por 'Company' de forma descendente.
        # Si queryset es una lista de diccionarios, Python no tiene un método `order_by`.
        # Se debe utilizar la función sorted para ordenar listas de diccionarios.
        queryset = sorted(queryset, key=lambda x: x["company_name"], reverse=False)
        return queryset

    def get_context_data(self, **kwargs):
        """
        Obtiene el contexto de datos adicionales para la plantilla.

        Args:
            **kwargs: Argumentos clave adicionales.

        Returns:
            dict: El contexto de datos adicionales para la plantilla.
        """
        context = super().get_context_data(**kwargs)
        companies = context[
            self.context_object_name
        ]  # Usa el objeto ya definido en el contexto

        # Calcula start_number más eficientemente
        page_number = context.get("page_obj").number if context.get("page_obj") else 1
        context["start_number"] = (page_number - 1) * self.get_paginate_by(None)

        # Optimización del cálculo para mostrar el botón de mapa
        for company in companies:
            company_id = company["id"]
            company_maps = CompanyTypeMap.objects.filter(company_id=company_id)
            total_maps = company_maps.count()
            has_only_map1 = (
                total_maps == 1 and company_maps.filter(map_type__id=1).exists()
            )
            company["show_map_button"] = not has_only_map1

        return context


class CreateDistributionCompanyView(
    PermissionRequiredMixin, LoginRequiredMixin, generic.CreateView
):
    """
    View para crear una empresa distribuidora.
    La empresa se crea y se le asigna a company_id del usuario.
    """

    model = Company
    template_name = "whitelabel/companies/add_company.html"
    permission_required = "whitelabel.add_company"
    login_url = "login"
    form_class = DistributionCompanyForm
    success_url = "companies:companies"

    def get_success_url(self):
        # Asegúrate de que el nombre de la URL sea correcto y esté definido en tus archivos de URL.
        return reverse("companies:companies")

    def form_valid(self, form):
        """
        Esta función se llama cuando se envía un formulario válido.
        Guarda el formulario sin confirmar aún en la base de datos y establece provider_id en None.
        Luego, guarda el formulario en la base de datos y guarda las relaciones many-to-many.
        Si la empresa del usuario actual es la empresa principal, crea un tema para la empresa
        recién creada.
        Finalmente, devuelve una respuesta HTTP sin contenido con un encabezado que indica que se
        debe recargar la página.
        """
        form.instance.actived = True
        company = form.save(commit=False)
        # Asigna la instancia del usuario al campo 'modified_by' y 'created_by'
        company.modified_by = self.request.user
        company.created_by = self.request.user
        company.provider_id = None
        company.save()
        form.save_m2m()

        if self.request.user.company_id == 1:
            Theme.objects.create(company_id=company.id)

        maps = MapType.objects.filter(companytypemap__company=company)

        if maps.count() == 1 and maps.first().name == "OpenStreetMap":
            page_update = HttpResponse(
                ""
            )  # O puedes enviar algún contenido si es necesario.
            page_update["HX-Redirect"] = self.get_success_url()
            return page_update
        else:
            return redirect("companies:KeyMapView", pk=company.id)

    def form_invalid(self, form):
        """
        Esta función se llama cuando se envía un formulario inválido.
        Renderiza el template con el formulario inválido.
        """
        return render(self.request, self.template_name, {"form": form})


class CreateCustomerAzCompanyView(
    PermissionRequiredMixin, LoginRequiredMixin, generic.CreateView
):
    model = Company
    template_name = "whitelabel/companies/add_company.html"
    permission_required = "whitelabel.add_company"
    login_url = "login"
    form_class = DistributionCompanyForm
    success_url = "companies:companies"

    def get_success_url(self):
        # Asegúrate de que el nombre de la URL sea correcto y esté definido en tus archivos de URL.
        return reverse("companies:companies")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs[
            "provider_id"
        ] = self.request.user.company_id  # Asume que el usuario tiene un company_id
        return kwargs

    def form_valid(self, form):
        form.instance.provider_id = self.request.user.company_id
        form.instance.actived = True
        company = form.save(commit=False)
        # Asigna la instancia del usuario al campo 'modified_by' y 'created_by'
        company.modified_by = self.request.user
        company.created_by = self.request.user
        company.save()
        form.save_m2m()

        maps = MapType.objects.filter(companytypemap__company=company)

        if maps.count() == 1 and maps.first().name == "OpenStreetMap":
            page_update = HttpResponse(
                ""
            )  # O puedes enviar algún contenido si es necesario.
            page_update["HX-Redirect"] = self.get_success_url()
            return page_update
        else:
            return redirect("companies:KeyMapView", pk=company.id)

    def form_invalid(self, form):
        return render(self.request, self.template_name, {"form": form})


class CreateCustomerCompanyView(
    PermissionRequiredMixin, LoginRequiredMixin, generic.CreateView
):
    model = Company
    template_name = "whitelabel/companies/add_company.html"
    permission_required = "whitelabel.add_company"
    form_class = CompanyCustomerForm
    success_url = reverse_lazy(
        "companies:companies"
    )  # Asegúrate de que la URL sea correcta

    def get_success_url(self):
        # Asegúrate de que el nombre de la URL sea correcto y esté definido en tus archivos de URL.
        return reverse("companies:companies")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs[
            "provider_id"
        ] = self.request.user.company_id  # Asume que el usuario tiene un company_id
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        # Aquí puedes agregar cualquier dato adicional que necesites en tu template
        context["type_maps"] = CompanyTypeMap.objects.filter(company_id=user.company_id)
        context["modules"] = Module.objects.filter(
            company__id=self.request.user.company_id
        )
        return context

    def form_valid(self, form):
        with transaction.atomic():
            self.object = form.save(commit=False)
            self.object.actived = True
            self.object.provider_id = self.request.user.company_id
            self.object.seller = self.request.user.company.seller
            self.object.consultant = self.request.user.company.consultant
            self.object.save()

            # Manejar relaciones ManyToMany aquí
            type_map_ids = self.request.POST.getlist("type_map")
            for type_map_id in type_map_ids:
                CompanyTypeMap.objects.create(
                    company=self.object, map_type_id=type_map_id
                )

            modules_ids = self.request.POST.getlist("modules")
            for module_id in modules_ids:
                Module.objects.create(
                    company=self.object, group_id=module_id
                )  # Asegúrate de que `group_id` sea correcto

            page_update = HttpResponse(
                ""
            )  # O puedes enviar algún contenido si es necesario.
            page_update["HX-Redirect"] = self.get_success_url()
            return page_update


class KeyMapView(LoginRequiredMixin, generic.UpdateView):
    form_class = KeyMapForm
    model = CompanyTypeMap
    template_name = "whitelabel/companies/keymap.html"

    def get_success_url(self):
        # Asegúrate de que el nombre de la URL sea correcto y esté definido en tus archivos de URL.
        return reverse("companies:companies")

    def get(self, request, *args, **kwargs):
        company_id = self.kwargs.get("pk")
        company = Company.objects.get(id=company_id)
        maps = CompanyTypeMap.objects.filter(company_id=company.id)
        form = self.form_class()
        return render(
            request,
            self.template_name,
            {"maps": maps, "company": company, "form": form},
        )

    def post(self, request, *args, **kwargs):
        form = KeyMapForm(request.POST)
        if form.is_valid():
            company_map = form.save(commit=False)
            key_map = form.data.getlist("key_map")
            count = 0
            for pk in form.data.getlist("id"):
                CompanyTypeMap.objects.filter(id=pk).update(key_map=key_map[count])
                count += 1

            page_update = HttpResponse(
                ""
            )  # O puedes enviar algún contenido si es necesario.
            page_update["HX-Redirect"] = self.get_success_url()
            return page_update
        else:
            return render(request, self.template_name, {"form": form})


class UpdateCompanyLogoView(LoginRequiredMixin, generic.UpdateView):
    """
    UpdateCompanyLogoView es un generic.edit.UpdateView que usa el modelo Company,
    los campos enumerados,
    CompanyForm y el template_name_suffix para actualizar una empresa.
    """

    model = Company
    template_name = "whitelabel/companies/company_update_logo.html"
    form_class = CompanyLogoForm
    success_url = reverse_lazy("companies:companies")

    def get_success_url(self):
        # Asegúrate de que el nombre de la URL sea correcto y esté definido en tus archivos de URL.
        return reverse("main")

    def form_valid(self, form):
        """
        Llamado cuando se envía el formulario y es válido.
        Actualiza el logo de la empresa y responde con un código HTTP 204 y un header "HX-Trigger:
        reload-page".
        """
        # Asigna la instancia del usuario al campo 'modified_by'
        form.instance.modified_by = self.request.user
        form.save()
        response = HttpResponse("")  # O puedes enviar algún contenido si es necesario.
        response["HX-Redirect"] = self.get_success_url()
        return response

    def form_invalid(self, form):
        """
        Llamado cuando se envía el formulario y es inválido.
        Muestra de nuevo el formulario con los errores.
        """
        return render(self.request, self.template_name, {"form": form})


class UpdateDistributionCompanyView(
    PermissionRequiredMixin, LoginRequiredMixin, generic.UpdateView
):
    """
    UpdateCompanyView es un generic.edit.UpdateView que usa el modelo Company,
    los campos enumerados,
    CompanyForm y el template_name_suffix para actualizar una empresa.
    """

    model = Company
    template_name = "whitelabel/companies/company_update.html"
    permission_required = "whitelabel.change_company"
    form_class = DistributionCompanyForm
    success_url = reverse_lazy("companies:companies")

    def get_success_url(self):
        # Asegúrate de que el nombre de la URL sea correcto y esté definido en tus archivos de URL.
        return reverse("companies:companies")

    def form_valid(self, form):
        """
        Llamado cuando se envía el formulario y es válido.
        Actualiza el logo de la empresa y responde con un código HTTP 204 y un header "HX-Trigger:
        reload-page".
        """
        # Asigna la instancia del usuario al campo 'modified_by'
        form.instance.modified_by = self.request.user
        form.save()
        page_update = HttpResponse(
            ""
        )  # O puedes enviar algún contenido si es necesario.
        page_update["HX-Redirect"] = self.get_success_url()
        return page_update


class UpdateCustomerCompanyView(
    PermissionRequiredMixin, LoginRequiredMixin, generic.UpdateView
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
        # Asegúrate de que el nombre de la URL sea correcto y esté definido en tus archivos de URL.
        return reverse("companies:companies")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs[
            "provider_id"
        ] = self.request.user.company_id  # Asume que el usuario tiene un company_id
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        # Aquí puedes agregar cualquier dato adicional que necesites en tu template
        context["type_maps"] = CompanyTypeMap.objects.filter(company_id=user.company_id)
        context["modules"] = Module.objects.filter(
            company__id=self.request.user.company_id
        )
        return context

    def form_valid(self, form):
        with transaction.atomic():
            self.object = form.save(commit=False)
            self.object.actived = True
            self.object.provider_id = self.request.user.company_id
            self.object.seller = self.request.user.company.seller
            self.object.consultant = self.request.user.company.consultant
            self.object.save()

            # Manejar relaciones ManyToMany aquí
            type_map_ids = self.request.POST.getlist("type_map")
            for type_map_id in type_map_ids:
                CompanyTypeMap.objects.create(
                    company=self.object, map_type_id=type_map_id
                )

            modules_ids = self.request.POST.getlist("modules")
            for module_id in modules_ids:
                Module.objects.create(
                    company=self.object, group_id=module_id
                )  # Asegúrate de que `group_id` sea correcto

            page_update = HttpResponse(
                ""
            )  # O puedes enviar algún contenido si es necesario.
            page_update["HX-Redirect"] = self.get_success_url()
            return page_update


class DeleteCompanyView(
    PermissionRequiredMixin, LoginRequiredMixin, generic.UpdateView
):
    """
    DeleteCompanyView es un generic.edit.UpdateView que usa el modelo Company,
    los campos enumerados,
    CompanyForm y el template_name_suffix para actualizar una empresa.
    """

    model = Company
    template_name = "whitelabel/companies/company_delete.html"
    permission_required = "whitelabel.delete_company"
    form_class = CompanyDeleteForm
    success_url = reverse_lazy("companies:companies")

    def get_success_url(self):
        # Asegúrate de que el nombre de la URL sea correcto y esté definido en tus archivos de URL.
        return reverse("companies:companies")

    def form_valid(self, form):
        """
        Llamado cuando se envía el formulario y es válido.
        Actualiza el logo de la empresa y responde con un código HTTP 204 y un header "HX-Trigger:
        reload-page".
        """
        company = form.save(commit=False)
        company.visible = False
        company.actived = False
        form.save()
        page_update = HttpResponse(
            ""
        )  # O puedes enviar algún contenido si es necesario.
        page_update["HX-Redirect"] = self.get_success_url()
        return page_update


class ThemeView(LoginRequiredMixin, generic.UpdateView):
    """
    Si el tema existe, renderice la plantilla.
    Si el tema no existe, créelo y renderice la plantilla
    """

    model = Theme
    template_name = "whitelabel/theme/theme.html"
    form_class = ThemeForm
    success_url = reverse_lazy("companies:companies")

    def post(self, request, *args, **kwargs):
        """
        Guarda los datos del formulario en la base de datos.

        :param request: El objeto de la solicitud
        :return: El formulario está siendo devuelto.
        """
        theme = Theme.objects.get(company_id=self.request.user.company_id)
        form = self.form_class(request.POST, request.FILES, instance=theme)

        if form.is_valid():
            theme = form.save(commit=False)
            opacityhex = hex(int(theme.opacity))[2:]
            form.instance.opacity = opacityhex
            form.save()
            return redirect(self.success_url)

        return render(request, self.template_name, {"form": form})


class ModuleTemplateView(
    PermissionRequiredMixin, LoginRequiredMixin, generic.TemplateView
):
    """
    Vista como clase que renderiza el template HTML que contiene la lista de modulos de cada empresa.
    """

    template_name = "whitelabel/module/main_module.html"
    permission_required = "whitelabel.view_module"


class ModuleView(PermissionRequiredMixin, LoginRequiredMixin, generic.ListView):
    """
    Este código define una vista genérica basada en clases que lista todos los objetos del modelo "Module"
    en la base de datos y agrega una lista de precios para cada empresa que posee un objeto de módulo a los
    datos de contexto de la vista. Requiere permisos para ver módulos y requiere que el usuario haya iniciado sesión.
    """

    model = Module
    template_name = "whitelabel/module/list_create_module.html"
    login_url = "login"
    permission_required = "whitelabel.view_module"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        if self.request.user.company_id == 1:
            company = Company.objects.filter(visible=True, actived=True)
            list_price = []
            for companys in company:
                total_price = 0
                for modul in context["module_list"]:
                    if companys.id == modul.company_id:
                        total_price += modul.price
                list_price.append(
                    {"company_id": companys.id, "total_price": total_price}
                )
        else:
            companies_monitor = user.companies_to_monitor.all()
            if companies_monitor.exists():
                company = companies_monitor.filter(visible=True)
                list_price = []
                for companys in company:
                    total_price = 0
                    for modul in context["module_list"]:
                        if companys.id == modul.company_id:
                            total_price += modul.price
                    list_price.append(
                        {"company_id": companys.id, "total_price": total_price}
                    )
            else:
                company = Company.objects.filter(
                    provider_id=user.company_id, visible=True
                )
                list_price = []
                for companys in company:
                    total_price = 0
                    for modul in context["module_list"]:
                        if companys.id == modul.company_id:
                            total_price += modul.price
                    list_price.append(
                        {"company_id": companys.id, "total_price": total_price}
                    )
        context["list_price"] = list_price
        context["company"] = company
        return context


class UpdateModuleView(PermissionRequiredMixin, LoginRequiredMixin, generic.UpdateView):
    """
    Este código define una vista genérica de actualización de un objeto del modelo Module, que
    requiere permisosy autenticación de inicio de sesión. La vista maneja solicitudes GET y POST,
    con lógica de validación de formularios.Si el formulario es válido, se actualiza la información
    en la base de datos y se devuelve una respuesta de estado HTTP 204, y si no es válido, se
    renderiza la plantilla de actualización de módulo con los errores del formulario.
    """

    model = Module
    template_name = "whitelabel/module/update_module.html"
    permission_required = "whitelabel.change_module"
    form_class = Moduleform
    success_url = reverse_lazy("companies:module")

    def get_success_url(self):
        # Asegúrate de que el nombre de la URL sea correcto y esté definido en tus archivos de URL.
        return reverse("companies:module")

    def get(self, request, *args, **kwargs):
        company_id = self.kwargs.get("pk")
        company = Company.objects.get(id=company_id)
        modules = Module.objects.filter(company_id=company.id)

        forms = [self.form_class(instance=module) for module in modules]  # Lista de formularios

        return render(
            request,
            self.template_name,
            {"forms": forms, "company": company}
        )

    def post(self, request, *args, **kwargs):
        form = Moduleform(request.POST)
        if form.is_valid():
            price = form.data.getlist("price")
            count = 0
            for pk in form.data.getlist("id"):
                # Obtiene cada objeto Module individualmente
                module = Module.objects.get(id=pk)

                # Actualiza el precio y el usuario que modificó
                module.price = price[count]
                module.modified_by = (
                    request.user
                )  # Asigna el usuario actual a 'modified_by'

                # Guarda el objeto
                module.save()

                count += 1

            page_update = HttpResponse(
                ""
            )  # O puedes enviar algún contenido si es necesario.
            page_update["HX-Redirect"] = self.get_success_url()
            return page_update
        else:
            return render(request, self.template_name, {"form": form})


class ListProcessAddView(
    PermissionRequiredMixin, LoginRequiredMixin, MultipleObjectMixin, generic.CreateView
):
    """
    Vista de creación de procesos de lista.

    Esta vista permite a los usuarios crear nuevos procesos de lista.
    Los usuarios deben tener los permisos adecuados y estar autenticados para acceder a esta vista.

    Atributos:
        template_name (str): El nombre de la plantilla HTML para renderizar la vista.
        permission_required (str): El permiso requerido para acceder a esta vista.
        form_class (Form): La clase del formulario utilizado para crear nuevos procesos.
    """

    template_name = "whitelabel/process/main_process.html"
    permission_required = "whitelabel.add_company"
    form_class = ProcessForm
    model = Process

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

        return Process.objects.filter(company=user.company, visible=True).order_by(
            "process_type"
        )

    def get(self, request, *args, **kwargs):
        """
        Método que maneja las solicitudes GET para esta vista.

        Parámetros:
        - request: La solicitud HTTP recibida.
        - args: Argumentos posicionales adicionales.
        - kwargs: Argumentos de palabras clave adicionales.

        Retorna:
        - La respuesta generada por la superclase.

        """
        self.object_list = self.get_queryset()
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """
        Obtiene el contexto de datos para renderizar la vista.

        Args:
            **kwargs: Argumentos clave adicionales.

        Returns:
            dict: El contexto de datos para renderizar la vista.
        """
        context = super().get_context_data(**kwargs)
        user = self.request.user

        if user.company_id == 1:
            context["form"].fields["company"].queryset = Company.objects.filter(
                Q(provider_id=None, visible=True, actived=True)
                | Q(provider_id=self.request.user.company_id)
            )
        else:
            context["form"].fields["company"].queryset = Company.objects.filter(
                Q(id=self.request.user.company_id)
                | Q(provider_id=self.request.user.company_id),
                visible=True,
                actived=True,
            )
        # Simplificación directa para calcular start_number
        page_number = context.get("page_obj").number if context.get("page_obj") else 1
        context["start_number"] = (page_number - 1) * self.get_paginate_by(None)
        return context

    def form_valid(self, form):
        """
        Realiza acciones cuando el formulario es válido.

        Guarda el formulario y realiza acciones adicionales.

        Args:
            form (Form): El formulario válido.

        Returns:
            HttpResponse: Una respuesta HTTP con el estado 204 (Sin contenido) y encabezados adicionales.
        """
        form = form.save(commit=False)
        form.modified_by = self.request.user
        form.created_by = self.request.user
        form.save()
        return HttpResponse(status=204, headers={"HX-Trigger": "ListprocessChanged"})


class UpdateProcessView(
    PermissionRequiredMixin, LoginRequiredMixin, generic.UpdateView
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
    success_url = reverse_lazy("whitelabel:list_process")

    def get_context_data(self, **kwargs):
        """
        Retorna el contexto de datos para renderizar la vista.

        Args:
            **kwargs: Argumentos clave adicionales.

        Returns:
            dict: Contexto de datos para renderizar la vista.

        """
        context = super().get_context_data(**kwargs)
        return context

    def form_valid(self, form):
        """
        Guarda los datos del formulario y retorna una respuesta HTTP.

        Args:
            form (Form): Formulario con los datos del proceso.

        Returns:
            HttpResponse: Respuesta HTTP con estado 204 (Sin contenido) y encabezados adicionales.

        """
        form = form.save(commit=False)
        form.modified_by = self.request.user
        form.save()
        return HttpResponse(status=204, headers={"HX-Trigger": "ListprocessChanged"})


class DeleteProcessView(
    PermissionRequiredMixin, LoginRequiredMixin, generic.UpdateView
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
    permission_required = "whitelabel.delete_process"
    fields = ["visible"]

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
        form = form.save(commit=False)
        form.visible = False
        form.save()
        return HttpResponse(status=204, headers={"HX-Trigger": "ListprocessChanged"})


class ListTicketTemplate(LoginRequiredMixin, generic.ListView):
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
        return get_paginate_by(self.request)

    def get_queryset(self):
        """
        Obtiene el conjunto de datos de los comandos de envío filtrados y ordenados.

        Returns:
            QuerySet: El conjunto de datos de los comandos de envío filtrados y ordenados.
        """
        user = self.request.user
        tickets = get_ticket_by_user(user.id)
        company = user.company

        return tickets

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


class CreateTicketView(LoginRequiredMixin, generic.CreateView):
    model = Ticket
    template_name = "whitelabel/tickets/add_ticket.html"
    form_class = TicketForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["company"] = self.request.user.company
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context[
            "message_form"
        ] = MessageForm()  # Agregar el formulario de mensaje al contexto
        context[
            "attachment_form"
        ] = AttachmentForm()  # Agregar el formulario de adjunto al contexto
        context["process_form"] = ProcessForm()
        return context

    def handle_attachment_errors(self, form, attachment_form):
        files = self.request.FILES.getlist("file")
        total_size = sum(file.size for file in files) / (
            1024 * 1024
        )  # Tamaño total en MB
        if total_size > 7:
            messages.error(
                self.request,
                "El tamaño total de los archivos adjuntos no puede superar los 7 MB.",
            )
            return self.form_invalid(form)

        allowed_formats = [
            "pdf", "docx", "doc", "txt", "xlsx", "xls", "zip", "exe",
            "jpg", "png", "jpeg", "msg", "cfg", "mp4", "rar", "xim", "eml", 
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
        company = self.request.user.company
        form.instance.created_by = self.request.user
        form.instance.company = company

        attachment_form = AttachmentForm(self.request.POST, self.request.FILES)
        attachment_error = self.handle_attachment_errors(form, attachment_form)
        if attachment_error:
            return attachment_error

        # Guardar el ticket
        response = super().form_valid(form)

        # Obtener el número de mensajes del ticket
        message_count = self.object.messages.count()

        # Guardar el mensaje
        message_form = MessageForm(self.request.POST)
        if message_form.is_valid():
            message = message_form.save(commit=False)
            message.user = self.request.user
            message.ticket = self.object
            # Incrementar el contador de mensajes antes de guardar el mensaje
            message_count += 1

            # Asignar el número de mensaje al mensaje actual
            message.number = message_count
            message.save()

        # Guardar los adjuntos
        files = self.request.FILES.getlist("file")
        for file in files:
            # Generar nuevo nombre de archivo
            new_file_name = f"{self.object.id}_{message_count}_{file.name}"

            # Guardar el archivo con el nuevo nombre
            file.name = new_file_name

            Attachment.objects.create(ticket=self.object, file=file, message=message)

        return HttpResponse(status=204, headers={"HX-Trigger": "ListTicketChanged"})

    def get_success_url(self):
        return reverse_lazy("companies:main_ticket")


class ViewTicketView(LoginRequiredMixin, generic.DetailView):
    model = Ticket
    template_name = "whitelabel/tickets/view_ticket.html"
    context_object_name = "ticket"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user  # Obtener el usuario actual
        company = self.request.user.company

        # Obtener las compañías proveedoras y clientes finales
        if user.company.id == 1:  # Si la empresa es la principal (Condicional para AZ)
            # Obtener todos los clientes distribuidores y clientes finales
            provider_companies = Company.objects.filter(provider=None)
            customer_companies = Company.objects.filter(provider=user.company)

        # Logica para que le muestre a la empresa distribuidora solo a su proveedor
        elif self.object.company.provider is None:
            # Obtener las compañías proveedoras y las compañías de clientes del usuario actual
            provider_companies = Company.objects.filter(id=1)
            customer_companies = Company.objects.filter(provider=user.company).exclude(
                id=user.company_id
            )

        # Logica para que le muestre a la empresa final solo a su proveedor
        elif self.object.company.provider is not None:
            provider_companies = Company.objects.filter(customer=user.company)
            customer_companies = Company.objects.filter(provider=user.company).exclude(
                customer=user.company
            )

        context["has_provider"] = company.provider is not None

        context["provider_companies"] = provider_companies
        context["customer_companies"] = customer_companies
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
        self.object = self.get_object()  # Asegúrate de obtener el objeto ticket actual
        id_ticket = self.object.id

        # Obtén el objeto Ticket con el id específico
        ticket = Ticket.objects.get(id=id_ticket)

        # Accede al campo company_id del objeto Ticket
        company_id_tk = ticket.company_id

        # Verifica si company_id_tk existe en la columna provider del modelo Company
        is_provider = Company.objects.filter(provider=company_id_tk).exists()

        # Procesamiento del formulario TicketForm
        ticket_form = TicketForm(request.POST, instance=self.object)

        # Verificar si se ha enviado el valor de process_type desde JavaScript
        process_type_id = request.POST.get("process_type")
        if process_type_id:
            process_type = Process.objects.get(id=process_type_id)
            if process_type != self.object.process_type:
                self.object.process_type = process_type
                self.object.assign_to = None  # Desasigna el usuario
                self.object.save()

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
        
        # Procesamiento de los formularios del mensaje y adjuntos

        message_form = MessageForm(request.POST)
        attachment_form = AttachmentForm(request.POST, request.FILES)

        # Verificar el tamaño y formato de los archivos adjuntos
        attachment_error = None
        max_size_mb = 7
        allowed_formats = [
            "pdf", "docx", "doc", "txt", "xlsx", "xls", "zip", "exe",
            "jpg", "png", "jpeg", "msg", "cfg", "mp4", "rar", "xim", "eml",
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
        for file in files:
            # Generar nuevo nombre de archivo
            new_file_name = f"{self.object.id}_{message_count}_{file.name}"

            # Guardar el archivo con el nuevo nombre
            file.name = new_file_name

            Attachment.objects.create(ticket=self.object, file=file, message=message)

        # Verifica si se hizo clic en el botón para cerrar el ticket
        if "close_ticket" in request.POST:
            self.object.status = False  # Marca el ticket como cerrado
            self.object.save()

        # Asignar el ticket al usuario seleccionado
        if user_id:
            self.object.assign_to_id = user_id
            self.object.save()

        # Asignar la compañía proveedora y cliente seleccionada al ticket
        if provider_company_id or customer_company_id:
            if provider_company_id:
                provider_company = Company.objects.get(id=provider_company_id)
                if self.request.user.company_id != provider_company_id:
                    self.object.company = provider_company
                    # Actualizar la compañía del ticket si la compañía que asigna es diferente a la compañía proveedora
                self.object.provider_company = provider_company
            if customer_company_id:
                customer_company = Company.objects.get(id=customer_company_id)
                if self.request.user.company_id != customer_company_id:
                    self.object.company = customer_company
                    # Actualizar la compañía del ticket si la compañía que asigna es diferente a la compañía cliente
                self.object.customer_company = customer_company
            self.object.save()
        if is_provider:
            company_instance = Company.objects.get(id=company_id_tk)
            # Asignar la instancia de Company al campo provider_company del ticket
            self.object.provider_company = company_instance
            self.object.save()
        return HttpResponse(status=204, headers={"HX-Trigger": "ListTicketChanged"})


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


class ClosedTicketsView(LoginRequiredMixin, generic.ListView):
    model = Ticket
    template_name = "whitelabel/tickets/closed_tickets.html"
    context_object_name = "closed_tickets"

    def get_queryset(self):
        # Filtrar los tickets cerrados por la empresa del usuario logueado
        user_company = self.request.user.company
        return Ticket.objects.filter(
            Q(company=user_company)
            | Q(provider_company_id=user_company)
            | Q(customer_company_id=user_company),
            status=False,
        ).order_by("-last_comment")


class ClienteListAPIView(generics.ListAPIView):
    queryset = Company.objects.filter(visible = True, actived = True)
    serializer_class = ClienteSerializer
