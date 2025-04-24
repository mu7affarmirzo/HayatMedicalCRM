from django.db import models
from core.models import BaseAuditModel, STATE_CHOICES, Account, IllnessHistory


class ConsultingWithNeurologistModel(BaseAuditModel):
    class Meta:
        verbose_name = "Appointment | Консультация невролога"
        verbose_name_plural = "Appointment | Консультации невролога"

    ST_CHOICES = (
        ('Показан', 'Показан'),
        ('Не показан', 'Не показан'),
        ('Противопоказан', 'Противопоказан'),
    )
    state = models.CharField(choices=STATE_CHOICES, max_length=250, default='Приём завершён')

    doctor = models.ForeignKey(Account, on_delete=models.CASCADE, null=True)
    illness_history = models.ForeignKey(
        IllnessHistory, on_delete=models.CASCADE,
        null=True, related_name='neurologist_consulting'
    )
    is_familiar_with_anamnesis = models.BooleanField(default=False)
    complaint = models.TextField(null=True, blank=True)
    anamnesis = models.TextField(null=True, blank=True)

    palpebral_fissures = models.CharField(max_length=250, null=True, blank=True)  # Глазные щели
    pupils = models.CharField(max_length=250, null=True, blank=True)
    reaction_on_pupils = models.CharField(max_length=250, null=True, blank=True)
    aye_frame_movement = models.CharField(max_length=250, null=True, blank=True)
    nystagmus = models.CharField(max_length=250, null=True, blank=True)
    face = models.CharField(max_length=250, null=True, blank=True)
    tongue = models.CharField(max_length=250, null=True, blank=True)
    soft_sk = models.CharField(max_length=250, null=True, blank=True)
    phonation_swallowing = models.CharField(max_length=250, null=True, blank=True)
    reflexes = models.CharField(max_length=250, null=True, blank=True)
    muscle_strength = models.CharField(max_length=250, null=True, blank=True)
    muscle_tones = models.CharField(max_length=250, null=True, blank=True)
    deep_reflexes_hand = models.CharField(max_length=250, null=True, blank=True)
    deep_reflexes_foot = models.CharField(max_length=250, null=True, blank=True)
    stylo_radial = models.CharField(max_length=250, null=True, blank=True)
    biceps = models.CharField(max_length=250, null=True, blank=True, verbose_name='с двуглавой мышцы плеча')
    triceps = models.CharField(max_length=250, null=True, blank=True, verbose_name='с трехглавой мышцы плеча')
    knees = models.CharField(max_length=250, null=True, blank=True, verbose_name='коленные')
    achilles = models.CharField(max_length=250, null=True, blank=True, verbose_name='ахилловы')
    abdominal = models.CharField(max_length=250, null=True, blank=True, verbose_name='брюшные')
    pathological_reflexes = models.CharField(max_length=250, null=True, blank=True, verbose_name='Патологические рефлексы')
    romberg_position = models.CharField(
        max_length=250, null=True, blank=True,
        default='устойчив', verbose_name='Положение в позе Ромберга')
    complicated_position = models.CharField(
        max_length=250, null=True, blank=True,
        default='устойчив', verbose_name='В усложненной позе Ромберга')
    finger_test = models.CharField(
        max_length=250, null=True, blank=True,
        default='выполняет точно', verbose_name='Пальценосовая проба')
    heel_knee_test = models.CharField(
        max_length=250, null=True, blank=True,
        default='выполняет точно', verbose_name='Пяточно-коленная проба')
    gait = models.CharField(
        max_length=250, null=True, blank=True,
        default='устойчив', verbose_name='Походка')
    sensitivity = models.CharField(default='не нарушена', max_length=255)
    cognitive_test = models.CharField(null=True, blank=True, max_length=255)
    emotional_volitional_sphere = models.CharField(null=True, blank=True, max_length=255)
    insomnia = models.CharField(null=True, blank=True, max_length=255, default='эпизодическая')
    movements_in_the_cervical_spine = models.CharField(null=True, blank=True, max_length=255)
    movements_in_the_spinal_spine = models.CharField(
        null=True, blank=True, max_length=255, verbose_name='Движения в поясничном отделе позвоночника')
    spinous_processes = models.CharField(
        null=True, blank=True, max_length=255, verbose_name='Болезненность при пальпации остистых отростков')
    paravertebral_points = models.CharField(
        null=True, blank=True, max_length=255, verbose_name='Болезненность паравертебральных точек')
    lasegues_symptom = models.CharField(null=True, blank=True, max_length=255)

    cito = models.BooleanField(default=False)
    for_sanatorium_treatment = models.CharField(choices=ST_CHOICES, max_length=250, null=True, blank=True)
    summary = models.TextField(blank=True, null=True)
    recommendation = models.TextField(blank=True, null=True)


    def __str__(self):
        return f"{self.id}"

