import json

from django.db import connection
from django.http import JsonResponse
from rest_framework.decorators import api_view


def getmapscompany(request, company_id):
    # Reemplaza 'your_parameter' con el nombre real del parámetro que esperas en la URL.

    if company_id is None:
        return JsonResponse({"error": "Se requiere el ID de la compañía."}, status=400)

    try:
        company_id = int(company_id)
    except ValueError:
        return JsonResponse(
            {"error": "El ID de la compañía debe ser un número entero."}, status=400
        )

    with connection.cursor() as cursor:
        query = """
        SELECT DISTINCT
            COALESCE(MP.Name, 'OpenStreetMap') AS Name,
            Key_Map,
            MP.ID  -- Asegúrate de incluir esto si decides mantenerlo en ORDER BY
        FROM whitelabel_company CD
        LEFT JOIN whitelabel_company CF ON CD.id = CF.provider_id
        LEFT JOIN whitelabel_companytypemap CM ON CM.company_id = CASE
            WHEN CD.Id IS NULL THEN CF.Id
            ELSE CD.Id
        END
        LEFT JOIN whitelabel_maptype MP ON MP.ID = CM.map_type_id
        WHERE CF.id = %s OR CD.Id = %s
        ORDER BY MP.ID

        """
        cursor.execute(query, [company_id, company_id])
        result = cursor.fetchall()

    # Convertir los resultados en un formato JSON amigable.
    mapas = [
        {"nombre": name, "clave_mapa": key_map, "id": id}
        for name, key_map, id in result
    ]

    return JsonResponse(
        mapas, safe=False
    )  # 'safe=False' es necesario porque estamos devolviendo una lista, no un diccionario.


def get_last_avl_as_json(request, user_id):
    try:
        # Asegúrate de que user_id es un entero
        user_id = int(user_id)
        print(user_id)

        json_result = ""
        with connection.cursor() as cursor:
            # Ejecutamos el procedimiento almacenado pasando user_id
            cursor.execute("EXEC GetLastAvlAsJson @User_ID=%s", [user_id])

            rows = cursor.fetchall()  # Recuperamos todas las filas del resultado

            # Concatenamos cada parte del JSON en la columna específica
            for row in rows:
                json_result += row[0]  # Asumimos que el JSON está en la primera columna

        # Antes de intentar decodificar, verificamos que json_result no esté vacío
        if not json_result:
            return JsonResponse(
                {"error": "No se encontraron datos para el usuario especificado."},
                status=404,
            )

        # Convertimos la cadena concatenada a un objeto JSON
        json_data = json.loads(json_result)

        return JsonResponse(json_data, safe=False)
    except ValueError as e:
        # Este bloque manejará errores de conversión de user_id a entero
        return JsonResponse(
            {"error": f"El ID de usuario debe ser un número entero. {str(e)}"},
            status=400,
        )
    except json.JSONDecodeError as e:
        # Manejamos errores específicos de decodificación JSON
        return JsonResponse(
            {"error": f"Error al decodificar JSON: {str(e)}"}, status=500
        )
    except Exception as e:
        # Cualquier otro error no anticipado
        return JsonResponse({"error": str(e)}, status=500)


def get_alarms_user(request, user_id):
    try:
        user_id = int(user_id)  # Ensure user_id is an integer
        json_result = ""

        with connection.cursor() as cursor:
            cursor.execute("EXEC GetAlarmsUser @User_ID=%s", [user_id])
            rows = cursor.fetchall()  # Recuperamos todas las filas del resultado

            # Concatenamos cada parte del JSON en la columna específica
            for row in rows:
                json_result += row[0]  # Asumimos que el JSON está en la primera columna

        # Convertimos la cadena concatenada a un objeto JSON
        json_data = json.loads(json_result)

        return JsonResponse(json_data, safe=False)
    except ValueError:
        return JsonResponse(
            {"error": "El ID de usuario debe ser un número entero."}, status=400
        )
    except json.JSONDecodeError as e:
        return JsonResponse(
            {"error": f"Error al decodificar JSON: {str(e)}"}, status=500
        )
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@api_view(["POST"])
def vehicle_history(request):
    if request.method == "POST":
        try:
            # Extrae los parámetros del cuerpo de la solicitud
            data = request.data
            imei = data.get("Imei")
            start_date = data.get("FechaInicial")
            end_date = data.get("FechaFinal")
            company_id = data.get("Company_id")

            # Inicializa json_result como un string vacío
            json_result = ""

            # Ejecuta el procedimiento almacenado dentro del bloque with
            with connection.cursor() as cursor:
                cursor.execute(
                    "EXEC GetVehicleHistory @Imei=%s, @FechaInicial=%s, @FechaFinal=%s, @Company_id=%s",
                    [imei, start_date, end_date, company_id],
                )
                rows = cursor.fetchall()

                # Concatena cada parte del JSON
                if rows:
                    for row in rows:
                        json_result += row[0]
                else:
                    return JsonResponse(
                        {"error": "No se encontraron resultados."}, status=404
                    )

            # Convierte el string concatenado a un objeto JSON
            json_data = json.loads(json_result)

            return JsonResponse(json_data, safe=False)
        except ValueError as e:
            # Maneja específicamente los errores de valor
            return JsonResponse(
                {"error": "Uno o más parámetros son inválidos: " + str(e)}, status=400
            )
        except json.JSONDecodeError as e:
            # Maneja específicamente los errores de decodificación JSON
            return JsonResponse(
                {"error": "Error al decodificar JSON: " + str(e)}, status=500
            )
        except Exception as e:
            # Maneja otros errores generales
            return JsonResponse({"error": str(e)}, status=500)


