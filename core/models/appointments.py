from django.db import models

from core.models import BaseAuditModel, Account, IllnessHistory, DiagnosisTemplate

CONSCIOUSNESS_CHOICES = (
        ("ясное", "ясное"),
        ("ступор", "ступор"),
        ("сопор", "сопор"),
    ("кома", "кома")
)
STATE_CHOICES = (
    ("активное", "активное"),
    ("пассивное", "пассивное"),
    ("вынужденное", "вынужденное")
)
CONSTITUTION_CHOICES = (
    ("нормасетик", "нормасетик"),
    ("аснетик", "аснетик"),
    ("гиперстеник", "гиперстеник")
)
SKIN_CHOICES = (
    ("нормальной окраски", "нормальной окраски"),
    ("бледные", "бледные"),
    ("гиперемия", "гиперемия"),
    ("иктеричные", "иктеричные"),
    ("субиктеричные", "субиктеричные"),
    ("акроцианоз", "акроцианоз"),
    ("земелистого цвета", "земелистого цвета")
)
SKIN_MOISTURE_CHOICES = (
    ("обычная", "обычная"),
    ("влажная", "влажная"),
    ("сухая", "сухая")
)
SKIN_TURGOR_CHOICES = (
    ("в норме", "в норме"),
    ("снижет", "снижет"),
)
SUBCUTANEOUS_FAT_CHOICES = (
    ("развита умеренно", "развита умеренно"),
    ("развита слабо", "развита слабо"),
    ("развита чрезмерно", "развита чрезмерно"),
)
LYMPH_NODES_CHOICES = (
    ("не увеличены", "не увеличены"),
    ("мягкие", "мягкие"),
    ("плотные", "плотные"),
    ("эластичные", "эластичные"),
)
BREATHING_TYPE_CHOICES = (
    ("нет", "нет"),
    ("брюшной", "брюшной"),
    ("смешанный", "смешанный"),
)
AUSCULTATIVE_BREATHING_CHOICES = (
    ("везикулярное", "везикулярное"),
    ("жестнкое", "жестнкое"),
    ("ослабленное", "ослабленное"),

)
WHEEZING_CHOICES = (
    ("сухые", "сухые"),
    ("влажное", "влажное"),
)
COUGHING_CHOICES = (
    ("сухой", "сухой"),
    ("мокрый", "мокрый"),
)
CREPITUS_CHOICES = (
    ("верхная часть", "верхная часть"),
    ("средняя часть", "средняя часть"),
    ("нижняя часть", "нижняя часть"),
    ("слева", "слева"),
    ("справа", "справа"),
)
LUNGS_PERCUSSION_CHOICES = (
    ("ясный", "ясный"),
    ("легочный", "легочный"),
    ("приглушенный", "приглушенный"),
    ("тупой", "тупой"),
    ("коробочный", "коробочный"),
    ("тимпанический", "тимпанический"),
    ("притупленно-тимпанический", "притупленно-тимпанический"),
    ("слева", "слева"),
    ("справа", "справа"),
)
HEAR_EDGE_CHOICES = (
    ("расширены", "расширены"),
    ("в норме", "в норме"),
)
HEART_TONES_CHOICES = (
    ("звучанные", "звучанные"),
    ("приглушенные", "приглушенные"),
    ("глухие", "глухие"),
    ("ритмичные", "ритмичные"),
    ("аритмичные", "аритмичные"),
    ("мерцательная аритмия", "мерцательная аритмия"),
    ("тахикардия", "тахикардия"),
    ("брадикардия", "брадикардия"),
)
ACCENT_IN_AORTA_CHOICES = (
    ("есть", "есть"),
    ("нет", "нет"),
    ("патологические шумы", "патологические шумы"),
)
N_C_ON_OT_CHOICES = (
    ("усиливается", "усиливается"),
    ("неизменяется", "неизменяется"),
)
NOISE_ON_ARTERIA = (
    ("сонная", "сонная"),
    ("подключичная", "подключичная"),
    ("яремная", "яремная"),
    ("тыльная", "тыльная"),
    ("слева", "слева"),
    ("справа", "справа"),
)
APPETIT_CHOICES = (
    ("удовлетворительный", "удовлетворительный"),
    ("снижен", "снижен"),
    ("повышен", "повышен"),
    ("анорексия", "анорексия"),
)
TONGUE_CHOICES = (
    ("чистый", "чистый"),
    ("влажный", "влажный"),
    ("географический", "географический"),
    ("облажен налетом", "облажен налетом"),
)
CUIM_CHOICES = (
    ("есть", "есть"),
)
STOMACH_CHOICES = (
    ("мягкий", "мягкий"),
    ("вздутый", "вздутый"),
    ("впавшый", "впавшый"),
)
ILL_PART_CHOICES = (
    ("в правом подреберье", "в правом подреберье"),
    ("в гипогастрии", "в гипогастрии"),
    ("по ходу толстого кишечника", "по ходу толстого кишечника"),
    ("по ходу тонкого кишечника", "по ходу тонкого кишечника"),
    ("вокруг пупка", "вокруг пупка"),
)
LIVER_CHOICES = (
    ("не увеличена", "не увеличена"),
    ("увеличена на ", "увеличена на "),
)
LIVER_EDGE_CHOICES = (
    ("острый", "острый"),
    ("закругленный", "закругленный"),
    ("мягкий", "мягкий"),
    ("плотный", "плотный")
)
SPLEEN_CHOICES = (
    ("не увеличена", "не увеличена"),
    ("увеличена на ", "увеличена на "),
)
SPLEEN_EDGE_CHOICES = (
    ("острый", "острый"),
    ("закругленный", "закругленный"),
    ("мягкий", "мягкий"),
    ("плотный", "плотный")
)
STOOL_CHOICES = (
    ("жидкий", "жидкий"),
    ("кашицеобразный", "кашицеобразный"),
    ("оформленный", "оформленный"),
    ("запоры", "запоры"),
    ("диарея", "диарея"),
)
EFFLEURAGE_SYMPTOMS_CHOICES = (
    ("отрицательный", "отрицательный"),
    ("положительный", "положительный"),
    ("справа", "справа"),
    ("слева", "слева"),
)
THYROID_CHOICES = (
    ("без изменений", "без изменений"),
    ("увеличена", "увеличена"),
    ("болезненна", "болезненна"),
    ("консистенция", "консистенция"),
)


