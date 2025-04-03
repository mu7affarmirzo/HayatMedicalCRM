from django.db import models
from core.models import BaseAuditModel
from core.models.rooms import RoomType
from core.models.services import Service


class Tariff(BaseAuditModel):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    services = models.ManyToManyField(Service, through='TariffService', related_name='tariffs')
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class TariffService(BaseAuditModel):
    """Links tariffs to services with session count"""
    tariff = models.ForeignKey(Tariff, on_delete=models.CASCADE, related_name='tariff_services')
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='tariff_inclusions')
    sessions_included = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ['tariff', 'service']

    def __str__(self):
        return f"{self.tariff.name} - {self.service.name}: {self.sessions_included} sessions"


class TariffRoomPrice(BaseAuditModel):
    """Price matrix for tariff and room combinations"""
    tariff = models.ForeignKey(Tariff, on_delete=models.CASCADE, related_name='prices')
    room_type = models.ForeignKey(RoomType, on_delete=models.CASCADE, related_name='tariff_prices')
    price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        unique_together = ['tariff', 'room_type']

    def __str__(self):
        return f"{self.tariff.name} - {self.room_type.name}: {self.price}"
