import re
from datetime import datetime

from django.contrib.auth.decorators import login_required
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db import DatabaseError, connection
from django.db.models import F, Q, Value
from django.db.models.functions import Concat
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import translation
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from apps.whitelabel.models import Company

from .models import (Brands_assets, DataPlan, Device, FamilyModelUEC,
                     Line_assets, Manufacture, SimCard, Vehicle)
from .sql import (ListDeviceByCompany, ListVehicleByUserAndCompany,
                  ListVehicleGroupsByCompany, fetch_all_dataplan,
                  fetch_all_geozones, fetch_all_response_commands,
                  fetch_all_sending_commands, fetch_all_simcards)


def list_family_model(request, manufacture_id):
    family_model = FamilyModelUEC.objects.filter(manufacture_id=manufacture_id).annotate(
        model_name=Concat(F('model__name'), Value(' '), F('model__network_type'))
    ).values('id', 'model', 'model_name')
    return JsonResponse(list(family_model), safe=False)

def list_manufacture(request,family_model_id):
    try:
        family_model = FamilyModelUEC.objects.get(id=family_model_id)
        return JsonResponse({
            'manufacture_id': family_model.manufacture.id,
            'manufacture_name': family_model.manufacture.name
        })
    except FamilyModelUEC.DoesNotExist:
        return JsonResponse({'error': 'Family model not found'}, status=404)

def get_data_plans(request, company_id):
    """
    Obtiene los planes de datos de una compañía específica.

    Args:
        request (HttpRequest): La solicitud HTTP recibida.
        company_id (int): El ID de la compañía.

    Returns:
        JsonResponse: Una respuesta JSON que contiene los planes de datos de la compañía.
    """
    # Asegúrate de que los usuarios puedan ver planes de otras compañías si es necesario
    # Puedes agregar controles adicionales aquí si hay restricciones en quien puede ver qué
    data_plans = (
        DataPlan.objects.filter(company_id=company_id)
        .annotate(operator_name=F("operator__name"))
        .values("id", "name", "operator_name")
    )
    # Modifica el nombre del plan
    data_plans = list(data_plans)
    for plan in data_plans:
        plan["name"] = plan["name"].lower()
    return JsonResponse(list(data_plans), safe=False)


def get_company_id_items_report(request):
    """
    Metodo para obtener la información de la instancia de Io_items_report por compañia
    """
    company_id = request.GET.get("company_id")

    query_sql = """
        EXEC [dbo].[GetCompanyItemsReport] @CompanyID=%s
        """
    # Inicializa una lista para almacenar los resultados
    data = {}

    try:
        if connection:
            with connection.cursor() as cursor:
                cursor.execute(query_sql, (company_id,))
                # Obtén la primera fila de resultados
                fila = cursor.fetchone()
                if fila:
                    data["info_widgets"] = fila[0]
                    data["info_reports"] = fila[1]

    except Exception as e:
        print(f"Error al realizar la consulta de 'GetCompanyItemsReport': {e}")
        # Si hay un error, devuelve un diccionario vacío o un mensaje de error, según lo que necesites
        return JsonResponse({"error": "Error al obtener los datos"})

    # Devuelve los resultados como una respuesta JSON
    return JsonResponse(data)


def get_commands(request, imei):
    """
    API para obtener los comandos disponibles para un dispositivo específico.
    """
    query_sql = """
        EXEC [dbo].[GetCommands] @IMEI=%s
        """
    # Inicializa una lista para almacenar los resultados
    commands = []

    try:
        if connection:
            with connection.cursor() as cursor:
                cursor.execute(query_sql % (imei))

                # Genera una lista de diccionarios a partir de los resultados de la consulta
                commands = [{"id": fila[0], "name": fila[1]} for fila in cursor]

    except DatabaseError as e:
        # Manejar el error de base de datos aquí
        print("Error de base de datos:", e)

    except Exception as e:
        print(f"Error al realizar la consulta de comandos 'get_commands': {e}")

    return JsonResponse({"commands": commands}, safe=False)


def get_user_vehicles(company_id, user):
    """
    Obtener los vehículos que el usuario puede ver según la lógica de filtrado proporcionada.
    """
    query_sql = """
        EXEC [dbo].[GetUserVehicles] @CompanyId=%s, @UserId=%s
        """
    # Inicializa una lista para almacenar los resultados
    vehicles = []

    try:
        if connection:
            with connection.cursor() as cursor:
                cursor.execute(query_sql % (company_id, user.id))
                results = cursor.fetchall()
                if results:
                    # Genera una lista de tuplas a partir de los resultados de la consulta
                    vehicles.extend([(fila[1], fila[0]) for fila in results])
                else:
                    # Ejecutar la segunda consulta
                    cursor.execute(
                        """
                        EXEC [dbo].[GetVehiclesByProviderOrCompany] @CompanyId=%s
                    """,
                        [company_id],
                    )
                    results = cursor.fetchall()
                    vehicles.extend([(fila[1], fila[0]) for fila in results])

    except DatabaseError as e:
        # Manejar el error de base de datos aquí
        print("Error de base de datos:", e)

    except Exception as e:
        print(f"Error al realizar la consulta de vehiculos 'get_user_vehicles': {e}")

    return vehicles


