from django.db import models
from django.utils import timezone

# En algún lugar central como ready() en apps.py o al final de models.py
from apps.authentication.models import User


class AuditLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    company_id = models.IntegerField()
    view_name = models.CharField(max_length=255)
    action = models.CharField(max_length=50)
    before = models.TextField(null=True, blank=True)
    after = models.TextField(null=True, blank=True)
    modification_date = models.DateTimeField(default=timezone.now)
    ip_address = models.GenericIPAddressField()

    def __str__(self):
        return f"{self.user} - {self.view_name} - {self.action}"
