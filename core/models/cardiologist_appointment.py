from django.db import models

from core.models import BaseAuditModel, Account, IllnessHistory, upload_location

STATE_CHOICES = (
        ('Приём завершён', 'Приём завершён'),
        ('Пациент на прием не явился', 'Пациент на прием не явился'),
        ('Не завершено', 'Не завершено'),
    )

ST_CHOICES = (
    ('Показан', 'Показан'),
    ('Не показан', 'Не показан'),
    ('Противопоказан', 'Противопоказан'),
)
BODY_CHOICES = (
    ('правильное,', 'правильное,'),
    ('неправильное,', 'неправильное,'),
    ('астеник', 'астеник'),
    ('нормастеник', 'нормастеник'),
    ('гиперстеник', 'гиперстеник'),
)
SKIN_CHOICES = (
    ('нормальной окраски', 'нормальной окраски'),
    ('бледные', 'бледные'),
    ('желтушные', 'желтушные'),
    ('гиперемированные,', 'гиперемированные,'),
    ('высыпания', 'высыпания'),
)
MUCOSA_CHOICES = (
    ('нормальной окраски', 'нормальной окраски'),
    ('бледные', 'бледные'),
    ('желтушные', 'желтушные'),
    ('гиперемированные,', 'гиперемированные,'),
)
THYROIDS_CHOICES = (
    ('не увеличена', 'не увеличена'),
    ('увеличена до', 'увеличена до'),
    ('0', '0'),
    ('I', 'I'),
    ('II ст', 'II ст'),
)
LYMPHATIC_CHOICES = (
    ('не увеличены', 'не увеличены'),
    ('увеличены', 'увеличены'),
    ('мягкие', 'мягкие'),
    ('уплотнены при пальпации', 'уплотнены при пальпации'),
    ('безболезненные', 'безболезненные'),
    ('болезненные', 'болезненные'),
)

PULSE_CHOICES = (
    ('ритмичный', 'ритмичный'),
    ('аритмичный', 'аритмичный'),
    ('напряжен', 'напряжен'),
    ('хорошего', 'хорошего'),
    ('удовлетворительного наполнения и напряжения', 'удовлетворительного наполнения и напряжения'),
)
HEART_TONE_CHOICES = (
    ('чистые', 'чистые'),
    ('ясные', 'ясные'),
    ('громкие', 'громкие'),
    ('приглушенные', 'приглушенные'),
    ('глухие', 'глухие'),
)
I_TONE_CHOICES = (
    ('ослаблен', 'ослаблен'),
    ('усилен', 'усилен'),
)
II_TONE_CHOICES = (
    ('аорте', 'аорте'),
    ('легочной артерии', 'легочной артерии'),
)
NOISE_CHOICES = (
    ('отсутствует', 'отсутствует'),
    ('диастолический', 'диастолический'),
)
ARTERIAL_PULSE_STOP_CHOICES = (
    ('отчетливая', 'отчетливая'),
    ('ослаблена', 'ослаблена'),
    ('отсутствует', 'отсутствует'),
    ('слева', 'слева'),
    ('справа', 'справа'),
)
SUPERFICIAL_VEINS_CHOICES = (
    ('отсутствует', 'отсутствует'),
    ('слева', 'слева'),
    ('справа', 'справа'),
)
CHEST_SHAPE_CHOICES = (
    ('правильная', 'правильная'),
    ('неправильная', 'неправильная'),
    ('«бочкообразная»', '«бочкообразная»'),
)
PULMONARY_FIELDS_CHOICES = (
    ('легочный', 'легочный'),
    ('с коробочным оттенком', 'с коробочным оттенком'),
    ('укорочение', 'укорочение'),
    ('притупление', 'притупление'),
)
AUSCULTATION_BREATHING_CHOICES = (
    ('везикулярное', 'везикулярное'),
    ('ослабленное', 'ослабленное'),
    ('жесткое', 'жесткое'),
    ('бронхиальное', 'бронхиальное'),
)
WHEEZING_CHOICES = (
    ('отсутствуют', 'отсутствуют'),
    ('имеются сухие', 'имеются сухие'),
    ('влажные', 'влажные'),
    ('крепитирующие', 'крепитирующие'),
)
PLEURAL_FRICTION_RUB_CHOICES = (
    ('шум трения плевры', 'шум трения плевры'),
)

