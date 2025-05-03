from django.db import models
from django.utils import timezone

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
        return f"{self.medication.name} {self.dosage} {self.frequency} ({self.get_status_display()})"

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


class MedicationAdministration(BaseAuditModel):
    prescribed_medication = models.ForeignKey('PrescribedMedication', on_delete=models.CASCADE,
                                              related_name='administrations')
    administered_at = models.DateTimeField()
    administered_by = models.ForeignKey('Account', on_delete=models.SET_NULL, null=True,
                                        related_name='administered_medications')

    # Details
    dosage_given = models.CharField(max_length=50)
    notes = models.TextField(blank=True)

    # Patient response
    patient_response = models.TextField(blank=True, help_text="How patient responded to medication")
    side_effects = models.TextField(blank=True)

    class Meta:
        ordering = ['-administered_at']

    def __str__(self):
        return f"{self.prescribed_medication.medication.name} administered on {self.administered_at.strftime('%Y-%m-%d %H:%M')}"