from django.db import models
from core.models import BaseAuditModel


class Service(BaseAuditModel):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    duration_minutes = models.PositiveIntegerField(default=30, null=True, blank=True)
    base_price = models.PositiveIntegerField(default=0, null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name
