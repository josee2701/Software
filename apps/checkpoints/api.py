import datetime
import json
from datetime import datetime, timedelta

import pandas as pd
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db import connection
from django.db.models import Prefetch
from django.http import HttpResponse, JsonResponse
from django.utils import translation
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from apps.authentication.models import User
from apps.events.models import Event, EventFeature
from apps.realtime.apis import sort_key
from apps.realtime.models import Device

from .sql import (fetch_all_confidatasem, get_drivers_list,
                  getCompanyScoresByCompanyAndUser)


def vehicles_by_company(request, company_id):
    """
    Retorna una lista de vehículos pertenecientes a una compañía específica.

    Args:
        request (HttpRequest): La solicitud HTTP recibida.
        company_id (int): El ID de la compañía a la que pertenecen los vehículos.

    Returns:
        JsonResponse: Una respuesta JSON que contiene la lista de vehículos.
    """
    # Asumiendo que cada Device tiene un Vehicle asociado, y que la relación inversa es 'vehicle'
    # en Device
    vehicles = (
        Device.objects.filter(company_id=company_id, visible=True)
        .prefetch_related("vehicle")
        .values("imei", "vehicle__license")
    )

    # Filtra las entradas para asegurarte de que tanto 'imei' como 'vehicle__license' estén
    # presentes y no sean None o estén vacíos
    vehicles_list = [
        vehicle
        for vehicle in vehicles
        if vehicle["imei"] and vehicle["vehicle__license"]
    ]

    return JsonResponse(vehicles_list, safe=False)


def events_by_company(request, company_id):
    # Prefetch de eventos y sus características visibles para la compañía dada
    events = Event.objects.prefetch_related(
        Prefetch(
            "eventfeature_set",
            queryset=EventFeature.objects.filter(company=company_id, visible=True),
            to_attr="visible_features",
        )
    )
    # Lista para almacenar los eventos actualizados
    updated_events = []
    # Diccionario para evitar procesamiento duplicado de números de evento
    event_features_map = {}
    for event in events:
        # Utilizar las características prefetchadas
        event_features = event.visible_features
        if event_features:
            # Concatenar los nombres de las características de evento
            event_name = " | ".join(feature.alias for feature in event_features)
            event.name = event_name
        # Agregar el evento a la lista con información actualizada
        updated_events.append(f"{event.pk} - {event.number} Event: {event.name}")
    # Ordenar eventos por el nombre de evento de forma alfabética
    updated_events.sort(key=lambda x: x.split("Event: ")[-1])

    return JsonResponse(updated_events, safe=False)


def events_person_by_company(request, company_id):
    # Prefetch de EventFeatures específicas de la compañía para todos los eventos
    events = Event.objects.prefetch_related(
        Prefetch(
            "eventfeature_set",
            queryset=EventFeature.objects.filter(company_id=company_id, visible=True),
            to_attr="visible_features",
        )
    )

    # Generar la lista de eventos actualizados con una comprensión de lista
    updated_events = [
        f"{event.pk} - {event.number} Event: {' | '.join(feature.alias for feature in event.visible_features)}"
        if event.visible_features
        else f"{event.pk} - {event.number} Event: {event.name}"
        for event in events
    ]

    # Ordenar la lista de eventos actualizada por el nombre del evento en orden alfabético
    updated_events.sort(key=lambda x: x.split("Event: ")[-1])

    return JsonResponse(updated_events, safe=False)


