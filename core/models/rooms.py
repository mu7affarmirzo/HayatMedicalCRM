from django.db import models
from django.utils import timezone

from core.models import BaseAuditModel


class RoomType(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


class Room(models.Model):
    name = models.CharField(max_length=50)
    room_type = models.ForeignKey(RoomType, on_delete=models.CASCADE, related_name='rooms')
    price = models.PositiveBigIntegerField(default=0, blank=True, null=True)
    capacity = models.PositiveSmallIntegerField(default=1)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.room_type.name})"

    def is_available(self, start_date, end_date):
        """Check if room is available for the given date range"""
        # Check if there are any bookings for this room that overlap with the date range
        overlapping_bookings = self.bookings.filter(
            booking__start_date__lt=end_date,
            booking__end_date__gt=start_date,
            booking__status__in=['pending', 'confirmed', 'checked_in']
        ).exists()

        return not overlapping_bookings


class RoomMaintenance(BaseAuditModel):
    """
    TASK-032: Model to track room maintenance schedules.
    Prevents rooms from being booked during maintenance periods.
    """

    class MaintenanceType(models.TextChoices):
        ROUTINE = 'routine', 'Плановое обслуживание'
        DEEP_CLEANING = 'deep_cleaning', 'Глубокая уборка'
        REPAIR = 'repair', 'Ремонт'
        INSPECTION = 'inspection', 'Проверка'
        RENOVATION = 'renovation', 'Ремонт помещения'
        OTHER = 'other', 'Другое'

    class MaintenanceStatus(models.TextChoices):
        SCHEDULED = 'scheduled', 'Запланировано'
        IN_PROGRESS = 'in_progress', 'В процессе'
        COMPLETED = 'completed', 'Завершено'
        CANCELLED = 'cancelled', 'Отменено'

    room = models.ForeignKey(
        Room,
        on_delete=models.CASCADE,
        related_name='maintenance_records',
        help_text="Комната, находящаяся на обслуживании",
        db_index=True
    )

    maintenance_type = models.CharField(
        max_length=20,
        choices=MaintenanceType.choices,
        help_text="Тип обслуживания",
        db_index=True
    )

    status = models.CharField(
        max_length=20,
        choices=MaintenanceStatus.choices,
        default=MaintenanceStatus.SCHEDULED,
        help_text="Статус обслуживания",
        db_index=True
    )

    start_date = models.DateTimeField(
        help_text="Начало обслуживания",
        db_index=True
    )

    end_date = models.DateTimeField(
        help_text="Окончание обслуживания",
        db_index=True
    )

    description = models.TextField(
        blank=True,
        null=True,
        help_text="Описание работ по обслуживанию"
    )

    assigned_to = models.ForeignKey(
        'Account',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='room_maintenance_assignments',
        help_text="Сотрудник, назначенный на обслуживание"
    )

    estimated_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Расчетная стоимость обслуживания"
    )

    actual_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Фактическая стоимость обслуживания"
    )

    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Когда обслуживание было завершено"
    )

    completion_notes = models.TextField(
        blank=True,
        null=True,
        help_text="Примечания о завершении обслуживания"
    )

    class Meta:
        ordering = ['-start_date']
        verbose_name = 'Room Maintenance'
        verbose_name_plural = 'Room Maintenance Records'
        indexes = [
            models.Index(fields=['room', 'start_date', 'end_date'], name='idx_maintenance_room_dates'),
            models.Index(fields=['status', 'start_date'], name='idx_maintenance_status_date'),
            models.Index(fields=['maintenance_type'], name='idx_maintenance_type'),
        ]

    def __str__(self):
        return f"{self.room.name} - {self.get_maintenance_type_display()} ({self.start_date.strftime('%Y-%m-%d')} - {self.end_date.strftime('%Y-%m-%d')})"

    def clean(self):
        """Validate that end_date is after start_date"""
        from django.core.exceptions import ValidationError
        if self.start_date and self.end_date and self.end_date <= self.start_date:
            raise ValidationError('End date must be after start date')

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def mark_in_progress(self):
        """Mark maintenance as in progress"""
        self.status = self.MaintenanceStatus.IN_PROGRESS
        self.save(update_fields=['status', 'updated_at'])

    def mark_completed(self, completion_notes=None, actual_cost=None):
        """
        Mark maintenance as completed.

        Args:
            completion_notes: Notes about the completion
            actual_cost: Actual cost incurred
        """
        self.status = self.MaintenanceStatus.COMPLETED
        self.completed_at = timezone.now()
        if completion_notes:
            self.completion_notes = completion_notes
        if actual_cost is not None:
            self.actual_cost = actual_cost
        self.save(update_fields=['status', 'completed_at', 'completion_notes', 'actual_cost', 'updated_at'])

    def cancel(self, reason=None):
        """
        Cancel the maintenance.

        Args:
            reason: Reason for cancellation
        """
        self.status = self.MaintenanceStatus.CANCELLED
        if reason:
            self.completion_notes = f"Cancelled: {reason}"
        self.save(update_fields=['status', 'completion_notes', 'updated_at'])

    @property
    def is_active(self):
        """Check if maintenance is currently active (scheduled or in progress)"""
        return self.status in [self.MaintenanceStatus.SCHEDULED, self.MaintenanceStatus.IN_PROGRESS]

    @property
    def is_current(self):
        """Check if maintenance is currently ongoing"""
        now = timezone.now()
        return (
            self.is_active and
            self.start_date <= now <= self.end_date
        )

    @property
    def status_color(self):
        """Return Bootstrap color class for status display"""
        color_mapping = {
            self.MaintenanceStatus.SCHEDULED: 'info',
            self.MaintenanceStatus.IN_PROGRESS: 'warning',
            self.MaintenanceStatus.COMPLETED: 'success',
            self.MaintenanceStatus.CANCELLED: 'danger',
        }
        return color_mapping.get(self.status, 'secondary')

    @classmethod
    def get_active_maintenance_for_room(cls, room, start_date, end_date):
        """
        Get active maintenance records for a room within a date range.

        Args:
            room: Room instance
            start_date: Start of date range
            end_date: End of date range

        Returns:
            QuerySet of RoomMaintenance records
        """
        return cls.objects.filter(
            room=room,
            status__in=[cls.MaintenanceStatus.SCHEDULED, cls.MaintenanceStatus.IN_PROGRESS],
            start_date__lt=end_date,
            end_date__gt=start_date
        )

    @classmethod
    def is_room_under_maintenance(cls, room, start_date, end_date):
        """
        Check if a room is under maintenance during a date range.

        Args:
            room: Room instance
            start_date: Start of date range
            end_date: End of date range

        Returns:
            Boolean
        """
        return cls.get_active_maintenance_for_room(room, start_date, end_date).exists()
