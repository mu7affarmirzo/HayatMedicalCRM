import uuid
import random

from django.utils import timezone
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

    class BookingStatus(models.TextChoices):
        PENDING = 'pending', 'В ожидании'
        CONFIRMED = 'confirmed', 'Подтверждено'
        CHECKED_IN = 'checked_in', 'Заселен'
        IN_PROGRESS = 'in_progress', 'В процессе'
        COMPLETED = 'completed', 'Завершено'
        CANCELLED = 'cancelled', 'Отменено'
        DISCHARGED = 'discharged', 'Выписан'

    booking_number = models.CharField(max_length=20, unique=True)
    staff = models.ForeignKey('Account', on_delete=models.SET_NULL, null=True, related_name='bookings')

    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    notes = models.TextField(blank=True, null=True)

    status = models.CharField(
        max_length=20,
        choices=BookingStatus.choices,
        default=BookingStatus.PENDING
    )

    class Meta:
        indexes = [
            # TASK-052: Database optimization indexes
            models.Index(fields=['booking_number'], name='idx_booking_number'),
            models.Index(fields=['status'], name='idx_booking_status'),
            models.Index(fields=['start_date', 'end_date'], name='idx_booking_dates'),
            models.Index(fields=['staff'], name='idx_booking_staff'),
            models.Index(fields=['-created_at'], name='idx_booking_created'),
        ]

    def __str__(self):
        return f"Booking #{self.booking_number}"

    def total_price(self):
        booking_details_total = sum(detail.price for detail in self.details.all())
        additional_services_total = sum(service.price for service in self.additional_services.all())
        return booking_details_total + additional_services_total

    @property
    def is_active(self):
        """Check if booking is currently active"""
        return self.status in [
            self.BookingStatus.CONFIRMED,
            self.BookingStatus.CHECKED_IN,
            self.BookingStatus.IN_PROGRESS
        ]

    @property
    def status_display_color(self):
        """Return CSS color class for status display"""
        color_mapping = {
            self.BookingStatus.PENDING: 'warning',
            self.BookingStatus.CONFIRMED: 'info',
            self.BookingStatus.CHECKED_IN: 'primary',
            self.BookingStatus.IN_PROGRESS: 'primary',
            self.BookingStatus.COMPLETED: 'success',
            self.BookingStatus.CANCELLED: 'danger',
            self.BookingStatus.DISCHARGED: 'success',
        }
        return color_mapping.get(self.status, 'secondary')

    @staticmethod
    def generate_booking_number():
        """Generate unique booking number"""

        # Format: BK-YYYYMMDD-XXXX
        date_part = timezone.now().strftime('%Y%m%d')
        random_part = f"{random.randint(1000, 9999)}"

        booking_number = f"BK-{date_part}-{random_part}"

        # Ensure uniqueness
        while Booking.objects.filter(booking_number=booking_number).exists():
            random_part = f"{random.randint(1000, 9999)}"
            booking_number = f"BK-{date_part}-{random_part}"

        return booking_number


