from django.utils import timezone

from .models import AuditLog


def log_action(user, company_id, view_name, action, before, after, ip_address):
    """
    Registra una acción en el log de auditoría.
    """

    log = AuditLog(
        user=user,
        company_id=company_id,
        view_name=view_name,
        action=action,
        before=before,
        after=after,
        modification_date=timezone.now(),
        ip_address=ip_address,
    )
    log.save()
