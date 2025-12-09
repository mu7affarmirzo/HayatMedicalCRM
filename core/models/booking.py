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
        RESERVATION = 'reservation', 'Резервация'  # TASK-028: New reservation status
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
            self.BookingStatus.RESERVATION,
            self.BookingStatus.CONFIRMED,
            self.BookingStatus.CHECKED_IN,
            self.BookingStatus.IN_PROGRESS
        ]

    @property
    def status_display_color(self):
        """Return CSS color class for status display"""
        color_mapping = {
            self.BookingStatus.RESERVATION: 'secondary',
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


class BookingDeposit(BaseAuditModel):
    """
    TASK-029: Model to track deposits for reservations.
    Stores deposit amount, payment method, and status.
    """

    class DepositStatus(models.TextChoices):
        PENDING = 'pending', 'Ожидается'
        PAID = 'paid', 'Оплачен'
        REFUNDED = 'refunded', 'Возвращен'
        FORFEITED = 'forfeited', 'Аннулирован'

    class PaymentMethod(models.TextChoices):
        CASH = 'cash', 'Наличные'
        CARD = 'card', 'Карта'
        BANK_TRANSFER = 'bank_transfer', 'Банковский перевод'
        ONLINE = 'online', 'Онлайн оплата'

    booking = models.OneToOneField(
        Booking,
        on_delete=models.CASCADE,
        related_name='deposit',
        help_text="Бронирование, к которому относится депозит",
        db_index=True
    )

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Сумма депозита"
    )

    deposit_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Процент от общей стоимости (если применимо)"
    )

    payment_method = models.CharField(
        max_length=20,
        choices=PaymentMethod.choices,
        null=True,
        blank=True,
        help_text="Способ оплаты депозита"
    )

    status = models.CharField(
        max_length=20,
        choices=DepositStatus.choices,
        default=DepositStatus.PENDING,
        help_text="Статус депозита",
        db_index=True
    )

    paid_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Когда был оплачен депозит"
    )

    refunded_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Когда был возвращен депозит"
    )

    refund_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Сумма возврата (может отличаться от суммы депозита)"
    )

    notes = models.TextField(
        blank=True,
        null=True,
        help_text="Примечания к депозиту"
    )

    receipt_number = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Номер квитанции об оплате",
        db_index=True
    )

    processed_by = models.ForeignKey(
        'Account',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='processed_deposits',
        help_text="Сотрудник, обработавший депозит"
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Booking Deposit'
        verbose_name_plural = 'Booking Deposits'
        indexes = [
            models.Index(fields=['booking'], name='idx_deposit_booking'),
            models.Index(fields=['status'], name='idx_deposit_status'),
            models.Index(fields=['paid_at'], name='idx_deposit_paid_at'),
            models.Index(fields=['receipt_number'], name='idx_deposit_receipt'),
        ]

    def __str__(self):
        return f"Deposit for {self.booking.booking_number} - {self.amount} ({self.get_status_display()})"

    def mark_as_paid(self, payment_method, processed_by, receipt_number=None):
        """
        Mark deposit as paid.

        Args:
            payment_method: PaymentMethod choice
            processed_by: Account instance who processed the payment
            receipt_number: Optional receipt number
        """
        self.status = self.DepositStatus.PAID
        self.payment_method = payment_method
        self.paid_at = timezone.now()
        self.processed_by = processed_by
        if receipt_number:
            self.receipt_number = receipt_number
        self.save(update_fields=['status', 'payment_method', 'paid_at', 'processed_by', 'receipt_number', 'updated_at'])

    def refund(self, refund_amount=None, processed_by=None, notes=None):
        """
        Process a deposit refund.

        Args:
            refund_amount: Amount to refund (defaults to full deposit amount)
            processed_by: Account instance who processed the refund
            notes: Refund notes
        """
        self.status = self.DepositStatus.REFUNDED
        self.refund_amount = refund_amount if refund_amount is not None else self.amount
        self.refunded_at = timezone.now()
        if processed_by:
            self.processed_by = processed_by
        if notes:
            self.notes = (self.notes or '') + f'\nRefund: {notes}'
        self.save(update_fields=['status', 'refund_amount', 'refunded_at', 'processed_by', 'notes', 'updated_at'])

    def forfeit(self, notes=None):
        """
        Forfeit the deposit (e.g., due to late cancellation or no-show).

        Args:
            notes: Reason for forfeiture
        """
        self.status = self.DepositStatus.FORFEITED
        if notes:
            self.notes = (self.notes or '') + f'\nForfeited: {notes}'
        self.save(update_fields=['status', 'notes', 'updated_at'])

    @property
    def is_paid(self):
        """Check if deposit has been paid"""
        return self.status == self.DepositStatus.PAID

    @property
    def is_refundable(self):
        """Check if deposit can be refunded"""
        return self.status == self.DepositStatus.PAID

    @property
    def status_color(self):
        """Return Bootstrap color class for status display"""
        color_mapping = {
            self.DepositStatus.PENDING: 'warning',
            self.DepositStatus.PAID: 'success',
            self.DepositStatus.REFUNDED: 'info',
            self.DepositStatus.FORFEITED: 'danger',
        }
        return color_mapping.get(self.status, 'secondary')


class Waitlist(BaseAuditModel):
    """
    TASK-035: Waitlist model for managing booking requests when rooms are unavailable.
    Automatically notifies when rooms become available.
    """

    class WaitlistStatus(models.TextChoices):
        ACTIVE = 'active', 'Активен'
        CONTACTED = 'contacted', 'Связались'
        CONVERTED = 'converted', 'Преобразован в бронирование'
        EXPIRED = 'expired', 'Истек'
        CANCELLED = 'cancelled', 'Отменен'

    class Priority(models.TextChoices):
        LOW = 'low', 'Низкий'
        NORMAL = 'normal', 'Обычный'
        HIGH = 'high', 'Высокий'
        URGENT = 'urgent', 'Срочный'

    patient = models.ForeignKey(
        PatientModel,
        on_delete=models.CASCADE,
        related_name='waitlist_entries',
        help_text="Пациент в листе ожидания",
        db_index=True
    )

    desired_start_date = models.DateTimeField(
        help_text="Желаемая дата начала",
        db_index=True
    )

    desired_end_date = models.DateTimeField(
        help_text="Желаемая дата окончания",
        db_index=True
    )

    desired_room_type = models.ForeignKey(
        'RoomType',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='waitlist_entries',
        help_text="Желаемый тип комнаты"
    )

    desired_tariff = models.ForeignKey(
        'Tariff',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='waitlist_entries',
        help_text="Желаемый тариф"
    )

    number_of_guests = models.PositiveSmallIntegerField(
        default=1,
        help_text="Количество гостей"
    )

    priority = models.CharField(
        max_length=10,
        choices=Priority.choices,
        default=Priority.NORMAL,
        help_text="Приоритет запроса",
        db_index=True
    )

    status = models.CharField(
        max_length=20,
        choices=WaitlistStatus.choices,
        default=WaitlistStatus.ACTIVE,
        help_text="Статус записи в листе ожидания",
        db_index=True
    )

    contacted_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Когда связались с клиентом"
    )

    contacted_by = models.ForeignKey(
        'Account',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='waitlist_contacts',
        help_text="Кто связался с клиентом"
    )

    converted_booking = models.ForeignKey(
        Booking,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='waitlist_source',
        help_text="Бронирование, созданное из листа ожидания"
    )

    converted_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Когда был преобразован в бронирование"
    )

    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Когда истекает запрос (авто-расчет)",
        db_index=True
    )

    notes = models.TextField(
        blank=True,
        null=True,
        help_text="Примечания к запросу"
    )

    contact_preference = models.CharField(
        max_length=20,
        choices=[
            ('phone', 'Телефон'),
            ('email', 'Email'),
            ('sms', 'SMS'),
            ('any', 'Любой')
        ],
        default='phone',
        help_text="Предпочтительный способ связи"
    )

    created_by = models.ForeignKey(
        'Account',
        on_delete=models.SET_NULL,
        null=True,
        related_name='waitlist_created',
        help_text="Кто создал запись"
    )

    class Meta:
        ordering = ['priority', 'created_at']
        verbose_name = 'Waitlist Entry'
        verbose_name_plural = 'Waitlist Entries'
        indexes = [
            models.Index(fields=['status', 'priority', 'created_at'], name='idx_waitlist_status_priority'),
            models.Index(fields=['desired_start_date', 'desired_end_date'], name='idx_waitlist_dates'),
            models.Index(fields=['patient'], name='idx_waitlist_patient'),
            models.Index(fields=['expires_at'], name='idx_waitlist_expires'),
        ]

    def __str__(self):
        return f"Waitlist: {self.patient.full_name} - {self.desired_start_date.strftime('%Y-%m-%d')} ({self.get_status_display()})"

    def save(self, *args, **kwargs):
        """Auto-set expires_at if not set (default to desired_start_date)"""
        if not self.expires_at and self.desired_start_date:
            self.expires_at = self.desired_start_date
        super().save(*args, **kwargs)

    def mark_contacted(self, contacted_by, notes=None):
        """
        Mark that the patient has been contacted.

        Args:
            contacted_by: Account instance who contacted the patient
            notes: Contact notes
        """
        self.status = self.WaitlistStatus.CONTACTED
        self.contacted_at = timezone.now()
        self.contacted_by = contacted_by
        if notes:
            self.notes = (self.notes or '') + f'\nContacted: {notes}'
        self.save(update_fields=['status', 'contacted_at', 'contacted_by', 'notes', 'updated_at'])

    def convert_to_booking(self, booking):
        """
        Convert waitlist entry to an actual booking.

        Args:
            booking: Booking instance that was created from this waitlist entry
        """
        self.status = self.WaitlistStatus.CONVERTED
        self.converted_booking = booking
        self.converted_at = timezone.now()
        self.save(update_fields=['status', 'converted_booking', 'converted_at', 'updated_at'])

    def cancel(self, reason=None):
        """
        Cancel the waitlist entry.

        Args:
            reason: Reason for cancellation
        """
        self.status = self.WaitlistStatus.CANCELLED
        if reason:
            self.notes = (self.notes or '') + f'\nCancelled: {reason}'
        self.save(update_fields=['status', 'notes', 'updated_at'])

    def mark_expired(self):
        """Mark the waitlist entry as expired"""
        self.status = self.WaitlistStatus.EXPIRED
        self.save(update_fields=['status', 'updated_at'])

    @property
    def is_active(self):
        """Check if waitlist entry is active"""
        return self.status == self.WaitlistStatus.ACTIVE

    @property
    def status_color(self):
        """Return Bootstrap color class for status display"""
        color_mapping = {
            self.WaitlistStatus.ACTIVE: 'warning',
            self.WaitlistStatus.CONTACTED: 'info',
            self.WaitlistStatus.CONVERTED: 'success',
            self.WaitlistStatus.EXPIRED: 'secondary',
            self.WaitlistStatus.CANCELLED: 'danger',
        }
        return color_mapping.get(self.status, 'secondary')

    @property
    def priority_color(self):
        """Return Bootstrap color class for priority display"""
        color_mapping = {
            self.Priority.LOW: 'secondary',
            self.Priority.NORMAL: 'info',
            self.Priority.HIGH: 'warning',
            self.Priority.URGENT: 'danger',
        }
        return color_mapping.get(self.priority, 'secondary')

    @classmethod
    def get_active_for_dates(cls, start_date, end_date, room_type=None):
        """
        Get active waitlist entries for a date range.

        Args:
            start_date: Start date
            end_date: End date
            room_type: Optional room type filter

        Returns:
            QuerySet of active Waitlist entries
        """
        queryset = cls.objects.filter(
            status=cls.WaitlistStatus.ACTIVE,
            desired_start_date__lte=end_date,
            desired_end_date__gte=start_date
        )
        if room_type:
            queryset = queryset.filter(desired_room_type=room_type)
        return queryset

    @classmethod
    def check_and_expire_old_entries(cls):
        """
        Check and mark expired waitlist entries.
        Should be called periodically (e.g., daily cron job).

        Returns:
            Number of entries marked as expired
        """
        now = timezone.now()
        expired_entries = cls.objects.filter(
            status=cls.WaitlistStatus.ACTIVE,
            expires_at__lt=now
        )
        count = expired_entries.count()
        expired_entries.update(status=cls.WaitlistStatus.EXPIRED, updated_at=now)
        return count


