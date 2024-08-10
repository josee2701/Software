import datetime
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.translation import gettext as _

from .sql import fetch_all_event, fetch_all_event_personalized
from apps.realtime.apis import extract_number, sort_key


@method_decorator(csrf_exempt, name="dispatch")
class SearchEventPredefined(View):
    def get(self, request):
        company = request.user.company_id
        user_id = request.user.id
        session_filters = request.session.get(f'filters_sorted_eventpredefined_{user_id}', {})
        search_query = request.GET.get("query", None)
        page_number = request.GET.get('page', session_filters.get('page', [1]))[0]
        paginate_by = request.POST.get(
            "paginate_by", None
        )  # Obtener paginate_by de los parámetros POST
        if paginate_by is None:
            session_filters = request.session.get(
                f"filters_sorted_eventpredefined_{user_id}", {}
            )
            paginate_by = session_filters.get("paginate_by", 20)
        # Convertir a entero si es una lista
        try:
            paginate_by = int(
                paginate_by[0]
            )  # Convertir el primer elemento de la lista a entero
        except (TypeError, ValueError):
            paginate_by = int(paginate_by) if paginate_by else 20
        if not company or not user_id:
            return JsonResponse({"error": "Faltan parámetros"}, status=400)
        event_predefined = fetch_all_event(search_query)
        order_by = session_filters.get('order_by', [None])[0]
        direction = session_filters.get('direction', [None])[0]
        page_size = paginate_by # Número de elementos por página.
        # Obtener la función de clave para ordenar
        key_function = sort_key(order_by)
        # Determinar si es orden descendente
        reverse = direction == 'desc'
        try:
            event_predefined = sorted(event_predefined, key=key_function, reverse=reverse)
        except KeyError:
            # Ordenamiento por defecto si la clave no existe
            event_predefined = sorted(event_predefined, key=lambda x: x['number'].lower(), reverse=reverse)
        page_size = paginate_by  # Número de elementos por página.
        paginator = Paginator(event_predefined, page_size)
        try:
            page = paginator.page(page_number)
        except PageNotAnInteger:
            page = paginator.page(1)
        except EmptyPage:
            page = paginator.page(paginator.num_pages)

        formatted_results = []
        for event in page.object_list:
            formatted_results.append(
                {
                    "id": event["id"],
                    "name": event["name"] or "",
                    "number": event["number"] or 0,
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
class SearchEventUser(View):
    def get(self, request):
        company = request.user.company_id
        user_id = request.user.id
        session_filters = request.session.get(f'filters_sorted_eventuser_{user_id}', {})
        search_query = request.GET.get("query", None)
        page_number = request.GET.get('page', session_filters.get('page', [1]))[0]
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
        if not company or not user_id:
            return JsonResponse({"error": "Faltan parámetros"}, status=400)
        order_by = session_filters.get('order_by', [None])[0]
        direction = session_filters.get('direction', [None])[0]
        events_user = fetch_all_event_personalized(
            request.user.company, user_id, search_query
        )
        def sort_key(x):
            value = x.get(order_by)
            if value is None or value == "":
                return (4, "")  # Prioridad 4 para valores nulos o vacíos
            if isinstance(value, str):
                # Verificar si comienza con números, letras o caracteres especiales
                if value[0].isdigit():
                    return (2, extract_number(value))  # Prioridad 1 para números
                elif value[0].isalpha():
                    return (1, value.lower())  # Prioridad 2 para letras
                else:
                    return (3, value.lower())  # Prioridad 3 para caracteres especiales
            if isinstance(value, datetime.time):
                return (5, value)  # Prioridad 5 para objetos datetime.time
            return (6, value)  # Prioridad 6 para otros tipos

        # Determinar si es orden descendente
        reverse = direction == "desc"

        try:
            events_user = sorted(events_user, key=sort_key, reverse=reverse)
        except KeyError:
            # Ordenamiento por defecto si la clave no existe
            events_user = sorted(
                events_user, key=lambda x: x["company"].lower(), reverse=reverse
            )
        page_size = paginate_by  # Número de elementos por página.
        paginator = Paginator(events_user, page_size)
        try:
            page = paginator.page(page_number)
        except PageNotAnInteger:
            page = paginator.page(1)
        except EmptyPage:
            page = paginator.page(paginator.num_pages)

        formatted_results = []
        for event_user in page.object_list:
            formatted_results.append(
                {
                    "id": event_user["id"],
                    "alias": event_user["alias"] or "",
                    "company": event_user["company"] or "",
                    "central_alarm": event_user["central_alarm"] or False,
                    "user_alarm": event_user["user_alarm"] or False,
                    "email_alarm": event_user["email_alarm"] or False,
                    "alarm_sound": event_user["alarm_sound"] or False,
                    "sound_priority": event_user["sound_priority"] or "",
                    "type_alarm_sound": event_user["type_alarm_sound"] or "",
                    "start_time": event_user["start_time"] or "",
                    "end_time": event_user["end_time"] or "",
                    "color": event_user["color"] or "",
                    "get_type_alarm_sound_display": event_user[
                        "get_type_alarm_sound_display"
                    ]
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
    
@method_decorator(csrf_exempt, name='dispatch')
class ExportDataEvents(View):
    def get(self, request):
        search_query = request.GET.get('query', None)
        event_predefined = fetch_all_event(search_query)
        formatted_results = []
        # Encabezados traducidos
        headers = [
            _("Event name"),
            _("Event number")
        ]

        for event in event_predefined:
            formatted_results.append({
                "name": event["name"] or "",
                "number": event["number"] or 0,
            })
        response_data = {
            'headers': headers,
            'data': formatted_results
        }
        return JsonResponse(response_data, safe=False)
    

@method_decorator(csrf_exempt, name='dispatch')
class ExportDataEventsusers(View):
    def get(self, request):
        user_id = request.user.id
        search_query = request.GET.get('query', None)
        events_user = fetch_all_event_personalized(
            request.user.company, user_id, search_query
        )
        formatted_results = []
        # Encabezados traducidos
        headers = [
            _("Event name"),
            _("Company"),
            _("Central alarm"),
            _("User alarm"),
            _("Email alarm"),
            _("Alarm sound"),
            _("Priority"),
            _("Alarm"),
            _("Color"),
            _("Start time"),
            _("End time")
        ]

        for event_user in events_user:
            formatted_results.append({
                "alias": event_user["alias"] or "",
                "company": event_user["company"] or "",
                "central_alarm": event_user["central_alarm"] or False,
                "user_alarm": event_user["user_alarm"] or False,
                "email_alarm": event_user["email_alarm"] or False,
                "alarm_sound": event_user["alarm_sound"] or False,
                "sound_priority": event_user["sound_priority"] or "",
                "type_alarm_sound": event_user["type_alarm_sound"] or "",
                "start_time": event_user["start_time"] or "",
                "end_time": event_user["end_time"] or "",
                "color": event_user["color"] or "",
                "get_type_alarm_sound_display": event_user[
                    "get_type_alarm_sound_display"
                ]
                or "",
            })
        response_data = {
            'headers': headers,
            'data': formatted_results
        }
        return JsonResponse(response_data, safe=False)
