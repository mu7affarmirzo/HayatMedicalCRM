from django.db import models
from core.models import BaseAuditModel
from core.models.rooms import RoomType
from core.models.services import Service


class Tariff(BaseAuditModel):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    services = models.ManyToManyField(Service, through='TariffService', related_name='tariffs')
    price = models.PositiveBigIntegerField(default=0, null=True, blank=True)
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
    # DO not delete this table even if it seems meaningless
    tariff = models.ForeignKey(Tariff, on_delete=models.CASCADE, related_name='prices')
    room_type = models.ForeignKey(RoomType, on_delete=models.CASCADE, related_name='tariff_prices')
    price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        unique_together = ['tariff', 'room_type']

    def __str__(self):
        return f"{self.tariff.name} - {self.room_type.name}: {self.price}"


class ServiceSessionTracking(BaseAuditModel):
    """
    Tracks service usage per BookingDetail period for billing purposes.
    Each BookingDetail (tariff period) has its own tracking records.
    """
    booking_detail = models.ForeignKey(
        'BookingDetail',
        on_delete=models.CASCADE,
        related_name='service_tracking',
        help_text="The BookingDetail period this tracking belongs to"
    )
    service = models.ForeignKey(
        Service,
        on_delete=models.CASCADE,
        related_name='session_tracking',
        help_text="The service being tracked"
    )
    tariff_service = models.ForeignKey(
        TariffService,
        on_delete=models.CASCADE,
        related_name='tracking_records',
        help_text="Reference to the tariff's service configuration"
    )

    # Session tracking
    sessions_included = models.PositiveIntegerField(
        default=0,
        help_text="Number of sessions included in tariff for this period"
    )
    sessions_used = models.PositiveIntegerField(
        default=0,
        help_text="Number of sessions actually used in this period"
    )
    sessions_billed = models.PositiveIntegerField(
        default=0,
        help_text="Number of sessions that were charged (beyond included amount)"
    )

    class Meta:
        unique_together = ['booking_detail', 'service']
        verbose_name = 'Service Session Tracking'
        verbose_name_plural = 'Service Session Trackings'
        indexes = [
            models.Index(fields=['booking_detail', 'service'], name='idx_tracking_bd_service'),
        ]

    def __str__(self):
        return f"{self.booking_detail} - {self.service.name}: {self.sessions_used}/{self.sessions_included}"

    @property
    def sessions_remaining(self):
        """Calculate remaining free sessions"""
        return max(0, self.sessions_included - self.sessions_used)

    @property
    def sessions_exceeded(self):
        """Calculate sessions that exceeded the included amount"""
        return max(0, self.sessions_used - self.sessions_included)

    def increment_session(self, is_billable=False):
        """
        Increment session usage counters.

        Args:
            is_billable: If True, increment sessions_billed as well
        """
        self.sessions_used += 1
        if is_billable:
            self.sessions_billed += 1
        self.save(update_fields=['sessions_used', 'sessions_billed', 'updated_at'])
