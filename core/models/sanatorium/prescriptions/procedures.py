import datetime
from datetime import timedelta

from django.db import models
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone

from core.models import BaseAuditModel, IllnessHistory, Service, Account


class ProcedureServiceModel(BaseAuditModel):
    STATE_CHOICES = (
        ('recommended', 'Рекомендовано'),
        ('assigned', 'Назначено'),
        ('cancelled', 'Отменено'),
        ('stopped', 'Остановлено'),
        ('dispatched', 'Отправлено'),
    )
    FREQUENCY_CHOICES = (
        ("каждый день", "каждый день"),
        ("через день", "через день"),
    )

    illness_history = models.ForeignKey(IllnessHistory, on_delete=models.CASCADE, null=True, blank=True,
                                        related_name='assigned_procedures')
    medical_service = models.ForeignKey(Service, on_delete=models.SET_NULL, null=True)

    therapist = models.ForeignKey(Account, blank=True, null=True, on_delete=models.SET_NULL, related_name='therapist')
    state = models.CharField(choices=STATE_CHOICES, default='assigned', max_length=50)

    quantity = models.IntegerField(default=1)
    proceeded_sessions = models.IntegerField(default=0, null=True, blank=True)

    start_date = models.DateField(null=True)
    frequency = models.CharField(choices=FREQUENCY_CHOICES, default='каждый день', max_length=50)
    comments = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.illness_history.series_number} - {self.medical_service.name}"

    @property
    def progres_percentile(self):
        return int(self.proceeded_sessions / self.quantity * 100)

    @property
    def remaining_quantity(self):
        return int(self.quantity - self.proceeded_sessions)

    def _is_out_of_graphic(self, start_at: datetime) -> bool:
        """
        Determines if the given start date is out of the booking end date.
        """
        return start_at.date() > self.illness_history.booking.end_date

    class Meta:
        verbose_name = 'Основной лист назначений | Процедуры'
        verbose_name_plural = 'Основной лист назначений | Процедуры'


class IndividualProcedureSessionModel(BaseAuditModel):
    """Model for tracking individual therapy sessions"""

    STATUS_CHOICES = (
        ('pending', 'Ожидает'),
        ('completed', 'Проведен'),
        ('canceled', 'Отменен'),
        ('conflicted', 'конфликтный'),
    )

    assigned_procedure = models.ForeignKey(
        ProcedureServiceModel, on_delete=models.CASCADE,
        related_name='individual_sessions', verbose_name='Бронирование'
    )

    session_number = models.PositiveIntegerField(verbose_name='Номер сеанса')

    status = models.CharField(max_length=20, choices=STATUS_CHOICES,
                              default='pending', verbose_name='Статус')

    therapist = models.ForeignKey(
        Account, on_delete=models.SET_NULL, related_name='conducted_sessions',
        null=True, blank=True, verbose_name='Массажист'
    )
    scheduled_to = models.DateTimeField(null=True, blank=True,
                                        verbose_name='Дата ')
    completed_at = models.DateTimeField(null=True, blank=True,
                                        verbose_name='Дата проведения')

    notes = models.TextField(blank=True, null=True, verbose_name='Примечания')

    class Meta:
        ordering = ['session_number']
        unique_together = ['assigned_procedure', 'session_number', 'id']  # Ensure no duplicate session numbers

        verbose_name = 'Основной лист назначений | Индивидуальный сеанс'
        verbose_name_plural = 'Основной лист назначений | Индивидуальные сеансы'

    def __str__(self):
        return f"{self.assigned_procedure.illness_history} - Сеанс #{self.session_number}"


# Store original values before save to compare in post_save
# Store original values before save to compare in post_save
@receiver(pre_save, sender=ProcedureServiceModel)
def store_original_values(sender, instance, **kwargs):
    """Store original values before save to compare in post_save"""
    if instance.pk:
        try:
            original = ProcedureServiceModel.objects.get(pk=instance.pk)
            instance._original_quantity = original.quantity
            instance._original_start_date = original.start_date
            instance._original_frequency = original.frequency
        except ProcedureServiceModel.DoesNotExist:
            pass


