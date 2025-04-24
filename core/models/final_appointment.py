from django.db import models
from core.models import BaseAuditModel, STATE_CHOICES, Account, IllnessHistory, DiagnosisTemplate, upload_location


class FinalAppointmentWithDoctorModel(BaseAuditModel):
    class Meta:
        verbose_name = "Appointment | Заключительный приём у врача"
        verbose_name_plural = "Appointment | Заключительные приёмы у врачей"

    RESULT_CHOICES = (
        ('Улучение', 'Улучение'),
        ('Без изменения', 'Без изменения'),
        ('Ухудшение', 'Ухудшение'),
    )
    state = models.CharField(choices=STATE_CHOICES, max_length=250, default='Приём завершён')

    doctor = models.ForeignKey(Account, on_delete=models.CASCADE, null=True)
    illness_history = models.ForeignKey(
        IllnessHistory, on_delete=models.CASCADE,
        null=True, related_name='final_appointment'
    )

    objective_status = models.TextField(null=True, blank=True)
    file = models.FileField(upload_to=upload_location, null=True, blank=True)

    height = models.FloatField(null=True, blank=True)
    weight = models.FloatField(null=True, blank=True)
    heart_beat = models.IntegerField(null=True, blank=True)
    arterial_high_low = models.CharField(max_length=255, null=True, blank=True)
    arterial_high = models.IntegerField(null=True, blank=True)
    arterial_low = models.IntegerField(null=True, blank=True)
    imt = models.FloatField(null=True, blank=True)
    imt_interpretation = models.FloatField(null=True, blank=True)

    diagnosis = models.ManyToManyField(DiagnosisTemplate)
    summary = models.TextField(blank=True, null=True)

    treatment_results = models.CharField(choices=RESULT_CHOICES, max_length=250, default='Улучение')

    def __str__(self):
        return f"{self.id}"

