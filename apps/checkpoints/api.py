import datetime
import json
from datetime import datetime, timedelta

import pandas as pd
from django.db import connection
from django.db.models import Prefetch
from django.http import HttpResponse, JsonResponse

from apps.events.models import Event, EventFeature
from apps.realtime.models import Device


def vehicles_by_company(request, company_id):
    """
    Retorna una lista de vehículos pertenecientes a una compañía específica.

    Args:
        request (HttpRequest): La solicitud HTTP recibida.
        company_id (int): El ID de la compañía a la que pertenecen los vehículos.

    Returns:
        JsonResponse: Una respuesta JSON que contiene la lista de vehículos.
    """
    # Asumiendo que cada Device tiene un Vehicle asociado, y que la relación inversa es 'vehicle' en Device
    vehicles = (
        Device.objects.filter(company_id=company_id, visible=True)
        .prefetch_related("vehicle")
        .values("imei", "vehicle__license")
    )
    return JsonResponse(list(vehicles), safe=False)


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
        ) - timedelta(minutes=timezone_offset)
        fecha_final = datetime.strptime(
            request.POST.get("FechaFinal"), "%Y-%m-%dT%H:%M"
        ) - timedelta(minutes=timezone_offset)
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
