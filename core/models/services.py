from django.db import models
from core.models import BaseAuditModel, Account


class ServiceTypeModel(BaseAuditModel):
    type = models.CharField(max_length=100)

    def __str__(self):
        return str(self.type)


class Service(BaseAuditModel):
    type = models.ForeignKey(ServiceTypeModel, on_delete=models.SET_NULL, null=True, blank=True, related_name='services')

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    duration_minutes = models.PositiveIntegerField(default=30, null=True, blank=True)
    price = models.PositiveIntegerField(default=0, null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name
