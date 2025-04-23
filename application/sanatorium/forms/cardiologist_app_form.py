from django import forms
from core.models import ConsultingWithCardiologistModel, Account


class ConsultingWithCardiologistForm(forms.ModelForm):
    """Form for creating and updating cardiologist consultations."""

    class Meta:
        model = ConsultingWithCardiologistModel
        exclude = ['created_by', 'modified_by', 'created_at', 'modified_at', 'illness_history', 'doctor']
        widgets = {
            # Basic information
            'state': forms.Select(attrs={'class': 'form-control'}),

            # Complaints
            'has_cardio_complaints': forms.CheckboxInput(attrs={'class': 'custom-control-input'}),
            'has_nerve_complaints': forms.CheckboxInput(attrs={'class': 'custom-control-input'}),
            'other_complaints': forms.Textarea(
                attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Другие жалобы пациента'}),
            'history_of_illness': forms.Textarea(
                attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'История заболевания'}),
            'inheritance': forms.Textarea(
                attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Наследственность'}),

            # Vital measurements
            'height': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'placeholder': 'см'}),
            'weight': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'placeholder': 'кг'}),
            'pulse_general': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'уд/мин'}),
            'arterial_high_low': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '120/80'}),
            'arterial_high': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '120'}),
            'arterial_low': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '80'}),
            'imt': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'readonly': 'readonly'}),
            'imt_interpretation': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),

            # Body examination
            'body_figure': forms.Select(attrs={'class': 'form-control'}),
            'skin': forms.Select(attrs={'class': 'form-control'}),
            'sclera_visible_mucosa': forms.Select(attrs={'class': 'form-control'}),
            'thyroids': forms.Select(attrs={'class': 'form-control'}),
            'cervical': forms.Select(attrs={'class': 'form-control'}),
            'axillary': forms.Select(attrs={'class': 'form-control'}),
            'inguinal': forms.Select(attrs={'class': 'form-control'}),

            # Heart examination
            'pulse_per_min': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'уд/мин'}),
            'pulse': forms.Select(attrs={'class': 'form-control'}),
            'fault_of_pulse': forms.TextInput(attrs={'class': 'form-control'}),
            'heart_arterial_high': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '120'}),
            'heart_arterial_low': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '80'}),
            'left_heart_edges': forms.TextInput(attrs={'class': 'form-control'}),
            'right_heart_edges': forms.TextInput(attrs={'class': 'form-control'}),
            'upper_heart_edges': forms.TextInput(attrs={'class': 'form-control'}),
            'heart_beat': forms.TextInput(attrs={'class': 'form-control'}),
            'heart_tone': forms.Select(attrs={'class': 'form-control'}),
            'i_tone': forms.Select(attrs={'class': 'form-control'}),
            'ii_tone': forms.Select(attrs={'class': 'form-control'}),
            'noise': forms.Select(attrs={'class': 'form-control'}),
            'arterial_pulse_stop': forms.Select(attrs={'class': 'form-control'}),
            'varicose_veins_of_superficial_veins': forms.Select(attrs={'class': 'form-control'}),
            'trophic_skin_changes': forms.TextInput(attrs={'class': 'form-control'}),

            # Respiratory system
            'chdd_per_minute': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'в минуту'}),
            'chest_shape': forms.Select(attrs={'class': 'form-control'}),
            'pulmonary_fields': forms.Select(attrs={'class': 'form-control'}),
            'auscultation_breathing': forms.Select(attrs={'class': 'form-control'}),
            'wheezing': forms.Select(attrs={'class': 'form-control'}),
            'pleural_friction_rub': forms.Select(attrs={'class': 'form-control'}),

            # Conclusion
            'cito': forms.CheckboxInput(attrs={'class': 'custom-control-input'}),
            'file': forms.FileInput(attrs={'class': 'form-control-file'}),
            'for_sanatorium_treatment': forms.Select(attrs={'class': 'form-control'}),
            'summary': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Заключение'}),
            'recommendation': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Рекомендации'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter doctors to show only cardiologist

        # Set field labels
        self.fields['has_cardio_complaints'].label = "Кардиологические жалобы"
        self.fields['has_nerve_complaints'].label = "Неврологические жалобы"
        self.fields['pulse_general'].label = "Пульс (общий)"
        self.fields['arterial_high_low'].label = "Артериальное давление"
        self.fields['imt'].label = "Индекс массы тела (ИМТ)"
        self.fields['imt_interpretation'].label = "Интерпретация ИМТ"

        # Add help text for fields
        self.fields['height'].help_text = "Рост пациента в сантиметрах"
        self.fields['weight'].help_text = "Вес пациента в килограммах"
        self.fields['imt'].help_text = "Рассчитывается автоматически"
        self.fields['for_sanatorium_treatment'].label = "Для санаторно-курортного лечения"

        # Set required fields
        optional_fields = [
            'has_cardio_complaints', 'has_nerve_complaints', 'imt_interpretation',
            'i_tone', 'ii_tone', 'noise', 'arterial_pulse_stop', 'pleural_friction_rub',
            'cito', 'file', 'for_sanatorium_treatment'
        ]

        for field in optional_fields:
            self.fields[field].required = False