class BookingDetail(BaseAuditModel):
    """Individual client booking within a group booking"""
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='details')
    client = models.ForeignKey(PatientModel, on_delete=models.CASCADE, related_name='bookings')
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='bookings')
    tariff = models.ForeignKey(Tariff, on_delete=models.CASCADE, related_name='bookings')
    price = models.DecimalField(max_digits=10, decimal_places=2)

    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)

    # New fields for tariff change tracking
    effective_from = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When this tariff/room combination started",
        db_index=True
    )
    effective_to = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When this tariff/room combination ended",
        db_index=True
    )
    is_current = models.BooleanField(
        default=True,
        help_text="Is this the current active tariff/room?",
        db_index=True
    )

    class Meta:
        ordering = ['-effective_from']
        indexes = [
            models.Index(fields=['booking', 'client', 'effective_from'], name='idx_booking_client_eff'),
            models.Index(fields=['booking', 'is_current'], name='idx_booking_is_current'),
        ]

    def __str__(self):
        if self.effective_from:
            period = f"({self.effective_from.strftime('%Y-%m-%d')} - "
            if self.effective_to:
                period += self.effective_to.strftime('%Y-%m-%d')
            else:
                period += "current"
            period += ")"
            return f"{self.booking.booking_number} - {self.client.full_name} - {self.room.name} - {self.tariff.name} {period}"
        return f"{self.booking.booking_number} - {self.client.full_name} - {self.room.name} - {self.tariff.name}"

    def save(self, *args, **kwargs):
        # Set effective_from to start_date if not set
        if not self.effective_from and self.start_date:
            self.effective_from = self.start_date

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

        is_new = self.pk is None
        super().save(*args, **kwargs)

        # Initialize ServiceSessionTracking for new BookingDetail
        if is_new:
            self._initialize_service_tracking()

    def _initialize_service_tracking(self):
        """Initialize ServiceSessionTracking records for all services in tariff"""
        from core.models.tariffs import ServiceSessionTracking

        for tariff_service in self.tariff.tariff_services.all():
            ServiceSessionTracking.objects.get_or_create(
                booking_detail=self,
                service=tariff_service.service,
                tariff_service=tariff_service,
                defaults={
                    'sessions_included': tariff_service.sessions_included,
                    'sessions_used': 0,
                    'sessions_billed': 0
                }
            )

    @staticmethod
    def change_tariff(booking, client, new_tariff, new_room=None, change_datetime=None):
        """
        Change tariff and/or room for a client within a booking.

        Args:
            booking: Booking instance
            client: PatientModel instance
            new_tariff: New Tariff instance
            new_room: New Room instance (optional, keep current if None)
            change_datetime: DateTime when change takes effect (default: now)

        Returns:
            New BookingDetail instance
        """
        if change_datetime is None:
            change_datetime = timezone.now()

        # Get the current active BookingDetail
        try:
            current_detail = BookingDetail.objects.get(
                booking=booking,
                client=client,
                is_current=True
            )
        except BookingDetail.DoesNotExist:
            raise ValueError(f"No active BookingDetail found for client {client.full_name} in booking {booking.booking_number}")

        # Close the current BookingDetail
        current_detail.effective_to = change_datetime
        current_detail.is_current = False
        current_detail.save(update_fields=['effective_to', 'is_current', 'updated_at'])

        # Determine the room for new detail
        room = new_room if new_room else current_detail.room

        # Calculate price for new tariff/room combination
        try:
            price_record = TariffRoomPrice.objects.get(
                tariff=new_tariff,
                room_type=room.room_type
            )
            price = price_record.price
        except TariffRoomPrice.DoesNotExist:
            price = new_tariff.price if new_tariff.price else 0

        # Create new BookingDetail
        new_detail = BookingDetail.objects.create(
            booking=booking,
            client=client,
            room=room,
            tariff=new_tariff,
            price=price,
            start_date=current_detail.start_date,
            end_date=current_detail.end_date,
            effective_from=change_datetime,
            effective_to=None,
            is_current=True
        )

        return new_detail

    @staticmethod
    def get_active_detail_at(booking, client, check_datetime):
        """
        Get the BookingDetail that was active at a specific datetime.

        Args:
            booking: Booking instance
            client: PatientModel instance
            check_datetime: DateTime to check

        Returns:
            BookingDetail instance or None
        """
        try:
            return BookingDetail.objects.filter(
                booking=booking,
                client=client,
                effective_from__lte=check_datetime
            ).filter(
                models.Q(effective_to__gte=check_datetime) | models.Q(effective_to__isnull=True)
            ).get()
        except BookingDetail.DoesNotExist:
            return None
        except BookingDetail.MultipleObjectsReturned:
            # Should not happen with proper data, but handle gracefully
            return BookingDetail.objects.filter(
                booking=booking,
                client=client,
                effective_from__lte=check_datetime
            ).filter(
                models.Q(effective_to__gte=check_datetime) | models.Q(effective_to__isnull=True)
            ).order_by('-effective_from').first()

    def get_days_in_period(self):
        """Calculate number of days this tariff/room was active"""
        start = self.effective_from if self.effective_from else self.start_date
        if not start:
            return 0
        end = self.effective_to if self.effective_to else timezone.now()
        return (end - start).days + 1  # +1 to include both start and end days

    def get_prorated_price(self):
        """Calculate prorated price based on days in period"""
        if not self.booking.start_date or not self.booking.end_date:
            return self.price

        total_booking_days = (self.booking.end_date - self.booking.start_date).days + 1
        days_in_period = self.get_days_in_period()

        if total_booking_days <= 0:
            return self.price

        return (self.price / total_booking_days) * days_in_period


