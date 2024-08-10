import psycopg2
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.http import require_GET

# Configuración de la base de datos
database_config = {
    "dbname": "dbpostgis",
    "user": "azadminpostgres",
    "password": "NhK%wAh#nT9c",
    "host": "postgresosm.postgres.database.azure.com",
    "port": 5432,
    "sslmode": "require",
}


# Clase para la vista del endpoint que obtiene la dirección
@method_decorator(require_GET, name="dispatch")
class ObtenerDireccionView(View):
    def obtener_direccion(self, longitude, latitude):
        try:
            # Conexión a la base de datos
            conn = psycopg2.connect(**database_config)
            cursor = conn.cursor()

            # Consulta a la base de datos
            # Consulta a la base de datos
            query = "SELECT public.rev_geocode_azsmart(%s, %s)"
            cursor.execute(query, (str(longitude), str(latitude)))

            resultado = cursor.fetchone()

            # Cerrar conexión
            cursor.close()
            conn.close()

            # Devolver el resultado
            return resultado[0] if resultado else "Ubicación no encontrada"
        except Exception as e:
            return str(e)

    def get(self, request):
        try:
            # Obtener la latitud y longitud de los parámetros de la solicitud
            latitud = request.GET.get("latitud")
            longitud = request.GET.get("longitud")

            if latitud is None or longitud is None:
                return JsonResponse(
                    {
                        "error": "Se requieren latitud y longitud en los parámetros de la URL."
                    },
                    status=400,
                )

            # Obtener la dirección
            direccion = self.obtener_direccion(latitud, longitud)

            # Devolver la dirección en la respuesta
            return JsonResponse({"direccion": direccion})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