class ConsultingWithCardiologistModel(BaseAuditModel):

    state = models.CharField(choices=STATE_CHOICES, max_length=250, default='Приём завершён')

    doctor = models.ForeignKey(Account, on_delete=models.CASCADE, null=True)
    illness_history = models.ForeignKey(
        IllnessHistory, on_delete=models.CASCADE,
        null=True, related_name='cardiologist_consulting'
    )
    has_cardio_complaints = models.BooleanField(default=False)
    has_nerve_complaints = models.BooleanField(default=False)
    other_complaints = models.TextField(null=True, blank=True)
    history_of_illness = models.TextField(null=True, blank=True)
    inheritance = models.TextField(null=True, blank=True)

    height = models.FloatField(null=True, blank=True)
    weight = models.FloatField(null=True, blank=True)
    pulse_general = models.IntegerField(null=True, blank=True)
    arterial_high_low = models.CharField(max_length=255, null=True, blank=True)
    arterial_high = models.IntegerField(null=True, blank=True)
    arterial_low = models.IntegerField(null=True, blank=True)
    imt = models.FloatField(null=True, blank=True)
    imt_interpretation = models.FloatField(null=True, blank=True)

    body_figure = models.CharField(max_length=255, choices=BODY_CHOICES, default='правильное, нормастеник')
    skin = models.CharField(max_length=255, choices=SKIN_CHOICES, default='нормальной окраски')
    sclera_visible_mucosa = models.CharField(max_length=255, choices=MUCOSA_CHOICES, default='нормальной окраски')
    thyroids = models.CharField(max_length=255, choices=THYROIDS_CHOICES, default='не увеличена')
    cervical = models.CharField(max_length=255, choices=LYMPHATIC_CHOICES, default='не увеличены, мягкие, безболезненные')
    axillary = models.CharField(max_length=255, choices=LYMPHATIC_CHOICES, default='не увеличены, мягкие, безболезненные')
    inguinal = models.CharField(max_length=255, choices=LYMPHATIC_CHOICES, default='не увеличены, мягкие, безболезненные')

    pulse_per_min = models.IntegerField(null=True, blank=True)
    pulse = models.CharField(max_length=255, choices=PULSE_CHOICES, default='ритмичный')
    fault_of_pulse = models.CharField(max_length=255, default='отсутствует')
    heart_arterial_high = models.IntegerField(null=True, blank=True)
    heart_arterial_low = models.IntegerField(null=True, blank=True)
    left_heart_edges = models.CharField(max_length=255, default='в норме')
    right_heart_edges = models.CharField(max_length=255, default='в норме')
    upper_heart_edges = models.CharField(max_length=255, default='в норме')
    heart_beat = models.CharField(max_length=255, default='в норме')
    heart_tone = models.CharField(max_length=255, choices=HEART_TONE_CHOICES, default='чистые, ясные')
    i_tone = models.CharField(max_length=255, choices=I_TONE_CHOICES, null=True, blank=True)
    ii_tone = models.CharField(max_length=255, choices=II_TONE_CHOICES, null=True, blank=True)

    noise = models.CharField(max_length=255, choices=II_TONE_CHOICES, null=True, blank=True)
    arterial_pulse_stop = models.CharField(max_length=255, choices=ARTERIAL_PULSE_STOP_CHOICES, null=True, blank=True)
    varicose_veins_of_superficial_veins = models.CharField(max_length=255, choices=SUPERFICIAL_VEINS_CHOICES, default='отсутствует')
    trophic_skin_changes = models.CharField(max_length=255, default='отсутствует')

    chdd_per_minute = models.IntegerField(null=True, blank=True)
    chest_shape = models.CharField(max_length=255, choices=CHEST_SHAPE_CHOICES, default='правильная')
    pulmonary_fields = models.CharField(max_length=255,
        verbose_name='При сравнительной перкуссии над легочными полями звук',
        choices=PULMONARY_FIELDS_CHOICES, default='легочный'
    )
    auscultation_breathing = models.CharField(max_length=255,
        verbose_name='При аускультации дыхание',
        choices=AUSCULTATION_BREATHING_CHOICES, default='везикулярное,'
    )
    wheezing = models.CharField(max_length=255,
        verbose_name='Хрипы',
        choices=WHEEZING_CHOICES, default='везикулярное,'
    )
    pleural_friction_rub = models.CharField(max_length=255,
        verbose_name='шум трения плевры', null=True, blank=True,
        choices=PLEURAL_FRICTION_RUB_CHOICES
    )

    cito = models.BooleanField(default=False)
    file = models.FileField(upload_to=upload_location, null=True, blank=True)
    for_sanatorium_treatment = models.CharField(choices=ST_CHOICES, max_length=250, null=True, blank=True)
    summary = models.TextField(blank=True, null=True)
    recommendation = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.id}"