class CheckInLog(BaseAuditModel):
    """TASK-026: Detailed check-in log with medical screening data"""

    class RoomCondition(models.TextChoices):
        EXCELLENT = 'excellent', 'Отличное'
        GOOD = 'good', 'Хорошее'
        FAIR = 'fair', 'Удовлетворительное'
        POOR = 'poor', 'Требует внимания'

    class MobilityStatus(models.TextChoices):
        FULLY_MOBILE = 'fully_mobile', 'Полностью мобильный'
        NEEDS_ASSISTANCE = 'needs_assistance', 'Нуждается в помощи'
        WHEELCHAIR = 'wheelchair', 'Инвалидная коляска'
        BEDRIDDEN = 'bedridden', 'Лежачий'

    booking = models.ForeignKey(
        Booking,
        on_delete=models.CASCADE,
        related_name='check_in_logs',
        db_index=True
    )
    booking_detail = models.OneToOneField(
        BookingDetail,
        on_delete=models.CASCADE,
        related_name='check_in_log',
        db_index=True
    )
    check_in_time = models.DateTimeField()
    room_condition = models.CharField(
        max_length=20,
        choices=RoomCondition.choices
    )
    temperature = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    blood_pressure_systolic = models.IntegerField(null=True, blank=True)
    blood_pressure_diastolic = models.IntegerField(null=True, blank=True)
    pulse = models.IntegerField(null=True, blank=True)
    weight = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    height = models.IntegerField(null=True, blank=True)
    allergies = models.TextField(blank=True, null=True)
    current_medications = models.TextField(blank=True, null=True)
    medical_conditions = models.TextField(blank=True, null=True)
    mobility_status = models.CharField(
        max_length=30,
        choices=MobilityStatus.choices,
        default=MobilityStatus.FULLY_MOBILE,
        db_index=True
    )
    special_dietary_requirements = models.TextField(blank=True, null=True)
    emergency_contact_name = models.CharField(max_length=255, blank=True, null=True)
    emergency_contact_phone = models.CharField(max_length=50, blank=True, null=True)
    emergency_contact_relationship = models.CharField(max_length=100, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    belongings_checked = models.BooleanField(default=False)
    room_orientation_completed = models.BooleanField(default=False)
    facility_tour_completed = models.BooleanField(default=False)
    documents_signed = models.BooleanField(default=False)

    class Meta:
        ordering = ['-check_in_time']
        verbose_name = 'Check-in Log'
        verbose_name_plural = 'Check-in Logs'
        indexes = [
            models.Index(fields=['booking', '-check_in_time'], name='idx_checkin_booking_time'),
            models.Index(fields=['booking_detail'], name='idx_checkin_detail'),
            models.Index(fields=['mobility_status'], name='idx_checkin_mobility'),
        ]

    def __str__(self):
        return f"Check-in for {self.booking_detail.client.full_name} at {self.check_in_time.strftime('%Y-%m-%d %H:%M')}"


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