class AvailableSimCardsAPI(View):
    """
    API para obtener las tarjetas SIM disponibles.

    Parámetros:
    - request: La solicitud HTTP recibida.
    - company_id: El ID de la compañía para filtrar las tarjetas SIM disponibles.
    - imei (opcional): El IMEI del dispositivo para filtrar las tarjetas SIM asignadas.

    Retorna:
    - Una respuesta JSON que contiene las tarjetas SIM disponibles.

    Ejemplo de uso:
    ```
    GET /api/simcards/available?company_id=1&imei=1234567890
    ```
    """

    def get(self, request, company_id, imei=None):
        current_device = None
        if imei:
            current_device = get_object_or_404(Device, imei=imei)

        # Obten todas las SIM cards asignadas excepto la del dispositivo actual.
        assigned_simcards = (
            SimCard.objects.filter(
                device__isnull=False, device__visible=True, is_active=True
            )
            .exclude(
                id=current_device.simcard.id
                if current_device and current_device.simcard
                else None
            )
            .values_list("id", flat=True)
        )

        # Filtra las SIM cards disponibles.
        available_simcards = (
            SimCard.objects.filter(company_id=company_id, visible=True, is_active=True)
            .exclude(id__in=assigned_simcards)
            .values("id", "phone_number")
        )

        result = list(available_simcards)
        if current_device and current_device.simcard:
            # Asegúrate de no duplicar la SIM card asignada.
            if not any(
                simcard["id"] == current_device.simcard.id for simcard in result
            ):
                result.append(
                    {
                        "id": current_device.simcard.id,
                        "phone_number": current_device.simcard.phone_number,
                    }
                )

        return JsonResponse(result, safe=False)


class ModelsByManufactureAPI(View):
    @method_decorator(login_required)
    def get(self, request, manufacture_id):
        models = FamilyModelUEC.objects.filter(
            manufacture_id=manufacture_id
        ).select_related("model")
        model_list = [
            {
                "id": m.model.id,
                "name": m.model.name,
                "network_type": m.model.network_type,
            }
            for m in models
        ]
        return JsonResponse(model_list, safe=False)


class AvailableDevicesAPI(View):
    def get(self, request, company_id, vehicle_id=None):
        # Este será el dispositivo actualmente asignado si estamos editando
        current_device = None

        # Si estamos editando y un vehicle_id fue proporcionado
        if vehicle_id:
            # Obtenemos el vehículo actualmente editado
            current_vehicle = get_object_or_404(Vehicle, id=vehicle_id)
            # Obtenemos el dispositivo actualmente asignado a este vehículo
            current_device = current_vehicle.device

        # Obtenemos todos los dispositivos que no están asignados a ningún vehículo
        available_devices_query = Device.objects.filter(
            company_id=company_id,
            vehicle__isnull=True,  # Dispositivos no asignados
            visible=True,
            is_active=True,
        )

        # Convertimos la consulta a una lista para poder modificarla si es necesario
        available_devices = list(available_devices_query.values("imei"))

        # Si hay un dispositivo actualmente asignado, lo agregamos a la lista
        # Esto asegura que el dispositivo asignado sea seleccionado por defecto en modo edición
        if current_device:
            # Agregamos el dispositivo actual al principio de la lista si no está ya en la lista
            if not any(
                device["imei"] == current_device.imei for device in available_devices
            ):
                available_devices.insert(
                    0,
                    {
                        "imei": current_device.imei,
                    },
                )

        return JsonResponse(available_devices, safe=False)


def get_geozone_by_id(geozone_id):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
    z.id,
    z.name,
    z.description,
    z.company_id,
    c.company_name AS company_name,  -- Asumiendo que existe una relación con una tabla de compañías
    z.type_event,
    z.shape_type,
    z.latitude,
    z.longitude,
    z.color,
    z.color_edges,
    z.polygon
FROM
    realtime_geozones z
    LEFT JOIN whitelabel_company c ON z.company_id = c.id