class InitialAppointmentWithDoctorModel(BaseAuditModel):
    APP_STATE_CHOICES = (
        ('Приём завершён', 'Приём завершён'),
        ('Пациент на прием не явился', 'Пациент на прием не явился'),
        ('Не завершено', 'Не завершено'),
    )

    created_by = models.ForeignKey(Account, related_name='iawd_created', on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    modified_by = models.ForeignKey(Account, related_name="modf_iawd", on_delete=models.SET_NULL, null=True)

    state = models.CharField(choices=APP_STATE_CHOICES, max_length=250, default='Приём завершён')

    doctor = models.ForeignKey(Account, on_delete=models.CASCADE, null=True)
    illness_history = models.OneToOneField(
        IllnessHistory, on_delete=models.CASCADE,
        null=True, related_name='init_appointment'
    )

    complaint = models.TextField(null=True, blank=True, )
    anamnesis_morbi = models.TextField(null=True, blank=True)
    anamnesis_vitae = models.TextField(null=True, blank=True)

    contact_with_infectious = models.TextField(null=True, blank=True, default='на протяжении максимального срока инкубации: не было')
    contact_with_orvi = models.BooleanField(default=False)
    is_away_two_month = models.BooleanField(default=False, blank=True)
    transferred_infectious = models.CharField(max_length=255, null=True, blank=True)
    staying_hospital = models.CharField(max_length=255, null=True, blank=True)
    receiving_blood_transfusions = models.CharField(max_length=255, null=True, blank=True)
    surgical_massive_interventions_six_months = models.CharField(max_length=255, null=True, blank=True)
    dentist_visits_last_six_months = models.CharField(max_length=255, null=True, blank=True)
    profession_toxics = models.CharField(max_length=255, null=True, blank=True)
    additional_data = models.CharField(max_length=255, null=True, blank=True)

    # Status praesens objectivus
    general_state = models.CharField(null=True, blank=True, max_length=255)
    consciousness = models.CharField(choices=CONSCIOUSNESS_CHOICES, null=True, blank=True, max_length=255)
    consciousness_state = models.CharField(choices=CONSCIOUSNESS_CHOICES, null=True, blank=True, max_length=255)
    constitution = models.CharField(choices=CONSTITUTION_CHOICES, null=True, blank=True, max_length=255)
    skin = models.CharField(choices=SKIN_CHOICES, null=True, blank=True, max_length=255)
    pigmentation = models.CharField(null=True, blank=True, max_length=255)
    depigmentation = models.CharField(null=True, blank=True, max_length=255)
    rashes = models.CharField(null=True, blank=True, max_length=255)
    vascular_changes = models.CharField(null=True, blank=True, max_length=255)
    hemorrhages = models.CharField(null=True, blank=True, max_length=255)
    scarring = models.CharField(null=True, blank=True, max_length=255, verbose_name='рубцы')
    trophic_changes = models.CharField(null=True, blank=True, max_length=255)
    visible_tumors = models.CharField(null=True, blank=True, max_length=255)
    skin_moisture = models.CharField(choices=SKIN_MOISTURE_CHOICES, null=True, blank=True, max_length=255)
    skin_turgor = models.CharField(choices=SKIN_TURGOR_CHOICES, null=True, blank=True, max_length=255)
    subcutaneous_fat = models.CharField(choices=SUBCUTANEOUS_FAT_CHOICES, null=True, blank=True, max_length=255)
    temperature = models.FloatField(default=36.6)
    height = models.FloatField(null=True, blank=True)
    weight = models.FloatField(null=True, blank=True)
    heart_beat = models.IntegerField(null=True, blank=True)
    arterial_high = models.IntegerField(null=True, blank=True)
    arterial_low = models.IntegerField(null=True, blank=True)
    imt = models.FloatField(null=True, blank=True)
    extra_weight = models.FloatField(null=True, blank=True)
    swelling_pastiness = models.CharField(null=True, blank=True, max_length=255)
    lymph_nodes = models.CharField(choices=LYMPH_NODES_CHOICES, null=True, blank=True, max_length=255)

    # Конно-мыщечная система
    deformations = models.CharField(null=True, blank=True, max_length=255)
    contractures = models.CharField(null=True, blank=True, max_length=255)
    movement_restrictions = models.CharField(null=True, blank=True, max_length=255)

    # Dixatelnaya sistema
    respiratory_frequency = models.IntegerField(null=True, blank=True)
    breathing_type = models.CharField(choices=BREATHING_TYPE_CHOICES, null=True, blank=True, max_length=255)
    auscultative_breathing = models.CharField(choices=AUSCULTATIVE_BREATHING_CHOICES, default="везикулярное",
                                              null=True, blank=True, max_length=255)
    wheezing = models.CharField(choices=WHEEZING_CHOICES, default="влажное", null=True, blank=True, max_length=255)
    coughing = models.CharField(choices=COUGHING_CHOICES, null=True, blank=True, max_length=255)
    high_humidity = models.CharField(null=True, blank=True, max_length=255)
    crepitus = models.CharField(choices=CREPITUS_CHOICES, null=True, blank=True, max_length=255)
    lungs_percussion = models.CharField(choices=LUNGS_PERCUSSION_CHOICES, default='ясный',
                                        null=True, blank=True, max_length=255)

    # сердечно-сосудистая система
    heart_edge = models.CharField(choices=HEAR_EDGE_CHOICES, default='расширены', null=True, blank=True, max_length=255)
    heart_tones = models.CharField(choices=HEART_TONES_CHOICES, default='звучанные', null=True, blank=True, max_length=255)
    accent_in_aorta = models.CharField(choices=ACCENT_IN_AORTA_CHOICES, null=True, blank=True, max_length=255)
    noise_change_on_ot = models.CharField(choices=N_C_ON_OT_CHOICES, null=True, blank=True, max_length=255)
    ad_left = models.CharField(max_length=255, null=True, default="130/80")
    ad_right = models.CharField(max_length=255, null=True, default="130/80")
    ps_left = models.CharField(max_length=255, null=True, default="75")
    ps_right = models.CharField(max_length=255, null=True, default="75")
    pulse_noise_on_arteria = models.CharField(choices=NOISE_ON_ARTERIA, max_length=255, null=True, default="сонная")

    # органы пищеварения
    appetit = models.CharField(choices=APPETIT_CHOICES, max_length=255, null=True, default="удовлетворительный")
    tongue = models.CharField(choices=TONGUE_CHOICES, max_length=255, null=True, default="чистый, влажный")
    cracks_ulcers_in_mouth = models.CharField(choices=CUIM_CHOICES, max_length=255, null=True, blank=True)
    stomach = models.CharField(choices=STOMACH_CHOICES, max_length=255, null=True, default='мягкий')
    liver = models.CharField(choices=LIVER_CHOICES, max_length=255, null=True, blank=True, default="не увеличени")
    liver_edge = models.CharField(choices=LIVER_EDGE_CHOICES, max_length=255, null=True, blank=True)
    spleen = models.CharField(choices=SPLEEN_CHOICES, max_length=255, null=True, default="не увеличени")
    spleen_edge = models.CharField(choices=SPLEEN_EDGE_CHOICES, max_length=255, null=True, blank=True)
    stool = models.CharField(choices=STOOL_CHOICES, max_length=255, null=True, default="запоры")
    stool_frequency = models.CharField(max_length=255, null=True, default="1")

    # мочевидетальная система
    urinary_system = models.CharField(max_length=255, null=True, default="1")
    effleurage_symptoms = models.CharField(choices=EFFLEURAGE_SYMPTOMS_CHOICES, max_length=255,
                                           null=True, default="отрицательный")
    thyroid = models.CharField(choices=THYROID_CHOICES, max_length=255,
                               null=True, default="без изменений")
    nerve_system = models.CharField(choices=THYROID_CHOICES, max_length=255,
                                    null=True, default="без изменений")

    diagnosis = models.ForeignKey(DiagnosisTemplate, null=True, on_delete=models.SET_NULL)
    cito = models.BooleanField(default=False)
    summary = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.id}"


