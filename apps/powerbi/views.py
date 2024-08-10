# apps/powerbi/views.py

import logging
import uuid

from django.http import HttpResponseServerError, JsonResponse
from django.views import View

from .embed_service import EmbedService


class ReportEmbedView(View):
    def get(self, request, workspace_id, report_id):
        try:
            workspace_id = uuid.UUID(workspace_id)
            report_id = uuid.UUID(report_id)
            embed_params = EmbedService.get_embed_params(workspace_id, report_id)
            return JsonResponse(embed_params, safe=False)
        except Exception as e:
            logging.error(str(e))
            return HttpResponseServerError(str(e))


class ReportUserView(View):
    def get(self, request, user_id):
        try:
            embed_result = EmbedService.get_embed_user(user_id)
            return JsonResponse(embed_result, safe=False)
        except Exception as e:
            logging.error(str(e))
            return HttpResponseServerError(str(e))


class GroupsView(View):
    def get(self, request):
        try:
            groups = EmbedService.get_groups()
            return JsonResponse(groups, safe=False)
        except Exception as e:
            logging.error(str(e))
            return HttpResponseServerError(str(e))


class ReportsInGroupView(View):
    def get(self, request, group_id):
        try:
            reports = EmbedService.get_reports_in_group(group_id)
            return JsonResponse(reports, safe=False)
        except Exception as e:
            logging.error(str(e))
            return HttpResponseServerError(str(e))