class BookingBilling(BaseAuditModel):
    """
    Model to track billing information for each booking.
    Stores breakdown of costs including tariff base amount and additional charges.
    """

    class BillingStatus(models.TextChoices):
        PENDING = 'pending', 'Pending'
        CALCULATED = 'calculated', 'Calculated'
        INVOICED = 'invoiced', 'Invoiced'
        PAID = 'paid', 'Paid'
        PARTIALLY_PAID = 'partially_paid', 'Partially Paid'

    booking = models.OneToOneField(
        Booking,
        on_delete=models.CASCADE,
        related_name='billing',
        help_text="Reference to the booking this billing record belongs to"
    )

    tariff_base_amount = models.IntegerField(
        default=0,
        help_text="Base amount from the tariff package"
    )

    additional_services_amount = models.IntegerField(
        default=0,
        help_text="Amount for services not included in tariff or exceeding included quantities"
    )

    medications_amount = models.IntegerField(
        default=0,
        help_text="Total amount for prescribed medications"
    )

    lab_research_amount = models.IntegerField(
        default=0,
        help_text="Total amount for laboratory research and tests"
    )

    total_amount = models.IntegerField(
        default=0,
        help_text="Total billing amount (sum of all components)"
    )

    billing_status = models.CharField(
        max_length=20,
        choices=BillingStatus.choices,
        default=BillingStatus.PENDING,
        help_text="Current status of the billing calculation"
    )

    class Meta:
        db_table = 'booking_billing'
        verbose_name = 'Booking Billing'
        verbose_name_plural = 'Booking Billings'
        indexes = [
            models.Index(fields=['booking'], name='idx_billing_booking'),
            models.Index(fields=['billing_status'], name='idx_billing_status'),
            models.Index(fields=['created_at'], name='idx_billing_calculated'),
        ]

    def __str__(self):
        return f"Billing for Booking #{self.booking.booking_number} - {self.total_amount}"

    def calculate_total(self):
        """
        Calculate and update the total amount from all components.
        """
        self.total_amount = (
                self.tariff_base_amount +
                self.additional_services_amount +
                self.medications_amount +
                self.lab_research_amount
        )
        return self.total_amount

    def save(self, *args, **kwargs):
        """
        Override save to automatically calculate total before saving.
        """
        self.calculate_total()
        super().save(*args, **kwargs)

    @property
    def is_calculated(self):
        """Check if billing has been calculated."""
        return self.billing_status in [self.BillingStatus.CALCULATED, self.BillingStatus.INVOICED]

    @property
    def is_invoiced(self):
        """Check if billing has been invoiced."""
        return self.billing_status == self.BillingStatus.INVOICED


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


