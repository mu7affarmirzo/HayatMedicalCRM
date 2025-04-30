from django.db import models
from core.models import BaseAuditModel, STATE_CHOICES, Account, IllnessHistory, DiagnosisTemplate


class EkgAppointmentModel(BaseAuditModel):
    class Meta:
        verbose_name = "Appointment | Приём на ЭКГ"
        verbose_name_plural = "Appointment | Приёмы на ЭКГ"


    AXIS_CHOICES = (
        ('N', 'N'),
        ('горизонтальная', 'горизонтальная'),
        ('вертикальная', 'вертикальная'),
        ('отклонена влево', 'отклонена влево'),
        ('отклонена вправо', 'отклонена вправо')
    )

    ST_CHOICES = (
        ('Показан', 'Показан'),
        ('Не показан', 'Не показан'),
        ('Противопоказан', 'Противопоказан'),
    )

    state = models.CharField(choices=STATE_CHOICES, max_length=250, default='Приём завершён')

    doctor = models.ForeignKey(Account, on_delete=models.CASCADE, null=True)
    illness_history = models.ForeignKey(
        IllnessHistory, on_delete=models.CASCADE,
        null=True, related_name='ekg_app'
    )

    rhythm = models.CharField(max_length=250, null=True, blank=True)
    heart_s_count = models.IntegerField(null=True, blank=True)
    r_r = models.FloatField(null=True, blank=True)
    p_q = models.FloatField(null=True, blank=True)
    qrs = models.FloatField(null=True, blank=True)
    v1 = models.FloatField(null=True, blank=True)
    v6 = models.FloatField(null=True, blank=True)
    q_t = models.FloatField(null=True, blank=True)
    la = models.FloatField(null=True, blank=True)

    prong_p = models.CharField(max_length=250, null=True, blank=True)
    complex_qrs = models.CharField(max_length=250, null=True, blank=True)
    prong_t = models.CharField(max_length=250, null=True, blank=True)
    segment_st = models.CharField(max_length=250, null=True, blank=True)
    electric_axis = models.CharField(choices=AXIS_CHOICES, max_length=250, null=True, blank=True)

    cito = models.BooleanField(default=False)
    diagnosis = models.ForeignKey(DiagnosisTemplate, null=True, on_delete=models.SET_NULL)
    for_sanatorium_treatment = models.CharField(choices=ST_CHOICES, max_length=250, null=True, blank=True)
    objective_data = models.TextField(null=True, blank=True)

    summary = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.id}"

