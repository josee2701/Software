from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.translation import gettext as _
from apps.realtime.apis import extract_number, sort_key

from apps.realtime.models import Vehicle
from apps.whitelabel.models import Company, Process

from .models import User
from .sql import fetch_all_user


def list_proces_by_company(request, company_id, user_id):
    """
    Lista todos los procesos por empresa.

    Parámetros:
    - request: La solicitud HTTP recibida.
    - company_id: El ID de la empresa para filtrar los procesos.
    - user: El usuario que hace la solicitud.

    Retorna:
    Un objeto JsonResponse que contiene una lista de procesos, donde cada proceso tiene los campos 'id' y 'process_type'.
    """
    user = get_object_or_404(User, id=user_id)
    user_process = user.process_type.process_type.lower()
    
    # Filtrar los procesos según el tipo de usuario
    if user_process in ['admin', 'administrador']:
        processes = Process.objects.filter(company_id=company_id).values("id", "process_type")
    else:
        processes = Process.objects.filter(company_id=company_id).exclude(process_type__in=['Admin', 'Administrador']).values("id", "process_type")
    
    # Retornar los procesos como JsonResponse
    return JsonResponse({"process": list(processes)}, safe=False)


def list_companies_to_monitor_by_company(request, company_id):
    """
    Lista la compañía especificada y todas las compañías que esta monitorea, donde estas compañías tienen
    el mismo proveedor que el `company_id` especificado.

    Parámetros:
    - request: La solicitud HTTP recibida.
    - company_id: El ID de la compañía para filtrar los ítems monitoreados.

    Retorna:
    Un objeto JsonResponse que contiene una lista de las compañías monitoreadas.
    """
    try:
        company = Company.objects.get(pk=company_id)
        # Filtramos las compañías que esta compañía monitorea y que tienen el mismo proveedor.
        monitored_companies = Company.objects.filter(
            id__in=company.companies_to_monitor.values_list("id", flat=True),
            provider=company_id,
        ).values("id", "company_name")

        return JsonResponse(
            {
                "companies_to_monitor": list(monitored_companies),
                "your_company": {
                    "id": company.id,
                    "company_name": company.company_name,
                },
            },
            safe=False,
        )
    except Company.DoesNotExist:
        return JsonResponse({"error": "Company not found"}, status=404)


def list_vehicles_to_monitor_by_company(request, company_id):
    """
    Lista la compañía especificada y todas las compañías que esta monitorea, donde estas compañías tienen
    el mismo proveedor que el `company_id` especificado.

    Parámetros:
    - request: La solicitud HTTP recibida.
    - company_id: El ID de la compañía para filtrar los ítems monitoreados.

    Retorna:
    Un objeto JsonResponse que contiene una lista de las compañías monitoreadas.
    """
    try:
        vehicle = Vehicle.objects.get(pk=company_id)
        # Filtramos las compañías que esta compañía monitorea y que tienen el mismo proveedor.
        monitored_vehicle = Vehicle.objects.filter(
            company_id=company_id, visible=True
        ).values("id", "license")

        return JsonResponse(
            {
                "vehicles_to_monitor": list(monitored_vehicle),
            },
            safe=False,
        )
    except Company.DoesNotExist:
        return JsonResponse({"error": "Company not found"}, status=404)


@method_decorator(csrf_exempt, name="dispatch")
class SearchUser(View):
    def get(self, request):
        company = request.user.company_id
        user_id = request.user.id
        session_filters = request.session.get(f'filters_sorted_users_{user_id}', {})
        search_query = request.GET.get("query", None)
        page_number = request.GET.get('page', session_filters.get('page', [1]))[0]

        if not company or not user_id:
            return JsonResponse({"error": "Faltan parámetros"}, status=400)
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
        order_by = session_filters.get('order_by', [None])[0]
        direction = session_filters.get('direction', [None])[0]
        users = fetch_all_user(company, user_id, search_query)
        key_function = sort_key(order_by)
        # Determinar si es orden descendente
        reverse = direction == 'desc'
        try:
            users = sorted(users, key=key_function, reverse=reverse)
        except KeyError:
            # Ordenamiento por defecto si la clave no existe
            users = sorted(users, key=lambda x: x['company'].lower(), reverse=reverse)
        page_size = paginate_by  # Número de elementos por página.
        paginator = Paginator(users, page_size)
        try:
            page = paginator.page(page_number)
        except PageNotAnInteger:
            page = paginator.page(1)
        except EmptyPage:
            page = paginator.page(paginator.num_pages)

        formatted_results = []
        for user in page.object_list:
            formatted_results.append(
                {
                    "id": user["id"],
                    "company": user["company"] or "",
                    "process": user["process"] or "",
                    "username": user["username"] or "",
                    "first_name": user["first_name"] or "",
                    "last_name": user["last_name"] or "",
                    "email": user["email"] or "",
                    "is_active": user["is_active"] or False,
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
    
@method_decorator(csrf_exempt, name='dispatch')
class ExportDataUsers(View):
    def get(self, request):
        search_query = request.GET.get('query', None)
        users = fetch_all_user(request.user.company_id, search_query)
        formatted_results = []
        # Encabezados traducidos
        headers = [
            _("company"),
            _("process"),
            _("username"),
            _("first name"),
            _("last name"),
            _("Email"),
            _("Status")
        ]

        for user in users:
            formatted_results.append({
                "company": user["company"] or "",
                "process": user["process"] or "",
                "username": user["username"] or "",
                "first_name": user["first_name"] or "",
                "last_name": user["last_name"] or "",
                "email": user["email"] or "",
                "is_active": user["is_active"] or False,
            })
        response_data = {
            'headers': headers,
            'data': formatted_results
        }

        return JsonResponse(response_data, safe=False)
