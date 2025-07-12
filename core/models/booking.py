import uuid

from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

from core.models import BaseAuditModel
from core.models.clients import PatientModel
from core.models.rooms import Room
from core.models.services import Service
from core.models.tariffs import TariffRoomPrice, Tariff, TariffService


class Booking(BaseAuditModel):
    """Main booking record"""
    booking_number = models.CharField(max_length=20, unique=True)
    staff = models.ForeignKey('Account', on_delete=models.SET_NULL, null=True, related_name='bookings')

    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    notes = models.TextField(blank=True, null=True)

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('checked_in', 'Checked In'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    def __str__(self):
        return f"Booking #{self.booking_number}"

    def total_price(self):
        booking_details_total = sum(detail.price for detail in self.details.all())
        additional_services_total = sum(service.price for service in self.additional_services.all())
        return booking_details_total + additional_services_total


class BookingDetail(BaseAuditModel):
    """Individual client booking within a group booking"""
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='details')
    client = models.ForeignKey(PatientModel, on_delete=models.CASCADE, related_name='bookings')
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='bookings')
    tariff = models.ForeignKey(Tariff, on_delete=models.CASCADE, related_name='bookings')
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.client.full_name} - {self.room.name} - {self.tariff.name}"

    def save(self, *args, **kwargs):
        # Automatically calculate price based on tariff and room type if not set
        if not self.price:
            try:
                price_record = TariffRoomPrice.objects.get(
                    tariff=self.tariff,
                    room_type=self.room.room_type
                )
                self.price = price_record.price
            except TariffRoomPrice.DoesNotExist:
                pass
        super().save(*args, **kwargs)


class ServiceUsage(BaseAuditModel):
    """Additional services purchased beyond what's included in the tariff"""
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='additional_services')
    booking_detail = models.ForeignKey(BookingDetail, on_delete=models.CASCADE, related_name='service_usages')
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='usages')
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    date_used = models.DateTimeField()
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.booking_detail.client.name} - {self.service.name} x{self.quantity}"

    def save(self, *args, **kwargs):
        # Auto-calculate price if not set
        if not self.price:
            self.price = self.service.base_price * self.quantity
        super().save(*args, **kwargs)


class ServiceSessionTracking(BaseAuditModel):
    """Tracks usage of services included in tariffs"""
    booking_detail = models.ForeignKey(BookingDetail, on_delete=models.CASCADE, related_name='service_sessions')
    tariff_service = models.ForeignKey(TariffService, on_delete=models.CASCADE, related_name='usages')
    sessions_used = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ['booking_detail', 'tariff_service']

    def __str__(self):
        return f"{self.booking_detail.client.full_name} - {self.tariff_service.service.name}: {self.sessions_used}/{self.tariff_service.sessions_included}"

    @property
    def sessions_remaining(self):
        return max(0, self.tariff_service.sessions_included - self.sessions_used)


@receiver(post_save, sender=Booking)
def create_illness_history(sender, instance, created, **kwargs):
    """
    Signal handler to create illness histories when a booking status
    is changed to 'checked_in'
    """
    from core.models import IllnessHistory

    # Skip if this is a new booking (we only want to react to status changes)
    if created:
        return

    # Check if status is 'checked_in'
    if instance.status == 'checked_in':
        # Get all booking details to find patients
        for detail in instance.details.all():
            patient = detail.client

            # Check if an illness history already exists for this booking and patient
            existing_history = IllnessHistory.objects.filter(
                booking=instance,
                patient=patient
            ).exists()

            if not existing_history:
                # Create a new illness history
                IllnessHistory.objects.create(
                    series_number=f"IH-{uuid.uuid4().hex[:8]}",
                    patient=patient,
                    booking=instance,
                    type='stationary',  # Default type
                    state='registration',  # Default initial state
                    # Other fields will use their default values
                )