@receiver(post_save, sender=ProcedureServiceModel)
def create_individual_sessions(sender, instance, created, **kwargs):
    """
    Signal to create or update individual sessions when a procedure service is saved
    """
    # Get current number of individual sessions
    current_sessions = instance.individual_sessions.count()

    # Get the booking end date for conflict checking
    booking_end_date = instance.illness_history.booking.end_date if instance.illness_history.booking else None

    # If this is a new procedure service, create all sessions
    if created:
        for i in range(1, instance.quantity + 1):
            # Calculate scheduled time based on frequency
            scheduled_time = None
            status = 'pending'

            if instance.start_date:
                if instance.frequency == "каждый день":
                    scheduled_date = instance.start_date + timedelta(days=i - 1)
                elif instance.frequency == "через день":
                    scheduled_date = instance.start_date + timedelta(days=(i - 1) * 2)
                else:
                    scheduled_date = None

                # Default time is 10:00 AM if only date is provided
                if scheduled_date:
                    scheduled_time = datetime.datetime.combine(
                        scheduled_date,
                        datetime.datetime.strptime("10:00", "%H:%M").time()
                    )
                    # Make timezone-aware if needed
                    if timezone.is_naive(scheduled_time):
                        scheduled_time = timezone.make_aware(scheduled_time)

                # Check if scheduled date is beyond booking end date
                if scheduled_time and booking_end_date:
                    # Convert both to date objects for comparison
                    scheduled_date = scheduled_time.date()
                    end_date = booking_end_date
                    if isinstance(booking_end_date, datetime.datetime):
                        end_date = booking_end_date.date()

                    if scheduled_date > end_date:
                        status = 'conflicted'

            IndividualProcedureSessionModel.objects.create(
                assigned_procedure=instance,
                session_number=i,
                therapist=instance.therapist,
                status=status,
                scheduled_to=scheduled_time
            )

        # Update proceeded_sessions to 0 (should already be 0, but just in case)
        instance.proceeded_sessions = 0
        instance.save(update_fields=['proceeded_sessions'])
        return

    # Handle existing procedure with changed quantity
    if hasattr(instance, '_original_quantity') and instance._original_quantity != instance.quantity:
        # If quantity increased, add new sessions
        if instance.quantity > instance._original_quantity:
            for i in range(instance._original_quantity + 1, instance.quantity + 1):
                # Calculate scheduled time for new sessions
                scheduled_time = None
                status = 'pending'

                if instance.start_date:
                    if instance.frequency == "каждый день":
                        scheduled_date = instance.start_date + timedelta(days=i - 1)
                    elif instance.frequency == "через день":
                        scheduled_date = instance.start_date + timedelta(days=(i - 1) * 2)
                    else:
                        scheduled_date = None

                    if scheduled_date:
                        scheduled_time = datetime.datetime.combine(
                            scheduled_date,
                            datetime.datetime.strptime("10:00", "%H:%M").time()
                        )
                        if timezone.is_naive(scheduled_time):
                            scheduled_time = timezone.make_aware(scheduled_time)

                    # Check if scheduled date is beyond booking end date
                    if scheduled_time and booking_end_date:
                        # Convert both to date objects for comparison
                        scheduled_date = scheduled_time.date()
                        end_date = booking_end_date
                        if isinstance(booking_end_date, datetime.datetime):
                            end_date = booking_end_date.date()

                        if scheduled_date > end_date:
                            status = 'conflicted'

                IndividualProcedureSessionModel.objects.create(
                    assigned_procedure=instance,
                    session_number=i,
                    therapist=instance.therapist,
                    status=status,
                    scheduled_to=scheduled_time
                )

        # If quantity decreased, remove excess sessions
        elif instance.quantity < instance._original_quantity:
            # Only remove sessions that haven't been completed
            for session in instance.individual_sessions.filter(
                    session_number__gt=instance.quantity
            ).order_by('-session_number'):
                if session.status != 'completed':
                    session.delete()
                else:
                    # If a completed session would be removed, adjust quantity to keep it
                    if instance.quantity < session.session_number:
                        instance.quantity = session.session_number
                        instance.save(update_fields=['quantity'])
                        break

    # If start_date or frequency changed, update scheduled times
    if (hasattr(instance, '_original_start_date') and instance._original_start_date != instance.start_date) or \
            (hasattr(instance, '_original_frequency') and instance._original_frequency != instance.frequency):

        for session in instance.individual_sessions.all():
            # Only reschedule pending sessions
            if session.status not in ['completed', 'canceled']:
                scheduled_time = None
                status = session.status

                if instance.start_date:
                    if instance.frequency == "каждый день":
                        scheduled_date = instance.start_date + timedelta(days=session.session_number - 1)
                    elif instance.frequency == "через день":
                        scheduled_date = instance.start_date + timedelta(days=(session.session_number - 1) * 2)
                    else:
                        scheduled_date = None

                    if scheduled_date:
                        # Preserve the time if it exists, otherwise default to 10:00
                        if session.scheduled_to:
                            old_time = session.scheduled_to.time()
                        else:
                            old_time = datetime.datetime.strptime("10:00", "%H:%M").time()

                        scheduled_time = datetime.datetime.combine(scheduled_date, old_time)
                        if timezone.is_naive(scheduled_time):
                            scheduled_time = timezone.make_aware(scheduled_time)

                    # Check if scheduled date is beyond booking end date
                    if scheduled_time and booking_end_date:
                        # Convert both to date objects for comparison
                        scheduled_date = scheduled_time.date()
                        end_date = booking_end_date
                        if isinstance(booking_end_date, datetime.datetime):
                            end_date = booking_end_date.date()

                        if scheduled_date > end_date:
                            status = 'conflicted'
                        elif status == 'conflicted':
                            # If it was conflicted before but now it's not, change to pending
                            if scheduled_date <= end_date:
                                status = 'pending'

                session.scheduled_to = scheduled_time
                session.status = status
                session.save(update_fields=['scheduled_to', 'status'])

    # Sync proceeded_sessions count with completed individual sessions
    completed_count = instance.individual_sessions.filter(status='completed').count()
    if instance.proceeded_sessions != completed_count:
        instance.proceeded_sessions = completed_count
        instance.save(update_fields=['proceeded_sessions'])


# Signal for updating proceeded_sessions when an individual session is saved
@receiver(post_save, sender=IndividualProcedureSessionModel)
def update_booking_proceeded_sessions(sender, instance, created=False, **kwargs):
    """
    Update the proceeded_sessions count in the procedure model
    when an individual session is saved
    """
    # If status changed to completed, set completed_at time
    if instance.status == 'completed' and not instance.completed_at:
        instance.completed_at = timezone.now()
        instance.save(update_fields=['completed_at'])

    # Get the procedure
    procedure = instance.assigned_procedure

    # Calculate the new count of completed sessions
    completed_count = procedure.individual_sessions.filter(status='completed').count()

    # Update the procedure's proceeded_sessions field if it's different
    if procedure.proceeded_sessions != completed_count:
        procedure.proceeded_sessions = completed_count
        # Use update_fields to avoid triggering other signals
        procedure.save(update_fields=['proceeded_sessions'])