WHERE
    z.id = 2
        """,
            [geozone_id],
        )
        row = cursor.fetchone()

        if row:
            columns = [col[0] for col in cursor.description]
            return dict(zip(columns, row))
        else:
            return None


def get_brands(request):
    vehicle_type_id = request.GET.get("vehicle_type_id")
    if vehicle_type_id:
        type_brand_assets = Brands_assets.objects.filter(type_asset_id=vehicle_type_id)
        brands = [
            {
                "brand_id": t.id,
                "brand": t.brand,
            }
            for t in type_brand_assets
        ]
        return JsonResponse({"brands": brands})
    return JsonResponse({"error": "Invalid vehicle type ID"}, status=400)


def get_lines(request):
    brand_id = request.GET.get("brand_id")
    if brand_id:
        lines = Line_assets.objects.filter(brand_asset_id=brand_id)
        lines_data = [
            {
                "line_id": line.id,
                "line": line.line,
            }
            for line in lines
        ]
        return JsonResponse({"lines": lines_data})
    return JsonResponse({"error": "Invalid brand ID"}, status=400)


def get_user_companies(user):
    if user.company_id == 1:
        companies = Company.objects.filter(visible=True, actived=True)
    elif user.companies_to_monitor.exists():
        companies = user.companies_to_monitor.filter(visible=True, actived=True)
    else:
        companies = Company.objects.filter(
            Q(id=user.company_id) | Q(provider_id=user.company_id),
            visible=True,
            actived=True,
        )
    companies = companies.order_by("company_name")

    if user.company_id == 1:
        modified_companies = []
        for company in companies:
            if company.provider_id:
                provider_company = Company.objects.get(id=company.provider_id)
                modified_name = (
                    f"{company.company_name} -- {provider_company.company_name}"
                )
            else:
                modified_name = company.company_name
            modified_companies.append((company.id, modified_name))
        return modified_companies
    else:
        return companies


@method_decorator(csrf_exempt, name="dispatch")
class SearchVehicles(View):
    def get(self, request):
        company = request.user.company_id
        user_id = request.user.id
        session_filters = request.session.get(f'filters_sorted_vehicle_{user_id}', {})
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
        vehicles = ListVehicleByUserAndCompany(company, user_id, search_query)
        order_by = session_filters.get('order_by', [None])[0]
        direction = session_filters.get('direction', [None])[0]
        page_size = paginate_by # Número de elementos por página.
        # Obtener la función de clave para ordenar
        key_function = sort_key(order_by)
        # Determinar si es orden descendente
        reverse = direction == 'desc'
        try:
            vehicles = sorted(vehicles, key=key_function, reverse=reverse)
        except KeyError:
            # Ordenamiento por defecto si la clave no existe
            vehicles = sorted(vehicles, key=lambda x: x['company'].lower(), reverse=reverse)
        page_size = paginate_by  # Número de elementos por página.
        paginator = Paginator(vehicles, page_size)

        try:
            page = paginator.page(page_number)
        except PageNotAnInteger:
            page = paginator.page(1)
        except EmptyPage:
            page = paginator.page(paginator.num_pages)
        current_language = translation.get_language()

        formatted_results = []
        for vehicle in page.object_list:
            installation_date = vehicle["installation_date"]
            month_name = installation_date.strftime("%B")
            month_name = _(month_name)
            if installation_date:
                if current_language == "es":
                    # Formato en español
                    formatted_date = installation_date.strftime(
                        f'%d {_("de")} {month_name} {_("de")} %Y'
                    )
                else:
                    # Formato en inglés u otros idiomas
                    formatted_date = installation_date.strftime("%B %d, %Y")
            formatted_results.append(
                {
                    "id": vehicle["id"],
                    "device": vehicle["device"],
                    "company": vehicle["company"] or "",
                    "license": vehicle["license"] or "",
                    "vehicle_type": vehicle["vehicle_type"] or "",
                    "n_interno": vehicle["n_interno"] or "",
                    "is_active": vehicle["is_active"] or False,
                    "icon": vehicle["icon"] or "",
                    "installation_date": formatted_date,
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
class SearchDevices(View):
    def get(self, request):
        company = request.user.company_id
        user_id = request.user.id
        session_filters = request.session.get(f'filters_sorted_device_{user_id}', {})
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
        devices = ListDeviceByCompany(company, user_id, search_query)
        order_by = session_filters.get('order_by', [None])[0]
        direction = session_filters.get('direction', [None])[0]
        # Obtener la función de clave para ordenar
        key_function = sort_key(order_by)
        # Determinar si es orden descendente
        reverse = direction == 'desc'
        try:
            devices = sorted(devices, key=key_function, reverse=reverse)
        except KeyError:
            # Ordenamiento por defecto si la clave no existe
            devices = sorted(devices, key=lambda x: x['company'].lower(), reverse=reverse)
        page_size = paginate_by  # Número de elementos por página.
        paginator = Paginator(devices, page_size)

        try:
            page = paginator.page(page_number)
        except PageNotAnInteger:
            page = paginator.page(1)
        except EmptyPage:
            page = paginator.page(paginator.num_pages)
        current_language = translation.get_language()

        formatted_results = []
        for device in page.object_list:
            installation_date = device["create_date"]
            month_name = installation_date.strftime("%B")
            month_name = _(month_name)
            if installation_date:
                if current_language == "es":
                    # Formato en español
                    formatted_date = installation_date.strftime(
                        f'%d {_("de")} {month_name} {_("de")} %Y'
                    )
                else:
                    # Formato en inglés u otros idiomas
                    formatted_date = installation_date.strftime("%B %d, %Y")
            formatted_results.append(
                {
                    "pk": device["pk"],
                    "imei": device["imei"],
                    "company": device["company"] or "",
                    "ip": device["ip"] or "",
                    "serial_number": device["serial_number"] or "",
                    "simcard": device["simcard"] or "",
                    "simcard_visible": device["simcard_visible"] or False,
                    "is_active": device["is_active"] or False,
                    "familymodel": device["familymodel"] or "",
                    "create_date": _(formatted_date),
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
class SearchSimcards(View):
    def get(self, request):
        company = request.user.company_id
        user_id = request.user.id
        session_filters = request.session.get(f'filters_sorted_simcard_{user_id}', {})
        search_query = request.GET.get("query", None)
        page_number = request.GET.get('page', session_filters.get('page', [1]))[0]

        if not company or not user_id:
            return JsonResponse({"error": "Faltan parámetros"}, status=400)
        paginate_by = request.POST.get(
            "paginate_by", None
        )  # Obtener paginate_by de los parámetros POST
        if paginate_by is None:
            paginate_by = session_filters.get("paginate_by", 15)
        # Convertir a entero si es una lista
        try:
            paginate_by = int(
                paginate_by[0]
            )  # Convertir el primer elemento de la lista a entero
        except (TypeError, ValueError):
            paginate_by = int(paginate_by) if paginate_by else 15
        simcards = fetch_all_simcards(request.user.company, request.user, search_query)
        order_by = session_filters.get('order_by', [None])[0]
        direction = session_filters.get('direction', [None])[0]
        # Obtener la función de clave para ordenar
        key_function = sort_key(order_by)
        # Determinar si es orden descendente
        reverse = direction == 'desc'
        try:
            simcards = sorted(simcards, key=key_function, reverse=reverse)
        except KeyError:
            # Ordenamiento por defecto si la clave no existe
            simcards = sorted(simcards, key=lambda x: x['Company'].lower(), reverse=reverse)
        page_size = paginate_by  # Número de elementos por página.
        paginator = Paginator(simcards, page_size)
        try:
            page = paginator.page(page_number)
        except PageNotAnInteger:
            page = paginator.page(1)
        except EmptyPage:
            page = paginator.page(paginator.num_pages)
        current_language = translation.get_language()

        formatted_results = []
        for simcard in page.object_list:
            installation_date = simcard["activate_date"]
            month_name = installation_date.strftime("%B")
            month_name = _(month_name)
            if installation_date:
                if current_language == "es":
                    # Formato en español
                    formatted_date = installation_date.strftime(
                        f'%d {_("de")} {month_name} {_("de")} %Y'
                    )
                else:
                    # Formato en inglés u otros idiomas
                    formatted_date = installation_date.strftime("%B %d, %Y")
            formatted_results.append(
                {
                    "id": simcard["id"],
                    "company": simcard["Company"] or "",
                    "serial_number": simcard["serial_number"] or "",
                    "phone_number": simcard["phone_number"] or "",
                    "data_plan": simcard["data_plan"] or "",
                    "is_active": simcard["is_active"] or False,
                    "activate_date": formatted_date,
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
class SearchDataPlan(View):
    def get(self, request):
        company = request.user.company_id
        user_id = request.user.id
        session_filters = request.session.get(f'filters_sorted_dataplan_{user_id}', {})
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
        dataplans = fetch_all_dataplan(request.user.company, request.user, search_query)
        order_by = session_filters.get('order_by', [None])[0]
        direction = session_filters.get('direction', [None])[0]
        # Obtener la función de clave para ordenar
        key_function = sort_key(order_by)
        # Determinar si es orden descendente
        reverse = direction == 'desc'
        try:
            dataplans = sorted(dataplans, key=key_function, reverse=reverse)
        except KeyError:
            # Ordenamiento por defecto si la clave no existe
            dataplans = sorted(dataplans, key=lambda x: x['Company'].lower(), reverse=reverse)
        page_size = paginate_by  # Número de elementos por página.
        paginator = Paginator(dataplans, page_size)
        try:
            page = paginator.page(page_number)
        except PageNotAnInteger:
            page = paginator.page(1)
        except EmptyPage:
            page = paginator.page(paginator.num_pages)

        formatted_results = []
        for dataplan in page.object_list:
            formatted_results.append(
                {
                    "id": dataplan["id"],
                    "company": dataplan["Company"] or "",
                    "DataPlanName": dataplan["DataPlanName"] or "",
                    "operator": dataplan["Operator"] or "",
                    "coin": dataplan["Coin"] or "",
                    "price": dataplan["price"] or "",
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
class SearchSendCommand(View):
    def format_date(self, date_obj):
        if isinstance(date_obj, datetime):
            return date_obj.strftime("%d/%m/%Y %H:%M:%S")
        return ""

    def get(self, request):
        company = request.user.company_id
        user_id = request.user.id
        session_filters = request.session.get(f'filters_sorted_sendcommands_{user_id}', {})
        search_query = request.GET.get('query', None)
        page_number = request.GET.get('page', session_filters.get('page', [1]))[0]
        if not company or not user_id:
            return JsonResponse({"error": "Faltan parámetros"}, status=400)
        paginate_by = request.POST.get('paginate_by', None)  # Obtener paginate_by de los parámetros POST
        if paginate_by is None:
            paginate_by = session_filters.get('paginate_by', 20)
        # Convertir a entero si es una lista
        try:
            paginate_by = int(
                paginate_by[0]
            )  # Convertir el primer elemento de la lista a entero
        except (TypeError, ValueError):
            paginate_by = int(paginate_by) if paginate_by else 20
        send_commands = fetch_all_sending_commands(company, user_id, search_query)
        order_by = session_filters.get('order_by', [None])[0]
        direction = session_filters.get('direction', [None])[0]
        # Determinar si es orden descendente
        reverse = direction == 'desc'
        try:
            send_commands = sorted(send_commands, key=sort_key_commands_datetime(order_by), reverse=reverse)
        except KeyError:
            # Ordenamiento por defecto si la clave no existe
            send_commands = sorted(send_commands, key=lambda x: x['id'].lower(), reverse=reverse)
        page_size = paginate_by  # Número de elementos por página.
        paginator = Paginator(send_commands, page_size)
        try:
            page = paginator.page(page_number)
        except PageNotAnInteger:
            page = paginator.page(1)
        except EmptyPage:
            page = paginator.page(paginator.num_pages)

        formatted_results = []
        for send_command in page.object_list:
            formatted_results.append(
                {
                    "id": send_command["id"],
                    "command": send_command["command"] or "",
                    "codigo": send_command["codigo"] or "",
                    "model": send_command["familymodel_name"] or "",
                    "license": send_command["license"] or "",
                    "status": send_command["status"] or False,
                    "shipping_date": send_command['shipping_date'].strftime('%Y-%m-%d %H:%M:%S') or "",
                    "answer_date": send_command["answer_date"].strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                    or "",
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
class SearchResponseCommand(View):
    def format_date(self, date_obj):
        if isinstance(date_obj, datetime):
            return date_obj.strftime("%d/%m/%Y %H:%M:%S")
        return ""

    def get(self, request):
        company = request.user.company_id
        user_id = request.user.id
        session_filters = request.session.get(f'filters_sorted_responsecommands_{user_id}', {})
        search_query = request.GET.get('query', None)
        page_number = request.GET.get('page', session_filters.get('page', [1]))[0]

        if not company or not user_id:
            return JsonResponse({"error": "Faltan parámetros"}, status=400)
        paginate_by = request.POST.get('paginate_by', None)  # Obtener paginate_by de los parámetros GET
        if paginate_by is None:
            session_filters = request.session.get(
                f"filters_sorted_responsecommands_{user_id}", {}
            )
            paginate_by = session_filters.get("paginate_by", 20)
        # Convertir a entero si es una lista
        try:
            paginate_by = int(
                paginate_by[0]
            )  # Convertir el primer elemento de la lista a entero
        except (TypeError, ValueError):
            paginate_by = int(paginate_by) if paginate_by else 20
        response_commands = fetch_all_response_commands(company, user_id, search_query)
        order_by = session_filters.get('order_by', [None])[0]
        direction = session_filters.get('direction', [None])[0]
        page_size = paginate_by # Número de elementos por página.
        # Obtener la función de clave para ordenar
        key_function = sort_key(order_by)
        # Determinar si es orden descendente
        reverse = direction == 'desc'
        try:
            response_commands = sorted(response_commands, key=key_function, reverse=reverse)
        except KeyError:
            # Ordenamiento por defecto si la clave no existe
            response_commands = sorted(response_commands, key=lambda x: x['id'].lower(), reverse=reverse)
        paginator = Paginator(response_commands, page_size)
        try:
            page = paginator.page(page_number)
        except PageNotAnInteger:
            page = paginator.page(1)
        except EmptyPage:
            page = paginator.page(paginator.num_pages)

        formatted_results = []
        for response_command in page.object_list:
            formatted_results.append(
                {
                    "id": response_command["id"],
                    "response": response_command["response"] or "",
                    "ip": response_command["ip"] or "",
                    "license": response_command["license"] or "",
                    "answer_date": response_command["answer_date"].strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                    or "",
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
class SearchGeofence(View):
    def format_date(self, date_obj):
        if isinstance(date_obj, datetime):
            return date_obj.strftime("%d/%m/%Y %H:%M:%S")
        return ""

    def get(self, request):
        company = request.user.company_id
        user_id = request.user.id
        session_filters = request.session.get(f'filters_sorted_geofence_{user_id}', {})
        search_query = request.GET.get('query', None)
        page_number = request.GET.get('page', session_filters.get('page', [1]))[0]

        if not company or not user_id:
            return JsonResponse({"error": "Faltan parámetros"}, status=400)
        paginate_by = request.POST.get('paginate_by', None)  # Obtener paginate_by de los parámetros POST
        if paginate_by is None:
            paginate_by = session_filters.get('paginate_by', 20)
        # Convertir a entero si es una lista
        try:
            paginate_by = int(
                paginate_by[0]
            )  # Convertir el primer elemento de la lista a entero
        except (TypeError, ValueError):
            paginate_by = int(paginate_by) if paginate_by else 20
        geofences = fetch_all_geozones(company, user_id, search_query)
        order_by = session_filters.get('order_by', [None])[0]
        direction = session_filters.get('direction', [None])[0]
        page_size = paginate_by # Número de elementos por página.
        # Obtener la función de clave para ordenar
        key_function = sort_key(order_by)
        # Determinar si es orden descendente
        reverse = direction == 'desc'
        try:
            geofences = sorted(geofences, key=key_function, reverse=reverse)
        except KeyError:
            # Ordenamiento por defecto si la clave no existe
            geofences = sorted(geofences, key=lambda x: x['company'].lower(), reverse=reverse)
        page_size = paginate_by  # Número de elementos por página.
        paginator = Paginator(geofences, page_size)
        try:
            page = paginator.page(page_number)
        except PageNotAnInteger:
            page = paginator.page(1)
        except EmptyPage:
            page = paginator.page(paginator.num_pages)

        formatted_results = []
        for geofence in page.object_list:
            formatted_results.append(
                {
                    "id": geofence["id"],
                    "company": geofence["company"] or "",
                    "name": geofence["name"] or "",
                    "type_event": geofence["type_event"] or "",
                    "shape_type": geofence["shape_type"] or "",
                    "latitude": geofence["latitude"] or "",
                    "longitude": geofence["longitude"] or "",
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
class SearchGroupAssets(View):
    def get(self, request):
        company = request.user.company_id
        user_id = request.user.id
        session_filters = request.session.get(f'filters_sorted_vehiclegroup_{user_id}', {})
        search_query = request.GET.get('query', None)
        page_number = request.GET.get('page', session_filters.get('page', [1]))[0]

        if not company or not user_id:
            return JsonResponse({"error": "Faltan parámetros"}, status=400)
        paginate_by = request.POST.get(
            "paginate_by", None
        )  # Obtener paginate_by de los parámetros GET
        if paginate_by is None:
            session_filters = request.session.get(
                f"filters_sorted_vehiclegroup_{user_id}", {}
            )
            paginate_by = session_filters.get("paginate_by", 15)
        # Convertir a entero si es una lista
        try:
            paginate_by = int(
                paginate_by[0]
            )  # Convertir el primer elemento de la lista a entero
        except (TypeError, ValueError):
            paginate_by = int(paginate_by) if paginate_by else 15
        groupAssets = ListVehicleGroupsByCompany(company, search_query)
        order_by = session_filters.get('order_by', [None])[0]
        direction = session_filters.get('direction', [None])[0]
        key_function = sort_key(order_by)
        # Determinar si es orden descendente
        reverse = direction == 'desc'
        try:
            groupAssets = sorted(groupAssets, key=key_function, reverse=reverse)
        except KeyError:
            # Ordenamiento por defecto si la clave no existe
            groupAssets = sorted(groupAssets, key=lambda x: x['name'].lower(), reverse=reverse)
        page_size = paginate_by  # Número de elementos por página.
        paginator = Paginator(groupAssets, page_size)
        try:
            page = paginator.page(page_number)
        except PageNotAnInteger:
            page = paginator.page(1)
        except EmptyPage:
            page = paginator.page(paginator.num_pages)

        formatted_results = []
        for groupAsset in page.object_list:
            formatted_results.append(
                {
                    "id": groupAsset["id"],
                    "name": groupAsset["name"] or "",
                    "VehicleCount": groupAsset["VehicleCount"] or 0,
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


def extract_number(text):
    match = re.search(r"\d+", text)
    return int(match.group()) if match else float("inf")


def extract_number_tp(s):
    """
    Extrae el primer número encontrado en una cadena y lo devuelve como un número entero.
    Si no se encuentra ningún número, devuelve 0.
    """
    match = re.search(r"\d+", s)
    return int(match.group()) if match else 0

def sort_key(order_by):
    """
    Función clave para ordenar campos de las listas main.

    Args:
        order_by (str): El campo por el que ordenar.

    Returns:
        callable: Función para usar como clave en la ordenación.
    """
    def key(x):
        value = x.get(order_by)
        if value is None or value == '':
            return (4, '')  # Prioridad 4 para valores nulos o vacíos
        if isinstance(value, str):
            # Verificar si comienza con números, letras o caracteres especiales
            if value[0].isdigit():
                return (1, extract_number(value))  # Prioridad 1 para números
            elif value[0].isalpha():
                return (2, value.lower())  # Prioridad 2 para letras
            else:
                return (3, value.lower())  # Prioridad 3 para caracteres especiales
        return value
    return key

def sort_key_commands_datetime(order_by):
        def extract_number(value):
            # Implementa tu lógica para extraer números si es necesario
            return int(''.join(filter(str.isdigit, value)))
        def date_key(value):
            # Manejo específico para fechas nulas o vacías
            if value is None:
                return (4, datetime.max)  # Prioridad 4, y asignamos la fecha máxima para que quede al final
            return (1, value)  # Prioridad 1 para fechas válidas

        def key_func(x):
            value = x.get(order_by)
            if isinstance(value, datetime):
                # Si el campo es una fecha
                return date_key(value)
            elif value is None or value == '':
                # Valores nulos o vacíos
                return (4, '')  # Prioridad 4 para valores nulos o vacíos
            if isinstance(value, str):
                # Verificar si comienza con números, letras o caracteres especiales
                if value[0].isdigit():
                    return (2, extract_number(value))  # Prioridad 2 para números
                elif value[0].isalpha():
                    return (3, value.lower())  # Prioridad 3 para letras
                else:
                    return (4, value.lower())  # Prioridad 4 para caracteres especiales
            return (5, value)  # Prioridad 5 para otros tipos de valores
        return key_func

@method_decorator(csrf_exempt, name='dispatch')
class ExportDataSendCommands(View):
    def format_date(self, date_obj):
        if isinstance(date_obj, datetime):
            return date_obj.strftime('%d/%m/%Y %H:%M:%S')
        return ""
    def get(self, request):
        company = request.user.company_id
        user_id = request.user.id
        search_query = request.GET.get('query', None)
        send_commands = fetch_all_sending_commands(company, user_id, search_query)
        formatted_results = []
        # Encabezados traducidos
        headers = [
            _("command"),
            _("code"),
            _("model"),
            _("License"),
            _("Status"),
            _("shipping_date"),
            _("answer_date")
        ]

        for send_command in send_commands:
            formatted_results.append({
                "command": send_command['command'] or "",
                "codigo": send_command['codigo'] or "",
                "model": send_command['familymodel_name'] or "",
                "license": send_command['license'] or "",
                "status": send_command['status'] or False,
                "shipping_date": send_command['shipping_date'].strftime('%Y-%m-%d %H:%M:%S') or "",
                "answer_date": send_command['answer_date'].strftime('%Y-%m-%d %H:%M:%S') or "",
            })
        response_data = {
            'headers': headers,
            'data': formatted_results
        }
        return JsonResponse(response_data, safe=False)

@method_decorator(csrf_exempt, name='dispatch')
class ExportDataResponseCommands(View):
    def format_date(self, date_obj):
        if isinstance(date_obj, datetime):
            return date_obj.strftime('%d/%m/%Y %H:%M:%S')
        return ""
    def get(self, request):
        company = request.user.company_id
        user_id = request.user.id
        search_query = request.GET.get('query', None)
        response_commands = fetch_all_response_commands(company, user_id, search_query)
        formatted_results = []
        # Encabezados traducidos
        headers = [
            _("license"),
            _("ip"),
            _("response"),
            _("answer_date")
        ]

        for response_command in response_commands:
            formatted_results.append({
                "ip": response_command['ip'] or "",
                "response": response_command['response'] or "",
                "license": response_command['license'] or "",
                "answer_date": response_command['answer_date'].strftime('%Y-%m-%d %H:%M:%S') or "",
            })
        response_data = {
            'headers': headers,
            'data': formatted_results
        }
        return JsonResponse(response_data, safe=False)
    
@method_decorator(csrf_exempt, name='dispatch')
class ExportDataGeofence(View):
    def get(self, request):
        company = request.user.company_id
        user_id = request.user.id
        search_query = request.GET.get('query', None)
        geofences = fetch_all_geozones(company, user_id, search_query)
        formatted_results = []
        # Encabezados traducidos
        headers = [
            _("Company"),
            _("Name geozone"),
            _("Event"),
            _("Type the geozone"),
            _("Latitude"),
            _("Longitude")
        ]

        for geofence in geofences:
            formatted_results.append({
                "company": geofence['company'] or "",
                "name": geofence['name'] or "",
                "type_event": geofence['type_event'] or "",
                "shape_type": geofence['shape_type'] or "",
                "latitude": geofence['latitude'] or "",
                "longitude": geofence['longitude'] or "",
            })
        response_data = {
            'headers': headers,
            'data': formatted_results
        }
        return JsonResponse(response_data, safe=False)
    
@method_decorator(csrf_exempt, name='dispatch')
class ExportDataPlans(View):
    def get(self, request):
        search_query = request.GET.get('query', None)
        dataplans = fetch_all_dataplan(request.user.company, request.user, search_query)
        formatted_results = []
        # Encabezados traducidos
        headers = [
            _("Company"),
            _("Name"),
            _("Operator"),
            _("Coin"),
            _("Price")
        ]

        for dataplan in dataplans:
            formatted_results.append({
                "company": dataplan["Company"] or "",
                "DataPlanName": dataplan["DataPlanName"] or "",
                "operator": dataplan["Operator"] or "",
                "coin": dataplan["Coin"] or "",
                "price": dataplan["price"] or "",
            })
        response_data = {
            'headers': headers,
            'data': formatted_results
        }
        return JsonResponse(response_data, safe=False)
    
@method_decorator(csrf_exempt, name='dispatch')
class ExportDataSimcards(View):
    def get(self, request):
        search_query = request.GET.get('query', None)
        simcards = fetch_all_simcards(request.user.company, request.user, search_query)
        formatted_results = []
        # Encabezados traducidos
        headers = [
            _("Company"),
            _("Phone number"),
            _("Serial number"),
            _("Data plan"),
            _("Activate date"),
            _("Status")
        ]

        for simcard in simcards:
            formatted_results.append({
                "company": simcard["Company"] or "",
                "serial_number": simcard["serial_number"] or "",
                "phone_number": simcard["phone_number"] or "",
                "data_plan": simcard["data_plan"] or "",
                "is_active": simcard["is_active"] or False,
                "activate_date": simcard["activate_date"],
            })
        response_data = {
            'headers': headers,
            'data': formatted_results
        }
        return JsonResponse(response_data, safe=False)
    
@method_decorator(csrf_exempt, name='dispatch')
class ExportDataDevices(View):
    def get(self, request):
        search_query = request.GET.get('query', None)
        devices = ListDeviceByCompany(request.user.company_id, request.user.id, search_query)
        formatted_results = []
        # Encabezados traducidos
        headers = [
            _("Company"),
            _("IMEI"),
            _("Serial Number"),
            _("Device Type"),
            _("Simcard"),
            _("IP"),
            _("Create Date"),
            _("Status")
        ]

        for device in devices:
            formatted_results.append({
                "imei": device["imei"],
                "company": device["company"] or "",
                "ip": device["ip"] or "",
                "serial_number": device["serial_number"] or "",
                "simcard": device["simcard"] or "",
                "simcard_visible": device["simcard_visible"] or False,
                "is_active": device["is_active"] or False,
                "familymodel": device["familymodel"] or "",
                "create_date": device["create_date"],
            })
        response_data = {
            'headers': headers,
            'data': formatted_results
        }
        return JsonResponse(response_data, safe=False)
    
@method_decorator(csrf_exempt, name='dispatch')
class ExportDataVehicles(View):
    def get(self, request):
        search_query = request.GET.get('query', None)
        vehicles = ListVehicleByUserAndCompany(request.user.company_id, request.user.id, search_query)
        formatted_results = []
        # Encabezados traducidos
        headers = [
            _("Company"),
            _("Plate"),
            _("N° Interno"),
            _("Imei"),
            _("Asset type"),
            _("Installation Date"),
            _("Status")
        ]

        for vehicle in vehicles:
            formatted_results.append({
                "device": vehicle["device"],
                "company": vehicle["company"] or "",
                "license": vehicle["license"] or "",
                "vehicle_type": vehicle["vehicle_type"] or "",
                "n_interno": vehicle["n_interno"] or "",
                "is_active": vehicle["is_active"] or False,
                "installation_date": vehicle["installation_date"],
            })
        response_data = {
            'headers': headers,
            'data': formatted_results
        }

        return JsonResponse(response_data, safe=False)
    
@method_decorator(csrf_exempt, name='dispatch')
class ExportDataAssetsGroups(View):
    def get(self, request):
        search_query = request.GET.get('query', None)
        groupAssets = ListVehicleGroupsByCompany(request.user.company_id, search_query)
        formatted_results = []
        # Encabezados traducidos
        headers = [
            _("Name Group"),
            _("Content")
        ]

        for groupAsset in groupAssets:
            formatted_results.append({
                "name": groupAsset["name"] or "",
                "VehicleCount": groupAsset["VehicleCount"] or 0,
            })
        response_data = {
            'headers': headers,
            'data': formatted_results
        }

        return JsonResponse(response_data, safe=False)

