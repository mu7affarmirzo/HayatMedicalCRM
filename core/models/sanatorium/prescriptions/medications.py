from django.db import models
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver
from datetime import datetime, time, timedelta

from core.models import BaseAuditModel


class PrescribedMedication(BaseAuditModel):
    FREQUENCY_CHOICES = [
        ('once', 'Однократно'),
        ('daily', 'Ежедневно'),
        ('bid', 'Два раза в день'),
        ('tid', 'Три раза в день'),
        ('qid', 'Четыре раза в день'),
        ('qhs', 'Перед сном'),
        ('q4h', 'Каждые 4 часа'),
        ('q6h', 'Каждые 6 часов'),
        ('q8h', 'Каждые 8 часов'),
        ('q12h', 'Каждые 12 часов'),
        ('weekly', 'Еженедельно'),
        ('biweekly', 'Два раза в неделю'),
        ('monthly', 'Ежемесячно'),
        ('prn', 'По необходимости'),
    ]

    STATUS_CHOICES = [
        ('recommended', 'Рекомендовано'),
        ('prescribed', 'Назначено'),
        ('active', 'Активно'),
        ('completed', 'Завершено'),
        ('discontinued', 'Прекращено'),
    ]

    illness_history = models.ForeignKey('IllnessHistory', on_delete=models.CASCADE,
                                        related_name='prescribed_medications')
    medication = models.ForeignKey('MedicationsInStockModel', on_delete=models.PROTECT,
                                   related_name='prescriptions')

    # Prescription details
    dosage = models.CharField(max_length=50, help_text="Dose amount (e.g., '500mg', '2 tablets')")
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES)
    route = models.CharField(max_length=50, blank=True,
                             help_text="Route of administration (e.g., oral, IV, topical)")

    # Duration
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    duration_days = models.PositiveIntegerField(null=True, blank=True,
                                                help_text="Duration in days (optional)")

    # Status tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='prescribed')
    is_prn = models.BooleanField(default=False, help_text="Medication to be taken as needed")

    # Special instructions
    instructions = models.TextField(blank=True,
                                    help_text="Special instructions for administration")
    reason = models.TextField(blank=True, help_text="Reason for prescription")

    # Audit fields
    prescribed_by = models.ForeignKey('Account', on_delete=models.SET_NULL, null=True,
                                      related_name='prescribed_medications')
    prescribed_at = models.DateTimeField(auto_now_add=True)
    last_modified_by = models.ForeignKey('Account', on_delete=models.SET_NULL, null=True,
                                         related_name='modified_prescriptions')

    class Meta:
        ordering = ['-prescribed_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['start_date']),
            models.Index(fields=['end_date']),
        ]

    def __str__(self):
        return f"{self.medication.item.name} {self.dosage} {self.frequency} ({self.get_status_display()})"

    @property
    def is_active(self):
        """Check if prescription is currently active"""
        today = timezone.now().date()
        if self.status != 'active':
            return False
        if self.end_date and self.end_date < today:
            return False
        return self.start_date <= today

    def save(self, *args, **kwargs):
        # Calculate end_date from duration_days if provided
        if not self.end_date and self.duration_days:
            self.end_date = self.start_date + timezone.timedelta(days=self.duration_days)
        super().save(*args, **kwargs)


class MedicationSession(BaseAuditModel):
    STATUS_CHOICES = [
        ('pending', 'Ожидает выдачи'),
        ('administered', 'Выдано'),
        ('missed', 'Пропущено'),
        ('refused', 'Отказано'),
        ('canceled', 'Отменено'),
    ]

    prescribed_medication = models.ForeignKey('PrescribedMedication', on_delete=models.CASCADE,
                                              related_name='sessions')

    # Session details
    session_datetime = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    # Simple notes field for any relevant information
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['session_datetime']
        indexes = [
            models.Index(fields=['session_datetime']),
            models.Index(fields=['status']),
            models.Index(fields=['prescribed_medication', 'session_datetime']),
        ]

    def __str__(self):
        return f"{self.prescribed_medication} - {self.session_datetime.strftime('%Y-%m-%d %H:%M')}"

    def administer(self, nurse):
        """Mark session as administered"""
        self.status = 'administered'
        self.administered_by = nurse
        self.administered_at = timezone.now()
        self.save()

    def mark_missed(self):
        """Mark session as missed"""
        self.status = 'missed'
        self.save()

    def mark_refused(self, notes=""):
        """Mark session as refused by patient"""
        self.status = 'refused'
        if notes:
            self.notes = notes
        self.save()

    def cancel(self, notes=""):
        """Cancel this session"""
        self.status = 'canceled'
        if notes:
            self.notes = notes
        self.save()


