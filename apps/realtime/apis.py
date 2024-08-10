from django.contrib.auth.decorators import login_required
from django.db import DatabaseError, connection
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views import View

from .models import DataPlan, Device, FamilyModelUEC, SimCard, Vehicle


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
    data_plans = DataPlan.objects.filter(company_id=company_id).values(
        "id", "name", "operator"
    )
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
