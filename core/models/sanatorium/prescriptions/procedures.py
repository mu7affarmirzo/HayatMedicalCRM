import datetime

from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

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

    illness_history = models.ForeignKey(IllnessHistory, on_delete=models.CASCADE, null=True, blank=True, related_name='assigned_procedures')
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
        return int(self.proceeded_sessions / self.quantity*100)

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

    completed_at = models.DateTimeField(null=True, blank=True,
                                        verbose_name='Дата проведения')

    notes = models.TextField(blank=True, null=True, verbose_name='Примечания')

    class Meta:
        ordering = ['session_number']
        unique_together = ['assigned_procedure', 'session_number']  # Ensure no duplicate session numbers

        verbose_name = 'Основной лист назначений | Индивидуальный сеанс'
        verbose_name_plural = 'Основной лист назначений | Индивидуальные сеансы'

    def __str__(self):
        return f"{self.assigned_procedure.illness_history} - Сеанс #{self.session_number}"


@receiver(post_save, sender=ProcedureServiceModel)
def create_individual_sessions(sender, instance, created, **kwargs):
    """
    Signal to create or update individual sessions when a booking is saved
    """

    # Get current number of individual sessions
    current_sessions = instance.individual_sessions.count()

    # If this is a new booking, create all sessions
    if created:
        for i in range(1, instance.quantity + 1):
            IndividualProcedureSessionModel.objects.create(
                assigned_procedure=instance,
                session_number=i,
                therapist=instance.therapist,
                status='pending'
            )
        # Update proceeded_sessions to 0 (should already be 0, but just in case)
        instance.proceeded_sessions = 0
        instance.save(update_fields=['proceeded_sessions'])
        return

    # Handle existing booking with changed quantity
    if hasattr(instance, '_original_quantity') and instance._original_quantity != instance.quantity:
        # If quantity increased, add new sessions
        if instance.quantity > instance._original_quantity:
            for i in range(instance._original_quantity + 1, instance.quantity + 1):
                IndividualProcedureSessionModel.objects.create(
                    booking=instance,
                    session_number=i,
                    therapist=instance.therapist,
                    status='pending'
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

    # Sync proceeded_sessions count with completed individual sessions
    completed_count = instance.proceeded_sessions
    if instance.proceeded_sessions != completed_count:
        instance.proceeded_sessions = completed_count
        instance.save(update_fields=['proceeded_sessions'])


# Signal for updating proceeded_sessions when an individual session is saved
@receiver(post_save, sender=IndividualProcedureSessionModel)
def update_booking_proceeded_sessions(sender, instance, **kwargs):
    """
    Update the proceeded_sessions count in the booking model
    when an individual session is saved
    """
    # Get the booking
    booking = instance.assigned_procedure

    # Calculate the new count of completed sessions
    completed_count = booking.individual_sessions.filter(status='completed').count()

    # Update the booking's proceeded_sessions field if it's different
    if booking.proceeded_sessions != completed_count:
        booking.proceeded_sessions = completed_count
        # Use update_fields to avoid triggering other signals
        booking.save(update_fields=['proceeded_sessions'])
