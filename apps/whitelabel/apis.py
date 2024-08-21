
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import F, OuterRef, Subquery, Sum
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.realtime.apis import extract_number

from .models import Company, Module, Process
from .serializer import CompanySerializer
from .sql import get_modules_by_user, get_ticket_by_user, get_ticket_closed
from .views import ClosedTicketsView


def list_proces_by_company(request, company_id):
    """
    Lista todos los procesos por empresa.

    Parámetros:
    - request: La solicitud HTTP recibida.
    - company_id: El ID de la empresa para filtrar los procesos.

    Retorna:
    Un objeto JsonResponse que contiene una lista de procesos, donde cada proceso tiene los campos 'id' y 'name'.
    """
    process = Process.objects.filter(company_id=company_id, visible=True).values(
        "id",
        "process_type",
    )
    return JsonResponse({"process": list(process)}, safe=False)


@method_decorator(csrf_exempt, name="dispatch")
class SearchTicketsView(View):
    def get(self, request):
        company = request.user.company_id
        user_id = request.user.id
        search_query = request.GET.get("query", None)

        if not company or not user_id:
            return JsonResponse({"error": "Faltan parámetros"}, status=400)

        params = request.GET.copy()
        if not params:
            params["query"] = ""
        if search_query:
            params["query"] = search_query

        # Recuperar filtros almacenados en la sesión
        session_filters = request.session.get(f'filters_{user_id}', {})
        
        for key, value in session_filters.items():
            if key not in params:
                params[key] = value

        # Actualizar los filtros de la sesión con los nuevos parámetros
        request.session[f"filters_{user_id}"] = params.dict()
        request.session.modified = True

        closed_tickets_view = ClosedTicketsView()
        closed_tickets_view.request = request

        tickets = closed_tickets_view.get_filtered_tickets(company, user_id, params)
        page_size = session_filters.get("paginate_by", 15)
        paginator = Paginator(tickets, page_size)
        page_number = request.GET.get('page', session_filters.get('page', [1]))[0]

        try:
            page = paginator.page(page_number)
        except PageNotAnInteger:
            page = paginator.page(1)
        except EmptyPage:
            page = paginator.page(paginator.num_pages)

        formatted_results = []
        for ticket in page.object_list:
            duration = ticket.get("duration", "0,0,0,0")
            days, hours, minutes, _ = duration.split(",")
            user_created = 1 if request.user.username == ticket["created_by"] else 0

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
                    "user_created": user_created,
                    "days": days,
                    "hours": hours,
                    "minutes": minutes,
                }
            )

        response_data = {
            "results": formatted_results,
            "page": {
                "has_next": page.has_next(),
                "has_previous": page.has_previous(),
                "number": page.number,
                "num_pages": paginator.num_pages,
                "start_index": page.start_index(),
                "end_index": page.end_index(),
                "total_items": paginator.count,
            },
            "query_string": request.GET.urlencode(),
        }

        return JsonResponse(response_data, safe=False)


@method_decorator(csrf_exempt, name="dispatch")
class SearchTicketsViewOpen(View):
    def get(self, request):
        company = request.user.company_id
        user_id = request.user.id
        session_filters = request.session.get(f'filters_sorted_ticketsopen_{user_id}', {})
        search_query = request.GET.get("query", None)
        page_number = request.GET.get('page', session_filters.get('page', [1]))[0]
        paginate_by = request.POST.get(
            "paginate_by", None
        )  # Obtener paginate_by de los parámetros GET
        if paginate_by is None:
            paginate_by = session_filters.get("paginate_by", 15)
        # Convertir a entero si es una lista
        try:
            paginate_by = int(
                paginate_by[0]
            )  # Convertir el primer elemento de la lista a entero
        except (TypeError, ValueError):
            paginate_by = int(paginate_by) if paginate_by else 15
        if not company or not user_id:
            return JsonResponse({"error": "Faltan parámetros"}, status=400)

        tickets = get_ticket_by_user(user_id, search_query)
        order_by = session_filters.get('order_by', [None])[0]
        direction = session_filters.get('direction', [None])[0]
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
            tickets = sorted(tickets, key=sort_key, reverse=reverse)
        except KeyError:
            # Ordenamiento por defecto si la clave no existe
            tickets = sorted(
                tickets, key=lambda x: x["last_comment"].lower(), reverse=reverse
            )
        page_size = paginate_by  # Número de elementos por página.
        paginator = Paginator(tickets, page_size)

        try:
            page = paginator.page(page_number)
        except PageNotAnInteger:
            page = paginator.page(1)
        except EmptyPage:
            page = paginator.page(paginator.num_pages)

        formatted_results = []
        for ticket in page.object_list:
            formatted_results.append(
                {
                    "id": ticket["id"],
                    "company": ticket["company"] or "",
                    "created_by": ticket["created_by"] or "",
                    "subject": ticket["subject"] or "",
                    "priority": ticket["priority"] or "",
                    "process_type": ticket["process_type"] or "",
                    "assign_to": ticket.get("assign_to") or "Unassigned",
                    "status": "Open" if ticket["status"] else "Closed",
                    "created_at": ticket["created_at"].strftime('%Y-%m-%d %H:%M:%S') or "",
                    "last_comment": ticket["last_comment"].strftime('%Y-%m-%d %H:%M:%S') or "",
                }
            )

        response_data = {
            "results": formatted_results,
            "page": {
                "has_next": page.has_next(),
                "has_previous": page.has_previous(),
                "number": page.number,
                "num_pages": paginator.num_pages,
                "start_index": page.start_index(),
                "end_index": page.end_index(),
                "total_items": paginator.count,
            },
            "query_string": request.GET.urlencode(),
        }

        return JsonResponse(response_data, safe=False)

