from django.db import models
from core.models import BaseAuditModel, STATE_CHOICES, Account, IllnessHistory


class AppointmentWithOnDutyDoctorOnArrivalModel(BaseAuditModel):
    class Meta:
        verbose_name = "Appointment | Приём у дежурного врача по прибытии"
        verbose_name_plural = "Appointment | Приёмы у дежурного врача по прибытии"

    ST_CHOICES = (
        ('Показан', 'Показан'),
        ('Не показан', 'Не показан'),
        ('Противопоказан', 'Противопоказан'),
    )
    PULSE_CHOICES = (
        ('ритмичный', 'ритмичный'),
        ('аритмичный', 'аритмичный'),
    )
    REGIME_CHOICES = (
        ('Щадящий', 'Щадящий'),
        ('Постельный', 'Постельный'),
        ('Тонизирующий', 'Тонизирующий'),
        ('Тренирующий', 'Тренирующий'),
    )
    state = models.CharField(choices=STATE_CHOICES, max_length=250, default='Приём завершён')

    doctor = models.ForeignKey(Account, on_delete=models.CASCADE, null=True)
    illness_history = models.ForeignKey(
        IllnessHistory, on_delete=models.CASCADE,
        null=True, related_name='on_duty_doctor_on_arr_appointment'
    )
    complaints = models.TextField(null=True, blank=True)
    arv_number = models.CharField(null=True, blank=True, max_length=255)
    ayes_shells = models.CharField(null=True, blank=True, max_length=255)
    from_to_sanatorium = models.CharField(null=True, blank=True, max_length=255)
    road_crossed = models.CharField(null=True, blank=True, max_length=255)

    abroad_for_last_years = models.CharField(null=True, blank=True, max_length=255)
    virus_hepatitis = models.CharField(null=True, blank=True, max_length=255)
    tuberculosis = models.CharField(null=True, blank=True, max_length=255)
    malarias = models.CharField(null=True, blank=True, max_length=255)
    venerian_illness = models.CharField(null=True, blank=True, max_length=255)
    dizanteri = models.CharField(null=True, blank=True, max_length=255)
    helminthic_infestations = models.CharField(null=True, blank=True, max_length=255)
    had_contact_with_inf_people = models.CharField(null=True, blank=True, max_length=255)
    had_stul_for = models.BooleanField(default=False)

    allergy = models.CharField(null=True, blank=True, max_length=255)
    meteolabilisis = models.CharField(null=True, blank=True, max_length=255)
    non_carrying_prods = models.CharField(null=True, blank=True, max_length=255)
    stull_issues = models.CharField(null=True, blank=True, max_length=255)
    has_always_pills = models.CharField(null=True, blank=True, max_length=255)

    objective_data = models.TextField(null=True, blank=True)

    temperature = models.CharField(null=True, blank=True, max_length=255)

    arterial_high_low = models.CharField(max_length=255, null=True, blank=True)
    arterial_high = models.IntegerField(null=True)
    arterial_low = models.IntegerField(null=True)
    imt = models.IntegerField(null=True)

    pulse = models.CharField(choices=PULSE_CHOICES, null=True, blank=True, max_length=255)
    diet = models.CharField(null=True, blank=True, max_length=255)
    regime = models.CharField(choices=REGIME_CHOICES, null=True, blank=True, max_length=255)

    def __str__(self):
        return f"{self.id}"