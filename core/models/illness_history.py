import uuid
from django.db import models
from core.models import BaseAuditModel, PatientModel, Booking, Account


# Supporting models that should be added first
class ProfessionModel(BaseAuditModel):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


class ToxicFactorModel(BaseAuditModel):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


class TagModel(BaseAuditModel):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class DiagnosisTemplate(BaseAuditModel):
    code = models.CharField(max_length=50)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.code} - {self.name}"


# Main illness history model
class IllnessHistory(BaseAuditModel):
    TYPES = (
        ('stationary', 'Стационарный'),
        ('ambulatory', 'Амбулаторный'),
    )
    STATES = (
        ('registration', 'Регистрация'),
        ('open', 'Открыт'),
        ('closed', 'Закрыт'),
    )

    series_number = models.CharField(max_length=255, default=uuid.uuid4)
    patient = models.ForeignKey(PatientModel, on_delete=models.CASCADE, related_name='illness_histories')
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='illness_histories')
    type = models.CharField(choices=TYPES, max_length=15, default='stationary')
    is_sick_leave = models.BooleanField(default=False, null=True, blank=True)

    profession = models.ForeignKey(ProfessionModel, on_delete=models.SET_NULL, null=True, blank=True)
    toxic_factors = models.ManyToManyField(ToxicFactorModel, blank=True)
    tags = models.ForeignKey(TagModel, on_delete=models.SET_NULL, null=True, blank=True)
    state = models.CharField(choices=STATES, default="registration", max_length=100)

    initial_diagnosis = models.ForeignKey(
        DiagnosisTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='initial_histories'
    )
    at_arrival_diagnosis = models.ForeignKey(
        DiagnosisTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='arrival_histories'
    )
    diagnosis = models.ForeignKey(
        DiagnosisTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='final_histories'
    )

    # Since NurseAccountModel and DoctorAccountModel don't exist, use Account with is_therapist field
    nurses = models.ManyToManyField(
        Account,
        blank=True,
        related_name='nurse_histories'
    )
    doctor = models.ForeignKey(
        Account,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='doctor_histories'
    )

    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"История болезни {self.series_number} - {self.patient.full_name}"

    class Meta:
        verbose_name = "История болезни"
        verbose_name_plural = "Истории болезней"

