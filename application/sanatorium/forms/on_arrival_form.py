from django import forms
from core.models import AppointmentWithOnDutyDoctorOnArrivalModel, Account


class OnDutyDoctorOnArrivalForm(forms.ModelForm):
    """Form for creating and updating on-duty doctor arrival appointments."""

    class Meta:
        model = AppointmentWithOnDutyDoctorOnArrivalModel
        exclude = ['created_by', 'modified_by', 'created_at', 'modified_at', 'illness_history', 'doctor']
        widgets = {
            # Basic information
            'state': forms.Select(attrs={'class': 'form-control'}),
            'complaints': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Жалобы пациента'}),

            # Arrival information
            'arv_number': forms.TextInput(attrs={'class': 'form-control'}),
            'ayes_shells': forms.TextInput(attrs={'class': 'form-control'}),
            'from_to_sanatorium': forms.TextInput(attrs={'class': 'form-control'}),
            'road_crossed': forms.TextInput(attrs={'class': 'form-control'}),

            # Medical history
            'abroad_for_last_years': forms.TextInput(attrs={'class': 'form-control'}),
            'virus_hepatitis': forms.TextInput(attrs={'class': 'form-control'}),
            'tuberculosis': forms.TextInput(attrs={'class': 'form-control'}),
            'malarias': forms.TextInput(attrs={'class': 'form-control'}),
            'venerian_illness': forms.TextInput(attrs={'class': 'form-control'}),
            'dizanteri': forms.TextInput(attrs={'class': 'form-control'}),
            'helminthic_infestations': forms.TextInput(attrs={'class': 'form-control'}),
            'had_contact_with_inf_people': forms.TextInput(attrs={'class': 'form-control'}),
            'had_stul_for': forms.CheckboxInput(attrs={'class': 'custom-control-input'}),

            # Patient conditions
            'allergy': forms.TextInput(attrs={'class': 'form-control'}),
            'meteolabilisis': forms.TextInput(attrs={'class': 'form-control'}),
            'non_carrying_prods': forms.TextInput(attrs={'class': 'form-control'}),
            'stull_issues': forms.TextInput(attrs={'class': 'form-control'}),
            'has_always_pills': forms.TextInput(attrs={'class': 'form-control'}),

            # Examination data
            'objective_data': forms.Textarea(
                attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Объективные данные осмотра'}),
            'temperature': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '36.6'}),
            'arterial_high_low': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '120/80'}),
            'arterial_high': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '120'}),
            'arterial_low': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '80'}),
            'imt': forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'pulse': forms.Select(attrs={'class': 'form-control'}),
            'diet': forms.TextInput(attrs={'class': 'form-control'}),
            'regime': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set field labels
        self.fields['arv_number'].label = "Номер прибытия"
        self.fields['ayes_shells'].label = "Глазные оболочки"
        self.fields['from_to_sanatorium'].label = "Прибытие из/в санаторий"
        self.fields['road_crossed'].label = "Дорога пройдена"
        self.fields['abroad_for_last_years'].label = "Выезд за границу за последние годы"
        self.fields['virus_hepatitis'].label = "Вирусный гепатит"
        self.fields['tuberculosis'].label = "Туберкулез"
        self.fields['malarias'].label = "Малярия"
        self.fields['venerian_illness'].label = "Венерические заболевания"
        self.fields['dizanteri'].label = "Дизентерия"
        self.fields['helminthic_infestations'].label = "Гельминтозы"
        self.fields['had_contact_with_inf_people'].label = "Контакт с инфекционными больными"
        self.fields['had_stul_for'].label = "Имел стул при себе"
        self.fields['allergy'].label = "Аллергия"
        self.fields['meteolabilisis'].label = "Метеочувствительность"
        self.fields['non_carrying_prods'].label = "Непереносимость продуктов"
        self.fields['stull_issues'].label = "Проблемы со стулом"
        self.fields['has_always_pills'].label = "Постоянно принимаемые препараты"
        self.fields['objective_data'].label = "Объективные данные"
        self.fields['temperature'].label = "Температура"
        self.fields['arterial_high_low'].label = "Артериальное давление"
        self.fields['arterial_high'].label = "Систолическое давление"
        self.fields['arterial_low'].label = "Диастолическое давление"
        self.fields['imt'].label = "ИМТ (Индекс массы тела)"
        self.fields['pulse'].label = "Пульс"
        self.fields['diet'].label = "Диета"
        self.fields['regime'].label = "Режим"