def export_report(request):
    """
    Exporta un informe en el formato especificado a partir de los datos recibidos en una solicitud
    POST.

    Parámetros:
    - request: La solicitud HTTP recibida.

    Retorna:
    - Si el método de la solicitud no es POST, retorna una respuesta HTTP con el mensaje 'Método no
    soportado' y estado 405.
    - Si ocurre un error en los parámetros de entrada, retorna una respuesta JSON con el mensaje de
    error y estado 400.
    - Si ocurre un error interno del servidor, retorna una respuesta JSON con el mensaje de error y
    estado 500.
    - Si no se encuentran resultados, retorna una respuesta JSON con el mensaje de error 'No se
    encontraron resultados' y estado 404.
    - Si el formato es 'xlsx', retorna un archivo Excel con los datos en el cuerpo de la respuesta.
    - Si el formato es 'csv', retorna un archivo CSV con los datos en el cuerpo de la respuesta.
    - Si el formato es 'pdf', retorna un archivo PDF con los datos en el cuerpo de la respuesta.
    """
    if request.method != "POST":
        return HttpResponse("Método no soportado.", status=405)

    print("Datos recibidos en POST:", request.POST)  # Depuración

    format = request.POST.get("format")
    try:
        company_id = request.POST.get("Company_id")
        imei = request.POST.get("Imei")
        timezone_offset = int(request.POST.get("timezone_offset", 0))

        # Ajustar la fecha inicial y final correctamente
        fecha_inicial = datetime.strptime(
            request.POST.get("FechaInicial"), "%Y-%m-%dT%H:%M"
        ) + timedelta(minutes=timezone_offset)
        fecha_final = datetime.strptime(
            request.POST.get("FechaFinal"), "%Y-%m-%dT%H:%M"
        ) + timedelta(minutes=timezone_offset)
        fecha_inicial_str = fecha_inicial.strftime("%Y-%m-%d %H:%M:%S")
        fecha_final_str = fecha_final.strftime("%Y-%m-%d %H:%M:%S")

        json_result = ""

        with connection.cursor() as cursor:
            cursor.execute(
                "EXEC [dbo].[GetAVLData] @Company_ID=%s, @IMEI=%s, @dFIni=%s, @dFFin=%s",
                [company_id, imei, fecha_inicial_str, fecha_final_str],
            )
            rows = cursor.fetchall()
            if not rows:
                return JsonResponse(
                    {"error": "No se encontraron resultados."}, status=404
                )

            for row in rows:
                json_result += row[0]

        json_data = json.loads(json_result)

        # Ajustar las fechas en json_data a la zona horaria del usuario
        for item in json_data:
            for key in ["server_date", "signal_date"]:
                if key in item and item[key]:
                    utc_date = datetime.strptime(item[key], "%Y-%m-%dT%H:%M:%S")
                    local_date = utc_date - timedelta(minutes=timezone_offset)
                    item[key] = local_date.strftime("%Y-%m-%d %H:%M:%S")
        # connectionpostgres = connect_db()
        # if connectionpostgres is None:
        #     return JsonResponse(
        #         {"error": "Failed to connect to the PostgreSQL database."},
        #         status=500,
        #     )
        # try:
        #     with connectionpostgres.cursor() as geo_cursor:
        #         for item in json_data:
        #             latitude = str(item.get("latitude"))
        #             longitude = str(item.get("longitude"))
        #             if latitude and longitude:
        #                 start_time = time.time()
        #                 geo_cursor.execute(
        #                     "SELECT public.rev_geocode_gpsmobile(%s, %s)",
        #                     [longitude, latitude],
        #                 )
        #                 location = geo_cursor.fetchone()[0]
        #                 end_time = time.time()
        #                 execution_time = end_time - start_time
        #                 # Añadir el campo "location" al diccionario
        #                 item["location"] = location
        # finally:
        #     connectionpostgres.close()

        df = pd.DataFrame(json_data)

        if format == "xlsx":
            response = HttpResponse(
                content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            response["Content-Disposition"] = 'attachment; filename="report.xlsx"'
            df.to_excel(response, index=False, engine="openpyxl")
            response["Content-Length"] = response.tell()
            return response
        elif format == "csv":
            response = HttpResponse(content_type="text/csv")
            response["Content-Disposition"] = 'attachment; filename="report.csv"'
            df.to_csv(response, index=False, encoding="utf-8-sig")
            response["Content-Length"] = response.tell()
            return response
        elif format == "pdf":
            from io import BytesIO

            from reportlab.pdfgen import canvas

            buffer = BytesIO()
            p = canvas.Canvas(buffer)

            # Ejemplo: añadir contenido al PDF
            p.drawString(100, 100, "Hello World")
            p.showPage()
            p.save()

            buffer.seek(0)
            response = HttpResponse(buffer, content_type="application/pdf")
            response["Content-Disposition"] = 'attachment; filename="report.pdf"'
            response["Content-Length"] = buffer.tell()
            return response

    except ValueError as e:
        return JsonResponse(
            {"error": "Error en los parámetros de entrada: " + str(e)}, status=400
        )
    except Exception as e:
        return JsonResponse(
            {"error": "Error interno del servidor: " + str(e)}, status=500
        )


@method_decorator(csrf_exempt, name="dispatch")
class SearchDrivers(View):
    def get(self, request):
        company = request.user.company_id
        user_id = request.user.id
        session_filters = request.session.get(f'filters_sorted_driver_{user_id}', {})
        search_query = request.GET.get('query', None)
        page_number = request.GET.get('page', session_filters.get('page', [1]))[0]

        if not company or not user_id:
            return JsonResponse({"error": "Faltan parámetros"}, status=400)
        paginate_by = request.POST.get('paginate_by', None)  # Obtener paginate_by de los parámetros POST
        if paginate_by is None:
            session_filters = request.session.get(
                f"filters_sorted_driver_{user_id}", {}
            )
            paginate_by = session_filters.get("paginate_by", 15)
        # Convertir a entero si es una lista
        try:
            paginate_by = int(
                paginate_by[0]
            )  # Convertir el primer elemento de la lista a entero
        except (TypeError, ValueError):
            paginate_by = int(paginate_by) if paginate_by else 15
        drivers = get_drivers_list(company, user_id, search_query)
        order_by = session_filters.get('order_by', [None])[0]
        direction = session_filters.get('direction', [None])[0]
        # Obtener la función de clave para ordenar
        key_function = sort_key(order_by)
        # Determinar si es orden descendente
        reverse = direction == 'desc'
        try:
            drivers = sorted(drivers, key=key_function, reverse=reverse)
        except KeyError:
            # Ordenamiento por defecto si la clave no existe
            drivers = sorted(drivers, key=lambda x: x['company'].lower(), reverse=reverse)
        page_size = paginate_by  # Número de elementos por página.
        paginator = Paginator(drivers, page_size)
        try:
            page = paginator.page(page_number)
        except PageNotAnInteger:
            page = paginator.page(1)
        except EmptyPage:
            page = paginator.page(paginator.num_pages)
        current_language = translation.get_language()

        formatted_results = []
        for driver in page.object_list:
            date_joined = driver["date_joined"]
            month_name = date_joined.strftime("%B")
            month_name = _(month_name)
            if date_joined:
                if current_language == "es":
                    # Formato en español
                    formatted_date = date_joined.strftime(
                        f'%d {_("de")} {month_name} {_("de")} %Y'
                    )
                else:
                    # Formato en inglés u otros idiomas
                    formatted_date = date_joined.strftime("%B %d, %Y")
            formatted_results.append(
                {
                    "id": driver["id"],
                    "company": driver["company"] or "",
                    "first_name": driver["first_name"] or "",
                    "last_name": driver["last_name"] or "",
                    "personal_identification_number": driver[
                        "personal_identification_number"
                    ]
                    or "",
                    "phone_number": driver["phone_number"] or "",
                    "address": driver["address"] or "",
                    "is_active": driver["is_active"] or False,
                    "date_joined": formatted_date,
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
class SearchScores(View):
    def get(self, request):
        company = request.user.company_id
        user_id = request.user.id
        session_filters = request.session.get(f'filters_sorted_scoredriver_{user_id}', {})
        search_query = request.GET.get('query', None)
        page_number = request.GET.get('page', session_filters.get('page', [1]))[0]

        if not company or not user_id:
            return JsonResponse({"error": "Faltan parámetros"}, status=400)
        paginate_by = request.POST.get('paginate_by', None)  # Obtener paginate_by de los parámetros GET
        if paginate_by is None:
            paginate_by = session_filters.get('paginate_by', 15)
        # Convertir a entero si es una lista
        try:
            paginate_by = int(
                paginate_by[0]
            )  # Convertir el primer elemento de la lista a entero
        except (TypeError, ValueError):
            paginate_by = int(paginate_by) if paginate_by else 15
        scores = getCompanyScoresByCompanyAndUser(company, user_id, search_query)
        order_by = session_filters.get('order_by', [None])[0]
        direction = session_filters.get('direction', [None])[0]
        # Obtener la función de clave para ordenar
        key_function = sort_key(order_by)
        # Determinar si es orden descendente
        reverse = direction == 'desc'
        try:
            scores = sorted(scores, key=key_function, reverse=reverse)
        except KeyError:
            # Ordenamiento por defecto si la clave no existe
            scores = sorted(scores, key=lambda x: x['company'].lower(), reverse=reverse)
        page_size = paginate_by  # Número de elementos por página.
        paginator = Paginator(scores, page_size)
        try:
            page = paginator.page(page_number)
        except PageNotAnInteger:
            page = paginator.page(1)
        except EmptyPage:
            page = paginator.page(paginator.num_pages)

        formatted_results = []
        for score in page.object_list:
            formatted_results.append(
                {
                    "company_id": score["company_id"],
                    "company": score["company"] or 0,
                    "min_score": score["min_score"] or 0,
                    "max_score": score["max_score"] or 0,
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
class ExportDataScoreDriver(View):
    def get(self, request):
        company = request.user.company_id
        user_id = request.user.id
        search_query = request.GET.get('query', None)
        scores = getCompanyScoresByCompanyAndUser(company, user_id, search_query)
        formatted_results = []
        # Encabezados traducidos
        headers = [
            _("company"),
            _("Minimum score"),
            _("Maximum score")
        ]

        for score in scores:
            formatted_results.append({
                "company": score['company'] or 0,
                "min_score": score['min_score'] or 0,
                "max_score": score['max_score'] or 0,
            })
        response_data = {
            'headers': headers,
            'data': formatted_results
        }
        return JsonResponse(response_data, safe=False)
    
@method_decorator(csrf_exempt, name='dispatch')
class ExportDataDriver(View):
    def get(self, request):
        company = request.user.company_id
        user_id = request.user.id
        search_query = request.GET.get('query', None)
        drivers = get_drivers_list(company, user_id, search_query)
        formatted_results = []
        # Encabezados traducidos
        headers = [
            _("Personal ID"),
            _("Company"),
            _("First name"),
            _("Last name"),
            _("Mobile numbere"),
            _("Date joined"),
            _("Status"),
            _("Address")
        ]

        for driver in drivers:
            formatted_results.append({
                "company": driver['company'] or "",
                "first_name": driver['first_name'] or "",
                "last_name": driver['last_name'] or "",
                "personal_identification_number": driver['personal_identification_number'] or "",
                "phone_number": driver['phone_number'] or "",
                "address": driver['address'] or "",
                "is_active": driver['is_active'] or False,
                "date_joined": driver['date_joined'] or "",
            })
        response_data = {
            'headers': headers,
            'data': formatted_results
        }
        return JsonResponse(response_data, safe=False)
    
@method_decorator(csrf_exempt, name="dispatch")
class SearchDataSem(View):
    """
    Vista para buscar y paginar datos SEM (Search Engine Marketing) según los filtros y parámetros proporcionados.

    Métodos:
        get: Maneja solicitudes GET para buscar, ordenar y paginar los datos SEM.
        get_page_number: Obtiene el número de página actual de la solicitud o de los filtros de sesión.
        get_paginate_by: Obtiene el número de elementos por página de la solicitud o de los filtros de sesión.
        sort_datasem: Ordena los datos SEM según los filtros de sesión.
        paginate_datasem: Pagina los datos SEM según el tamaño de página y el número de página proporcionados.
        format_results: Formatea los resultados de la página actual para la respuesta JSON.
        construct_response: Construye la respuesta JSON con los resultados formateados y la información de paginación.
    """

    def get(self, request):
        """
        Maneja solicitudes GET para buscar, ordenar y paginar los datos SEM.

        Args:
            request (HttpRequest): La solicitud HTTP.

        Returns:
            JsonResponse: La respuesta JSON con los datos buscados, ordenados y paginados.
        """
        company = request.user.company_id
        user_id = request.user.id
        session_filters = request.session.get(f'filters_sorted_confidatasem_{user_id}', {})
        search_query = request.GET.get("query", None)
        page_number = self.get_page_number(request, session_filters)
        paginate_by = self.get_paginate_by(request, session_filters)

        if not company or not user_id:
            return JsonResponse({"error": "Faltan parámetros"}, status=400)

        datasem = fetch_all_confidatasem(request.user.company, request.user, search_query)
        datasem = self.sort_datasem(datasem, session_filters)
        page = self.paginate_datasem(datasem, paginate_by, page_number)
        formatted_results = self.format_results(page)

        response_data = self.construct_response(formatted_results, page, request)
        return JsonResponse(response_data, safe=False)

    def get_page_number(self, request, session_filters):
        """
        Obtiene el número de página actual de la solicitud o de los filtros de sesión.

        Args:
            request (HttpRequest): La solicitud HTTP.
            session_filters (dict): Los filtros guardados en la sesión del usuario.

        Returns:
            int: El número de página actual.
        """
        return request.GET.get('page', session_filters.get('page', [1]))[0]

    def get_paginate_by(self, request, session_filters):
        """
        Obtiene el número de elementos por página de la solicitud o de los filtros de sesión.

        Args:
            request (HttpRequest): La solicitud HTTP.
            session_filters (dict): Los filtros guardados en la sesión del usuario.

        Returns:
            int: El número de elementos por página.
        """
        paginate_by = request.POST.get("paginate_by", None)
        if paginate_by is None:
            paginate_by = session_filters.get("paginate_by", 15)
        try:
            paginate_by = int(paginate_by[0])
        except (TypeError, ValueError):
            paginate_by = int(paginate_by) if paginate_by else 15
        return paginate_by

    def sort_datasem(self, datasem, session_filters):
        """
        Ordena los datos SEM según los filtros de sesión.

        Args:
            datasem (list): La lista de datos SEM a ordenar.
            session_filters (dict): Los filtros guardados en la sesión del usuario.

        Returns:
            list: La lista de datos SEM ordenada.
        """
        order_by = session_filters.get('order_by', [None])[0]
        direction = session_filters.get('direction', [None])[0]
        key_function = sort_key(order_by)
        reverse = direction == 'desc'
        try:
            return sorted(datasem, key=key_function, reverse=reverse)
        except KeyError:
            return sorted(datasem, key=lambda x: x['company_name'].lower(), reverse=reverse)

    def paginate_datasem(self, datasem, page_size, page_number):
        """
        Pagina los datos SEM según el tamaño de página y el número de página proporcionados.

        Args:
            datasem (list): La lista de datos SEM a paginar.
            page_size (int): El número de elementos por página.
            page_number (int): El número de la página actual.

        Returns:
            Page: Un objeto de página con los elementos de la página actual.
        """
        paginator = Paginator(datasem, page_size)
        try:
            return paginator.page(page_number)
        except PageNotAnInteger:
            return paginator.page(1)
        except EmptyPage:
            return paginator.page(paginator.num_pages)

    def format_results(self, page):
        """
        Formatea los resultados de la página actual para la respuesta JSON.

        Args:
            page (Page): Un objeto de página con los elementos de la página actual.

        Returns:
            list: Una lista de diccionarios con los resultados formateados.
        """
        formatted_results = []
        for datasem in page.object_list:
            formatted_results.append(
                {
                    "id": datasem["id"],
                    "company_name": datasem["company_name"] or "",
                    "full_name": datasem["full_name"] or "",
                    "workspace": datasem["workspace"] or "",
                    "name": datasem["name"] or "",
                    "report": datasem["report"] or "",
                    "price": datasem["price"],
                }
            )
        return formatted_results

    def construct_response(self, formatted_results, page, request):
        """
        Construye la respuesta JSON con los resultados formateados y la información de paginación.

        Args:
            formatted_results (list): Una lista de diccionarios con los resultados formateados.
            page (Page): Un objeto de página con los elementos de la página actual.
            request (HttpRequest): La solicitud HTTP.

        Returns:
            dict: Un diccionario con los resultados formateados y la información de paginación.
        """
        return {
            "results": formatted_results,
            "page": {
                "has_next": page.has_next(),
                "has_previous": page.has_previous(),
                "number": page.number,
                "num_pages": page.paginator.num_pages,
                "start_index": page.start_index(),
                "end_index": page.end_index(),
                "total_items": page.paginator.count,
            },
            "query_string": request.GET.urlencode(),
        }
        
        
def user_by_company(request,company_id):
    try:
        user = User.objects.filter(company_id=company_id)
        # Retornar los usuarios como JsonResponse
        return JsonResponse({"user": list(user.values())}, safe=False)
    except Exception as e:
        print(f'Error al obtener la lista de usuarios: {e}')
        return JsonResponse({"error": "No se pudo obtener la lista de usuarios"}, status=500)
