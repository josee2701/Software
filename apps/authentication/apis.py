from django.http import JsonResponse

from apps.realtime.models import Vehicle
from apps.whitelabel.models import Company, Process


def list_proces_by_company(request, company_id):
    """
    Lista todos los procesos por empresa.

    Parámetros:
    - request: La solicitud HTTP recibida.
    - company_id: El ID de la empresa para filtrar los procesos.

    Retorna:
    Un objeto JsonResponse que contiene una lista de procesos, donde cada proceso tiene los campos 'id' y 'name'.
    """
    process = Process.objects.filter(company_id=company_id).values(
        "id",
        "process_type",
    )
    return JsonResponse({"process": list(process)}, safe=False)


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
