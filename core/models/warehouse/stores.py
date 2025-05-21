from django.db import models
from core.models import BaseAuditModel, Account


class Warehouse(BaseAuditModel):
    is_main = models.BooleanField(default=False)
    is_emergency = models.BooleanField(default=False)
    name = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    email = models.EmailField()

    def __str__(self):
        return f"{self.name} - {self.address} - {self.is_main}"

    class Meta:
        verbose_name_plural = "Warehouses | Warehouse"
        verbose_name = "Warehouses | Warehouse"