@api_view(["GET"])
def get_device_commands(request):
    imei = request.query_params.get(
        "imei"
    )  # Obtiene el imei de los parámetros de la URL
    if not imei:
        return JsonResponse({"error": "IMEI es requerido."}, status=400)

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                C.id,
                C.command,
                C.name
            FROM
                realtime_commands AS C
                INNER JOIN realtime_familymodeluec AS FM ON C.model_id = FM.model_id
                INNER JOIN realtime_modeluec AS MUEC ON MUEC.id = FM.model_id
                INNER JOIN realtime_device AS D ON D.familymodel_id = MUEC.id
            WHERE
                D.imei = %s;
        """,
            [imei],
        )

        columns = [col[0] for col in cursor.description]
        result = [dict(zip(columns, row)) for row in cursor.fetchall()]

    return JsonResponse(result, safe=False)


@api_view(["POST"])
def insert_sending_command(request):
    # Obtiene los datos del cuerpo de la solicitud
    data = request.data
    imei = data.get("Imei")
    id_command = data.get("IdCommand")
    user_id = data.get("User_Id")

    # Verifica que los datos necesarios están presentes
    if imei is None or id_command is None or user_id is None:
        return JsonResponse(
            {"error": "IMEI, IdCommand y User_Id son requeridos."}, status=400
        )

    try:
        with connection.cursor() as cursor:
            # Ejecuta el procedimiento almacenado
            cursor.execute(
                "EXEC dbo.InsertSendingCommand @Imei=%s, @IdCommand=%s, @User_Id=%s",
                [imei, id_command, user_id],
            )

            # Si necesitas capturar algún valor de retorno del SP, ajusta esto según sea necesario
            return JsonResponse({"message": "Comando insertado exitosamente"})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@api_view(["POST"])
def update_or_insert_company_dashboard(request):
    try:
        data = request.data
        company_id = data.get("CompanyID")
        widgets_data = json.dumps(data.get("WidgetsData"))  # Convierte a string JSON
        layout = json.dumps(data.get("Layout"))  # Convierte a string JSON

        with connection.cursor() as cursor:
            cursor.execute(
                "EXEC dbo.UpdateOrInsertCompanyDashboard @CompanyID=%s, @WidgetsData=%s, @Layout=%s",
                [company_id, widgets_data, layout],
            )
        return JsonResponse(
            {"message": "Dashboard actualizado o insertado correctamente."}, safe=False
        )
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@api_view(["GET"])
def get_company_dashboard(request):
    company_id = request.query_params.get("CompanyID")
    if not company_id:
        return JsonResponse({"error": "CompanyID es requerido."}, status=400)

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """SELECT top 1 WidgetsData,Layout FROM whitelabel_company CD
                    LEFT JOIN whitelabel_company CF ON CD.id = CF.provider_id
                    LEFT JOIN CompanyDashboards CDA ON CDa.CompanyID = CASE
                                WHEN CD.Id IS NULL THEN CF.Id
                                ELSE CD.Id
                            END

                    WHERE CF.id = %s OR CD.Id = %s AND WidgetsData IS NOT NULL """,
                [company_id, company_id],
            )
            columns = [col[0] for col in cursor.description]
            result = [dict(zip(columns, row)) for row in cursor.fetchall()]
        return JsonResponse(result, safe=False)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@api_view(["GET"])
def update_events_alarm(request):
    user_id = request.query_params.get("user_id")
    event_id = request.query_params.get("alarm_id")

    try:
        with connection.cursor() as cursor:
            # Paso 1: Consultar el estado actual del registro
            cursor.execute(
                "SELECT 1 FROM events_alarm WHERE id = %s AND is_checked = 1",
                [event_id],
            )
            result = cursor.fetchone()

            if result:
                # El registro ya estaba marcado como chequeado
                message = "Event alarm was already checked."
            else:
                # Paso 2: El registro no estaba marcado, ejecutar el procedimiento almacenado para actualizar
                cursor.execute(
                    "EXEC UpdateEventsAlarm @user_id=%s, @id=%s", [user_id, event_id]
                )
                # Como la lógica ha cambiado para no esperar un retorno, asumimos que la actualización fue exitosa
                message = "Event alarm updated successfully."

        return JsonResponse({"message": message}, safe=False)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@api_view(["GET"])
def get_companies_user(request, user_id):
    try:
        user_id = int(user_id)  # Ensure user_id is an integer
        json_result = ""

        with connection.cursor() as cursor:
            cursor.execute("EXEC GetCompaniesUser @User_ID=%s", [user_id])
            rows = cursor.fetchall()  # Recuperamos todas las filas del resultado

            # Concatenamos cada parte del JSON en la columna específica
            for row in rows:
                json_result += row[0]  # Asumimos que el JSON está en la primera columna

        # Convertimos la cadena concatenada a un objeto JSON
        json_data = json.loads(json_result)

        return JsonResponse(json_data, safe=False)
    except ValueError:
        return JsonResponse(
            {"error": "El ID de usuario debe ser un número entero."}, status=400
        )
    except json.JSONDecodeError as e:
        return JsonResponse(
            {"error": f"Error al decodificar JSON: {str(e)}"}, status=500
        )
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@api_view(["POST"])
def insert_geozone(request):
    try:
        data = json.loads(request.body)
        name = data.get("name")
        description = data.get("description")
        shape_type = data.get("shape_type")
        type_event = data.get("type_event")
        polygon = data.get("polygon")
        radius = data.get("radius", None)
        latitude = data.get("latitude", None)
        longitude = data.get("longitude", None)
        company_id = data.get("company_id")
        created_by_id = data.get("created_by_id")
        modified_by_id = data.get("modified_by_id")
        color = data.get(
            "color", None
        )  # Asegúrate de obtener estos valores también si son necesarios
        color_edges = data.get("color_edges", None)

        with connection.cursor() as cursor:
            cursor.execute(
                """
                EXEC InsertRealtimeGeozone
                    @name=%s,
                    @description=%s,
                    @shape_type=%s,
                    @type_event=%s,
                    @polygon=%s,
                    @radius=%s,
                    @latitude=%s,
                    @longitude=%s,
                    @company_id=%s,
                    @created_by_id=%s,
                    @modified_by_id=%s,
                    @color=%s,
                    @color_edges=%s
            """,
                [
                    name,
                    description,
                    shape_type,
                    type_event,
                    polygon,
                    radius,
                    latitude,
                    longitude,
                    company_id,
                    created_by_id,
                    modified_by_id,
                    color,
                    color_edges,
                ],
            )

            message = "Geozone successfully saved"
            return JsonResponse({"message": message}, safe=False)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@api_view(["GET"])
def get_geozone_company(request, company_id):
    try:
        company_id = int(company_id)  # Ensure user_id is an integer
        json_result = ""

        with connection.cursor() as cursor:
            cursor.execute(
                "EXEC GetRealtimeGeozonesByCompanyId @CompanyId=%s", [company_id]
            )
            rows = cursor.fetchall()  # Recuperamos todas las filas del resultado

            # Concatenamos cada parte del JSON en la columna específica
            for row in rows:
                json_result += (
                    row[0].replace('"[[', "[[ ").replace(']]"', " ]]")
                )  # Asumimos que el JSON está en la primera columna
        # json_result = replace(json_result, "[", "},{")
        print(json_result)
        # Convertimos la cadena concatenada a un objeto JSON
        json_data = json.loads(json_result)

        return JsonResponse(json_data, safe=False)
    except ValueError as e:
        return JsonResponse(
            {"error": f"Error al decodificar JSON: {str(e)}"}, status=500
        )
    except json.JSONDecodeError as e:
        return JsonResponse(
            {"error": f"Error al decodificar JSON: {str(e)}"}, status=500
        )
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@api_view(["GET"])
def get_vehicle_monitoring(request, user_id):
    try:
        # Asegúrate de que user_id es un entero
        user_id = int(user_id)
        print(user_id)

        json_result = ""
        with connection.cursor() as cursor:
            # Ejecutamos el procedimiento almacenado pasando user_id
            cursor.execute("EXEC GetVehicleMonitoringData @User_ID=%s", [user_id])

            rows = cursor.fetchall()  # Recuperamos todas las filas del resultado

            # Concatenamos cada parte del JSON en la columna específica
            for row in rows:
                json_result += row[0]  # Asumimos que el JSON está en la primera columna

        # Antes de intentar decodificar, verificamos que json_result no esté vacío
        if not json_result:
            return JsonResponse(
                {"error": "No se encontraron datos para el usuario especificado."},
                status=404,
            )

        # Convertimos la cadena concatenada a un objeto JSON
        json_data = json.loads(json_result)

        return JsonResponse(json_data, safe=False)
    except ValueError as e:
        # Este bloque manejará errores de conversión de user_id a entero
        return JsonResponse(
            {"error": f"El ID de usuario debe ser un número entero. {str(e)}"},
            status=400,
        )
    except json.JSONDecodeError as e:
        # Manejamos errores específicos de decodificación JSON
        return JsonResponse(
            {"error": f"Error al decodificar JSON: {str(e)}"}, status=500
        )
    except Exception as e:
        # Cualquier otro error no anticipado
        return JsonResponse({"error": str(e)}, status=500)
