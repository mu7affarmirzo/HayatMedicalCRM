from django import forms
from core.models import FinalAppointmentWithDoctorModel
from core.models import DiagnosisTemplate


class FinalAppointmentWithDoctorForm(forms.ModelForm):
    """Form for creating and updating final doctor appointments."""

    class Meta:
        model = FinalAppointmentWithDoctorModel
        exclude = ['created_by', 'modified_by', 'created_at', 'modified_at', 'doctor', 'illness_history']
        widgets = {
            # Status field
            'state': forms.Select(attrs={'class': 'form-control'}),

            # Patient assessment
            'objective_status': forms.Textarea(
                attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Объективные данные пациента'}),
            'file': forms.FileInput(attrs={'class': 'form-control-file'}),

            # Vitals
            'height': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '170', 'step': '0.1'}),
            'weight': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '70', 'step': '0.1'}),
            'heart_beat': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '80'}),
            'arterial_high_low': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'мм рт.ст.'}),
            'arterial_high': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '120'}),
            'arterial_low': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '80'}),
            'imt': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '24.5', 'step': '0.1'}),
            'imt_interpretation': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0', 'step': '0.1'}),

            # Diagnosis and conclusion
            'diagnosis': forms.SelectMultiple(attrs={'class': 'form-control select2', 'style': 'width: 100%;'}),
            'summary': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Заключение врача'}),
            'treatment_results': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Set diagnosis queryset
        self.fields['diagnosis'].queryset = DiagnosisTemplate.objects.all()

        # Set custom field labels
        self.fields['state'].label = "Статус приема"

        # Patient assessment
        self.fields['objective_status'].label = "Объективный статус"
        self.fields['file'].label = "Прикрепить файл"

        # Vitals
        self.fields['height'].label = "Рост (см)"
        self.fields['weight'].label = "Вес (кг)"
        self.fields['heart_beat'].label = "ЧСС (уд/мин)"
        self.fields['arterial_high_low'].label = "Единицы измерения АД"
        self.fields['arterial_high'].label = "Систолическое давление"
        self.fields['arterial_low'].label = "Диастолическое давление"
        self.fields['imt'].label = "Индекс массы тела (ИМТ)"
        self.fields['imt_interpretation'].label = "Интерпретация ИМТ"

        # Diagnosis and conclusion
        self.fields['diagnosis'].label = "Диагнозы"
        self.fields['summary'].label = "Заключение"
        self.fields['treatment_results'].label = "Результаты лечения"