class CustomPagination(PageNumberPagination):
    page_size = "paginate_by"

    def get_paginated_response(self, data):
        return Response(
            {
                "results": data,
                "page": {
                    "has_next": self.page.has_next(),
                    "has_previous": self.page.has_previous(),
                    "number": self.page.number,
                    "num_pages": self.page.paginator.num_pages,
                    "start_index": self.page.start_index(),
                    "end_index": self.page.end_index(),
                    "total_items": self.page.paginator.count,
                },
                "query_string": self.request.GET.urlencode(),
            }
        )


class SearchModule(APIView):
    def get(self, request, *args, **kwargs):
        user = request.user
        session_filters = self.request.session.get(
                f"filters_sorted_module_{user.id}", {}
            )
        params = request.GET if request.method == 'GET' else request.POST
        query = params.get("query", "").lower()
        search = params.get("q", query).lower()
        paginate_by = request.POST.get(
            "paginate_by", None
        )  # Obtener paginate_by de los parámetros GET
        if paginate_by is None:
            paginate_by = session_filters.get("paginate_by", 10)
        # Convertir a entero si es una lista
        try:
            paginate_by = int(
                paginate_by[0]
            )  # Convertir el primer elemento de la lista a entero
        except (TypeError, ValueError):
            paginate_by = int(paginate_by) if paginate_by else 10

        companies = get_modules_by_user(user.company_id, user.id, search)
        total_price_subquery = (
            Module.objects.filter(company_id=OuterRef("id"))
            .values("company_id")
            .annotate(total_price=Sum("price"))
            .values("total_price")
        )
        # Obtener el ordenamiento desde la solicitud actual
        order_by = self.request.GET.get('order_by') or self.request.POST.get('order_by') or session_filters.get('order_by', ['company_name'])[0]
        direction = self.request.GET.get('direction') or self.request.POST.get('direction') or session_filters.get('direction', ['asc'])[0]
        company_queryset = Company.objects.filter(
            visible=True, actived=True, id__in=[company["id"] for company in companies]
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
        companies_queryset = company_queryset.order_by(f"{order_prefix}{order_field}")
        # Paginación de compañías
        paginator = CustomPagination()
        paginator.page_size = paginate_by
        paginated_queryset = paginator.paginate_queryset(companies_queryset, request)
        serializer = CompanySerializer(paginated_queryset, many=True)
        serialized_data = serializer.data

        list_price = []

        # Cargar módulos asociados y calcular precios
        for company in paginated_queryset:
            modules = Module.objects.filter(company_id=company.id)
            total_price = (
                modules.aggregate(total_price=Sum("price"))["total_price"] or 0
            )
            list_price.append({"company_id": company.id, "total_price": total_price})

        # Formatear los resultados para incluir precios
        formatted_results = []
        for company in serialized_data:
            formatted_company = {
                "id": company["id"],
                "company_name": company["company_name"],
                "coin_name": company["coin_name"],
                "total_price": next(
                    item["total_price"]
                    for item in list_price
                    if item["company_id"] == company["id"]
                ),
                "modules": [
                    {"group_name": module["group_name"], "price": module["price"]}
                    for module in company["modules"]
                ],
            }
            formatted_results.append(formatted_company)

        return paginator.get_paginated_response(formatted_results)
    
    
@method_decorator(csrf_exempt, name='dispatch')
class ExportDataTicketsOpen(View):
    def get(self, request):
        search_query = request.GET.get('query', None)
        tickets = get_ticket_by_user(request.user.id, search_query)
        
        # Verificar si el usuario pertenece a una empresa distribuidora
        user_is_distributor = Company.objects.filter(
            provider=request.user.company_id, visible=True, actived=True
        ).exists()
        
        formatted_results = []
        # Encabezados traducidos
        headers = [
            "Ticket",
            _("Created by User"),
            _("Subject"),
            _("Priority"),
            _("Process"),
            _("Assigned To User"),
            _("Status"),
            _("Assigned To Company"),
            _("Created At"),
            _("Last Comment")
        ]

        for ticket in tickets:
            if user_is_distributor:
                company_name = ticket["company"]
            else:
                # Verificar si la empresa del ticket es un proveedor
                ticket_is_distributor = Company.objects.filter(
                    provider=ticket["company_id"], visible=True, actived=True
                ).exists()
                company_name = "Distributor" if ticket_is_distributor else ticket["company"]
            
            formatted_results.append({
                "id": ticket["id"],
                "company": company_name,
                "created_by": ticket["created_by"] or "",
                "subject": ticket["subject"] or "",
                "priority": ticket["priority"] or "",
                "process_type": ticket["process_type"] or "",
                "assign_to": ticket.get("assign_to") or "Unassigned",
                "status": "Open" if ticket["status"] else "Closed",
                "created_at": ticket["created_at"] or "",
                "last_comment": ticket["last_comment"] or "",
            })
            
        response_data = {
            'headers': headers,
            'data': formatted_results
        }

        return JsonResponse(response_data, safe=False)
    
@method_decorator(csrf_exempt, name='dispatch')
class ExportDataTicketsHistoric(View):
    def get(self, request):
        search_query = request.GET.get('query', None)
        tickets = get_ticket_closed(request.user.company_id, request.user.id, search_query)
        
        # Verificar si el usuario pertenece a una empresa distribuidora
        user_is_distributor = Company.objects.filter(
            provider=request.user.company_id, visible=True, actived=True
        ).exists()
        
        formatted_results = []
        # Encabezados traducidos
        headers = [
            "Ticket",
            _("Created by User"),
            _("Subject"),
            _("Priority"),
            _("Process"),
            _("Assigned To User"),
            _("Status"),
            _("Assigned To Company"),
            _("Created At"),
            _("Last Comment"),
            _("Duration")
        ]
        days_label = _("Days")
        hours_label = ("Hrs")
        minutes_label = ("Min")
        for ticket in tickets:
            duration = ticket.get("duration", "0,0,0,0")
            days, hours, minutes, __ = duration.split(",")

            # Formatear la duración
            duration_str = f"{int(days)} {days_label}" if int(days) > 0 else ""
            if int(hours) > 0:
                duration_str += f", {int(hours)} {hours_label}" if duration_str else f"{int(hours)} {hours_label}"
            if int(minutes) > 0:
                duration_str += f", {int(minutes)} {minutes_label}" if duration_str else f"{int(minutes)} {minutes_label}"
                
            if user_is_distributor:
                company_name = ticket["company"]
            else:
                # Verificar si la empresa del ticket es un proveedor
                ticket_is_distributor = Company.objects.filter(
                    provider=ticket["company_id"], visible=True, actived=True
                ).exists()
                company_name = "Distributor" if ticket_is_distributor else ticket["company"]
            
            formatted_results.append({
                "id": ticket["id"],
                "company": company_name,
                "created_by": ticket["created_by"] or "",
                "subject": ticket["subject"] or "",
                "priority": ticket["priority"] or "",
                "process_type": ticket["process_type"] or "",
                "assign_to": ticket.get("assign_to") or "Unassigned",
                "status": "Open" if ticket["status"] else "Closed",
                "created_at": ticket["created_at"] or "",
                "last_comment": ticket["last_comment"] or "",
                "duration": duration_str,
            })
            
        response_data = {
            'headers': headers,
            'data': formatted_results
        }

        return JsonResponse(response_data, safe=False)


class ExportDataModule(View):
    @method_decorator(csrf_exempt, name='dispatch')
    def get(self, request, *args, **kwargs):
        user = request.user
        params = request.GET if request.method == 'GET' else request.POST
        query = params.get("query", "").lower()
        search = params.get("q", query).lower()
        modules = get_modules_by_user(user.company_id, user.id, search)
        translated_item = [
            _("Maps"),
            _("Io Items report"),
            _("Dataplan"),
            _("Driver qualification configuration"),
            _("Daily report"),
            _("Assets group"),
            _("Assets"),
            ] #Lista para traducir nombres de modulos
        headers = [
            _("Company"),
            _("Coin"),
            _("Module/Price"),
            _("Total Price")
        ]
        formatted_results = []
        for module in modules:
            # Translate the module data
            module_data = module["module"] or ""
            # Assuming module_data is a string with concatenated name_en:price
            translated_module = ', '.join(
                f"{_(name_en)}: {price}"
                for name_en, price in (item.split(':') for item in module_data.split(', '))
            )
            formatted_results.append({
                "company": module["company_name"],
                "name": module["name"] or "",
                "modules": translated_module,
                "total_price": module["total_price"] or 0,
            })
        response_data = {
            'headers': headers,
            'data': formatted_results
        }

        return JsonResponse(response_data, safe=False)