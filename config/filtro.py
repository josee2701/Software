from django.db.models import Q
from django.http import (Http404, HttpResponse, HttpResponseRedirect,
                         JsonResponse)

from apps.realtime.models import (DataPlan, Device, FamilyModelUEC,
                                  Manufacture, MobileOperator, SimCard,
                                  Vehicle, VehicleGroup)
from apps.whitelabel.models import Company, Theme


class General_Filters:
    @staticmethod
    def autentication_user(user):
        """
        Valida si el usuario actual está autenticado. Si el usuario no está autenticado,
        lanza un error Http404, evitando que se acceda a la funcionalidad o recurso protegido.
        """
        if not user.is_authenticated:
            raise Http404("User not authenticated")

    @staticmethod
    def get_filtered_companies(user):
        """
        Obtiene las compañías según la lógica de filtrado proporcionada, asumiendo
        que el usuario ya está autenticado.
        """
        # Primero, verificamos si el usuario está autenticado
        General_Filters.autentication_user(user)

        # Procedemos con la lógica para obtener las compañías
        user_company_id = user.company_id

        # Caso 1: Usuario con company_id = 1, obtener todas las compañías
        if user_company_id == 1:
            companies = Company.objects.filter(visible=True)

        # Caso 2: Si el usuario tiene compañías para monitorear, mostrar solo esas
        elif user.companies_to_monitor.exists():
            companies = user.companies_to_monitor.filter(visible=True, actived=True)

        # Caso 3: Obtener la empresa principal y todas las empresas donde es proveedor
        else:
            companies = Company.objects.filter(
                provider_id=user.company_id, visible=True
            )

        return companies

    @staticmethod
    def get_filtered_data(model, user, company_field="company_id"):
        """
        Obtiene los registros del modelo especificado según la lógica de filtrado proporcionada,
        considerando si el modelo tiene o no el campo 'visible'.

        Args:
            model: El modelo de Django sobre el cual filtrar (ej. DataPlan, Sending_Commands).
            user: El usuario actualmente autenticado (request.user).
            company_field: El nombre del campo en el modelo que referencia a la compañía (default 'company_id').

        Returns:
            Un QuerySet del modelo filtrado según las reglas de negocio.
        """
        # Verificación de autenticación del usuario
        General_Filters.autentication_user(user)

        # Inicialización del QuerySet basado en la presencia del campo 'visible'
        if hasattr(model, "visible"):
            base_query = model.objects.filter(visible=True)
        else:
            base_query = model.objects.all()

        user_company_id = getattr(user, company_field, None)

        if user_company_id == 1:
            # Para admin, retornamos todos los registros según la base_query
            filtered_data = base_query
        else:
            # Filtramos por compañía y, si aplica, por visibilidad
            filtered_data = base_query.filter(**{company_field: user_company_id})

            # Comprobamos compañías proveedoras si el modelo relaciona compañías
            if hasattr(model, "company"):
                companys_provider = Company.objects.filter(
                    provider_id=user_company_id, visible=True, actived=True
                )
                if companys_provider.exists():
                    # Extendemos el QuerySet para incluir registros de compañías proveedoras
                    filtered_data = filtered_data | base_query.filter(
                        company__in=companys_provider
                    )

        return filtered_data


def get_companies_and_vehicle(self):
    # Asegúrate de que el usuario esté autenticado antes de acceder a company_id
    if self.request.user.is_authenticated:
        company_id = self.request.user.company_id
        provider_company_ids = Company.objects.filter(
            provider_id=company_id
        ).values_list("id", flat=True)
        # Filtra las empresas disponibles para el usuario
        companies = Company.objects.filter(
            Q(id=company_id) | Q(provider_id=company_id), visible=True
        )
        # Llena las opciones del formulario con las empresas disponibles
        vehicle = Vehicle.objects.filter(
            Q(company_id=company_id, visible=True)
            | Q(company_id__in=list(provider_company_ids), visible=True)
        ).order_by("company")
        return companies, vehicle
    else:
        # En lugar de return redirect('login'), puedes generar una redirección HTTP
        raise Http404("User not authenticated")
