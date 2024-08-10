from django.db import connection  # Importar connection de django.db
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.http import require_GET


@method_decorator(require_GET, name="dispatch")
class MapsKeyView(View):
    def get_maps_key(self, company_id):
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT distinct case when MP.Name is null then 'OpenStreetMap' end Name, Key_Map
                    FROM whitelabel_company CD
                    LEFT JOIN whitelabel_company CF ON CD.id=CF.provider_id
                    LEFT JOIN whitelabel_companytypemap CM ON CM.company_id=CASE WHEN CF.id IS NULL THEN CD.Id ELSE NULL END
                    LEFT JOIN whitelabel_maptype MP ON MP.ID=CM.company_id
                    WHERE (CF.id=%s OR CD.Id=%s)
                """,
                    [company_id, company_id],
                )

                rows = cursor.fetchall()

            # Preparar respuesta
            data = [{"name": row[0], "key_map": row[1]} for row in rows] if rows else []

            return data
        except Exception as e:
            return str(e)

    def get(self, request):
        try:
            company_id = request.GET.get("company_id")
            if company_id is None:
                return JsonResponse(
                    {
                        "error": "Se requiere el ID de la compañía en los parámetros de la URL."
                    },
                    status=400,
                )

            # Obtener las claves de mapa
            map_keys = self.get_maps_key(company_id)

            # Verificar si se recibió algún error en forma de cadena
            if isinstance(map_keys, str):
                return JsonResponse({"error": map_keys}, status=500)

            # Devolver las claves de mapa en la respuesta
            return JsonResponse({"data": map_keys})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