@receiver(post_save, sender=PrescribedMedication)
def create_medication_sessions(sender, instance, created, **kwargs):
    """
    Signal handler to create medication sessions when a new medication is prescribed
    """
    if not created or instance.is_prn:
        # Skip if this is an update or a PRN medication
        return

    # Define times for each frequency
    times_by_frequency = {
        'once': [time(9, 0)],  # One time at 9 AM
        'daily': [time(9, 0)],  # Once a day at 9 AM
        'bid': [time(9, 0), time(21, 0)],  # Twice a day at 9 AM and 9 PM
        'tid': [time(9, 0), time(14, 0), time(21, 0)],  # Three times a day
        'qid': [time(8, 0), time(12, 0), time(16, 0), time(20, 0)],  # Four times a day
        'qhs': [time(21, 0)],  # Once at bedtime
        'q4h': [time(0, 0), time(4, 0), time(8, 0), time(12, 0), time(16, 0), time(20, 0)],
        'q6h': [time(0, 0), time(6, 0), time(12, 0), time(18, 0)],
        'q8h': [time(6, 0), time(14, 0), time(22, 0)],
        'q12h': [time(8, 0), time(20, 0)],
        'weekly': [time(9, 0)],  # Once a week
        'biweekly': [time(9, 0)],  # Twice a week
        'monthly': [time(9, 0)],  # Once a month
    }

    # Get administration times for this frequency
    admin_times = times_by_frequency.get(instance.frequency, [time(9, 0)])

    # Calculate end date
    end_date = instance.end_date
    if not end_date and instance.duration_days:
        end_date = instance.start_date + timedelta(days=instance.duration_days)
    elif not end_date:
        # Default to 7 days if no end date and no duration specified
        end_date = instance.start_date + timedelta(days=7)

    # Generate sessions based on frequency
    current_date = instance.start_date
    sessions_to_create = []

    # Handle special frequencies
    if instance.frequency == 'weekly':
        # Create a session for each week
        while current_date <= end_date:
            for admin_time in admin_times:
                session_datetime = datetime.combine(current_date, admin_time)
                if timezone.is_naive(session_datetime):
                    session_datetime = timezone.make_aware(session_datetime)

                sessions_to_create.append(
                    MedicationSession(
                        prescribed_medication=instance,
                        session_datetime=session_datetime
                    )
                )
            current_date += timedelta(days=7)

    elif instance.frequency == 'biweekly':
        # Create sessions twice a week (Monday and Thursday)
        while current_date <= end_date:
            # Find the next Monday and Thursday
            days_to_monday = (0 - current_date.weekday()) % 7
            monday = current_date + timedelta(days=days_to_monday)
            thursday = monday + timedelta(days=3)

            # Create Monday session if it's within the range
            if monday <= end_date:
                for admin_time in admin_times:
                    session_datetime = datetime.combine(monday, admin_time)
                    if timezone.is_naive(session_datetime):
                        session_datetime = timezone.make_aware(session_datetime)

                    sessions_to_create.append(
                        MedicationSession(
                            prescribed_medication=instance,
                            session_datetime=session_datetime
                        )
                    )

            # Create Thursday session if it's within the range
            if thursday <= end_date:
                for admin_time in admin_times:
                    session_datetime = datetime.combine(thursday, admin_time)
                    if timezone.is_naive(session_datetime):
                        session_datetime = timezone.make_aware(session_datetime)

                    sessions_to_create.append(
                        MedicationSession(
                            prescribed_medication=instance,
                            session_datetime=session_datetime
                        )
                    )

            # Move to the next week
            current_date = monday + timedelta(days=7)

    elif instance.frequency == 'monthly':
        # Create a session for each month
        while current_date <= end_date:
            for admin_time in admin_times:
                session_datetime = datetime.combine(current_date, admin_time)
                if timezone.is_naive(session_datetime):
                    session_datetime = timezone.make_aware(session_datetime)

                sessions_to_create.append(
                    MedicationSession(
                        prescribed_medication=instance,
                        session_datetime=session_datetime
                    )
                )

            # Move to next month
            month = current_date.month + 1
            year = current_date.year
            if month > 12:
                month = 1
                year += 1

            # Handle month length differences
            try:
                current_date = current_date.replace(year=year, month=month)
            except ValueError:
                # Handle February edge cases
                import calendar
                last_day = calendar.monthrange(year, month)[1]
                current_date = current_date.replace(year=year, month=month, day=min(current_date.day, last_day))

    else:
        # Handle daily frequencies
        while current_date <= end_date:
            for admin_time in admin_times:
                session_datetime = datetime.combine(current_date, admin_time)
                if timezone.is_naive(session_datetime):
                    session_datetime = timezone.make_aware(session_datetime)

                sessions_to_create.append(
                    MedicationSession(
                        prescribed_medication=instance,
                        session_datetime=session_datetime
                    )
                )

            # Move to next day
            current_date += timedelta(days=1)

    # Bulk create all sessions
    if sessions_to_create:
        MedicationSession.objects.bulk_create(sessions_to_create)

