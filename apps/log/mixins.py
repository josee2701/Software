import asyncio
import json

import aiohttp
from asgiref.sync import async_to_sync, sync_to_async
from django.forms.models import model_to_dict
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from .utils import log_action


async def obtener_ip_publica(request):
    """
    Obtiene la dirección IP pública del usuario desde la solicitud HTTP.
    """
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0]
    else:
        ip = request.META.get("REMOTE_ADDR")
    return ip


class AuditLogAsyncMixin:
    """
    Mixin para registrar acciones de auditoría de manera asíncrona.
    """

    action = None

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        self.request = request
        self.obj_before = None
        if self.action in ["update", "delete"] and hasattr(self, "get_object"):
            instance = self.get_object()
            if instance:
                self.obj_before = instance
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        response = super().form_valid(form)
        if self.action == "create" or self.action == "update":
            self.obj_after = getattr(form, "instance", None)
        elif self.action == "delete":
            self.obj_after = {}

        async_to_sync(self.log_action)()
        return response

    async def log_action(self):
        user = self.request.user
        company_id = getattr(user, "company_id", None)
        view_name = self.__class__.__name__
        ip_address = await obtener_ip_publica(self.request)

        before = (
            [await sync_to_async(model_to_dict)(obj) for obj in self.obj_before]
            if isinstance(self.obj_before, list)
            else (
                await sync_to_async(model_to_dict)(self.obj_before)
                if self.obj_before
                else {}
            )
        )
        after = (
            [await sync_to_async(model_to_dict)(obj) for obj in self.obj_after]
            if isinstance(self.obj_after, list)
            else (
                await sync_to_async(model_to_dict)(self.obj_after)
                if self.obj_after
                else {}
            )
        )

        before_json = json.dumps(before, default=str)
        after_json = json.dumps(after, default=str)

        await sync_to_async(log_action)(
            user=user,
            company_id=company_id,
            view_name=view_name,
            action=self.action,
            before=before_json,
            after=after_json,
            ip_address=ip_address,
        )


class AuditLogSyncMixin:
    """
    Mixin para registrar acciones de auditoría de manera sincrónica.
    """

    action = None

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        self.request = request
        self.obj_before = None
        if self.action in ["update", "delete"] and hasattr(self, "get_object"):
            instance = self.get_object()
            if instance:
                self.obj_before = instance
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        response = super().form_valid(form)
        if self.action in ["create", "update"]:
            self.obj_after = getattr(form, "instance", None)
        elif self.action == "delete":
            self.obj_after = {}

        self.log_action()
        return response

    def log_action(self):
        user = self.request.user
        company_id = getattr(user, "company_id", None)
        view_name = self.__class__.__name__
        ip_address = asyncio.run(obtener_ip_publica(self.request))

        before = model_to_dict(self.obj_before) if self.obj_before else {}
        after = model_to_dict(self.obj_after) if self.obj_after else {}

        before_json = json.dumps(before, default=str)
        after_json = json.dumps(after, default=str)

        log_action(
            user=user,
            company_id=company_id,
            view_name=view_name,
            action=self.action,
            before=before_json,
            after=after_json,
            ip_address=ip_address,
        )


# Mixins específicos para cada acción
class CreateAuditLogAsyncMixin(AuditLogAsyncMixin):
    """
    Mixin específico para registrar acciones de creación asíncronas.
    """

    action = "create"


class UpdateAuditLogAsyncMixin(AuditLogAsyncMixin):
    """
    Mixin específico para registrar acciones de actualización asíncronas.
    """

    action = "update"


class DeleteAuditLogAsyncMixin(AuditLogAsyncMixin):
    """
    Mixin específico para registrar acciones de eliminación asíncronas.
    """

    action = "delete"


class CreateAuditLogSyncMixin(AuditLogSyncMixin):
    """
    Mixin específico para registrar acciones de creación sincrónicas.
    """

    action = "create"


class UpdateAuditLogSyncMixin(AuditLogSyncMixin):
    """
    Mixin específico para registrar acciones de actualización sincrónicas.
    """

    action = "update"


class DeleteAuditLogSyncMixin(AuditLogSyncMixin):
    """
    Mixin específico para registrar acciones de eliminación sincrónicas.
    """

    action = "delete"