class BookingHistory(BaseAuditModel):
    """
    TASK-021: Audit trail model for tracking all changes to bookings.
    Records what changed, when it changed, who changed it, and the old/new values.
    """

    class ActionType(models.TextChoices):
        CREATED = 'created', 'Создано'
        STATUS_CHANGED = 'status_changed', 'Изменен статус'
        DATES_CHANGED = 'dates_changed', 'Изменены даты'
        TARIFF_CHANGED = 'tariff_changed', 'Изменен тариф'
        ROOM_CHANGED = 'room_changed', 'Изменена комната'
        GUEST_ADDED = 'guest_added', 'Добавлен гость'
        GUEST_REMOVED = 'guest_removed', 'Удален гость'
        SERVICE_ADDED = 'service_added', 'Добавлена услуга'
        SERVICE_REMOVED = 'service_removed', 'Удалена услуга'
        SERVICE_SESSION_RECORDED = 'service_session_recorded', 'Записана сессия услуги'
        NOTES_UPDATED = 'notes_updated', 'Обновлены примечания'
        OTHER = 'other', 'Другое'

    booking = models.ForeignKey(
        Booking,
        on_delete=models.CASCADE,
        related_name='history',
        help_text="Бронирование, к которому относится запись истории",
        db_index=True
    )

    action = models.CharField(
        max_length=50,
        choices=ActionType.choices,
        help_text="Тип выполненного действия",
        db_index=True
    )

    field_name = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Название измененного поля (если применимо)"
    )

    old_value = models.TextField(
        blank=True,
        null=True,
        help_text="Предыдущее значение"
    )

    new_value = models.TextField(
        blank=True,
        null=True,
        help_text="Новое значение"
    )

    description = models.TextField(
        blank=True,
        null=True,
        help_text="Описание изменения"
    )

    changed_by = models.ForeignKey(
        'Account',
        on_delete=models.SET_NULL,
        null=True,
        related_name='booking_changes',
        help_text="Пользователь, который внес изменение",
        db_index=True
    )

    changed_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Когда было сделано изменение",
        db_index=True
    )

    # Optional: link to specific booking detail if relevant
    booking_detail = models.ForeignKey(
        BookingDetail,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='history',
        help_text="Конкретная деталь бронирования (если применимо)"
    )

    class Meta:
        ordering = ['-changed_at']
        verbose_name = 'Booking History'
        verbose_name_plural = 'Booking Histories'
        indexes = [
            models.Index(fields=['booking', '-changed_at'], name='idx_booking_hist_date'),
            models.Index(fields=['booking', 'action'], name='idx_booking_hist_action'),
            models.Index(fields=['changed_by', '-changed_at'], name='idx_booking_hist_user'),
        ]

    def __str__(self):
        return f"{self.booking.booking_number} - {self.get_action_display()} by {self.changed_by} at {self.changed_at}"

    @classmethod
    def log_change(cls, booking, action, changed_by, field_name=None, old_value=None,
                   new_value=None, description=None, booking_detail=None):
        """
        Convenience method to create a history record.

        Args:
            booking: Booking instance
            action: ActionType choice value
            changed_by: User (Account) who made the change
            field_name: Name of the field that changed (optional)
            old_value: Previous value (optional)
            new_value: New value (optional)
            description: Human-readable description (optional)
            booking_detail: Related BookingDetail (optional)

        Returns:
            BookingHistory instance
        """
        # Convert values to strings if they're not None
        old_value_str = str(old_value) if old_value is not None else None
        new_value_str = str(new_value) if new_value is not None else None

        return cls.objects.create(
            booking=booking,
            action=action,
            field_name=field_name,
            old_value=old_value_str,
            new_value=new_value_str,
            description=description,
            changed_by=changed_by,
            booking_detail=booking_detail
        )

    @property
    def action_icon(self):
        """Return FontAwesome icon class for this action type"""
        icon_mapping = {
            self.ActionType.CREATED: 'fa-plus-circle',
            self.ActionType.STATUS_CHANGED: 'fa-exchange-alt',
            self.ActionType.DATES_CHANGED: 'fa-calendar-alt',
            self.ActionType.TARIFF_CHANGED: 'fa-money-bill-wave',
            self.ActionType.ROOM_CHANGED: 'fa-door-open',
            self.ActionType.GUEST_ADDED: 'fa-user-plus',
            self.ActionType.GUEST_REMOVED: 'fa-user-minus',
            self.ActionType.SERVICE_ADDED: 'fa-briefcase-medical',
            self.ActionType.SERVICE_REMOVED: 'fa-times-circle',
            self.ActionType.SERVICE_SESSION_RECORDED: 'fa-check-circle',
            self.ActionType.NOTES_UPDATED: 'fa-sticky-note',
            self.ActionType.OTHER: 'fa-info-circle',
        }
        return icon_mapping.get(self.action, 'fa-info-circle')

    @property
    def action_color(self):
        """Return Bootstrap color class for this action type"""
        color_mapping = {
            self.ActionType.CREATED: 'success',
            self.ActionType.STATUS_CHANGED: 'info',
            self.ActionType.DATES_CHANGED: 'warning',
            self.ActionType.TARIFF_CHANGED: 'primary',
            self.ActionType.ROOM_CHANGED: 'primary',
            self.ActionType.GUEST_ADDED: 'success',
            self.ActionType.GUEST_REMOVED: 'danger',
            self.ActionType.SERVICE_ADDED: 'success',
            self.ActionType.SERVICE_REMOVED: 'danger',
            self.ActionType.SERVICE_SESSION_RECORDED: 'info',
            self.ActionType.NOTES_UPDATED: 'secondary',
            self.ActionType.OTHER: 'secondary',
        }
        return color_mapping.get(self.action, 'secondary')



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