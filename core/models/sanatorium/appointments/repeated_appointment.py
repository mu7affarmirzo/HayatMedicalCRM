from django.db import models
from core.models import BaseAuditModel, STATE_CHOICES, Account, IllnessHistory, DiagnosisTemplate


class RepeatedAppointmentWithDoctorModel(BaseAuditModel):
    class Meta:
        verbose_name = "Appointment | Повторный приём у врача"
        verbose_name_plural = "Appointment | Повторные приёмы у врачей"

    state = models.CharField(choices=STATE_CHOICES, max_length=250, default='Приём завершён')

    doctor = models.ForeignKey(Account, on_delete=models.CASCADE, null=True)
    illness_history = models.ForeignKey(
        IllnessHistory, on_delete=models.CASCADE,
        null=True, related_name='repeated_appointment'
    )

    complaint = models.TextField(null=True, blank=True)
    objective_data = models.TextField(null=True, blank=True)

    arterial_high_low = models.CharField(max_length=255, null=True, blank=True)
    arterial_high = models.IntegerField(null=True)
    arterial_low = models.IntegerField(null=True)
    imt = models.CharField(max_length=255, null=True, blank=True)

    diagnosis = models.ForeignKey(DiagnosisTemplate, null=True, on_delete=models.SET_NULL)
    cito = models.BooleanField(default=False)
    summary = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.id}"

