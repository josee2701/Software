from django.db.models import Q
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.realtime.models import AVLData
from apps.realtime.serializer import (
    AVLDataSerializer,  # Necesitas crear este serializer
)


class ReportDataAPIView(APIView):
    def get(self, request):
        # Recoge los parámetros de la solicitud GET
        company_id = request.query_params.get("company")
        # vehicle_id = request.query_params.get('vehicle')
        event_id = request.query_params.get("event")
        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")

        # Construye el queryset basado en los parámetros recibidos
        queryset = AVLData.objects.all()
        if company_id:
            queryset = queryset.filter(company_id=company_id)
        # if vehicle_id:
        #     queryset = queryset.filter(vehicle_id=vehicle_id)
        # if event_id:
        #     queryset = queryset.filter(event_id=event_id)
        if start_date and end_date:
            queryset = queryset.filter(date__range=[start_date, end_date])

        # Serializa los datos
        serializer = AVLDataSerializer(queryset, many=True)
        return Response(serializer.data)
