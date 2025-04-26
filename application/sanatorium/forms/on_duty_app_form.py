from django import forms
from core.models import AppointmentWithOnDutyDoctorModel
from core.models import DiagnosisTemplate


class AppointmentWithOnDutyDoctorForm(forms.ModelForm):
    """Form for creating and updating appointments with on-duty doctors."""

    class Meta:
        model = AppointmentWithOnDutyDoctorModel
        exclude = ['created_by', 'modified_by', 'created_at', 'modified_at', 'doctor', 'illness_history']
        widgets = {
            # Status field
            'state': forms.Select(attrs={'class': 'form-control'}),

            # Patient examination data
            'complaints': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Жалобы пациента'}),
            'objective_data': forms.Textarea(
                attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Объективные данные'}),

            # Vitals
            'arterial_high_low': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'мм рт.ст.'}),
            'arterial_high': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '120'}),
            'arterial_low': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '80'}),
            'imt': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Индекс массы тела'}),

            # Diagnosis and conclusion
            'diagnosis': forms.Select(attrs={'class': 'form-control select2', 'style': 'width: 100%;'}),
            'cito': forms.CheckboxInput(attrs={'class': 'custom-control-input'}),
            'for_sanatorium_treatment': forms.Select(attrs={'class': 'form-control'}),
            'summary': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Заключение врача'}),
            'recommendation': forms.Textarea(
                attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Рекомендации врача'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Set diagnosis queryset
        self.fields['diagnosis'].queryset = DiagnosisTemplate.objects.all()

        # Set custom field labels
        self.fields['complaints'].label = "Жалобы"
        self.fields['objective_data'].label = "Объективные данные"
        self.fields['arterial_high_low'].label = "Единицы измерения АД"
        self.fields['arterial_high'].label = "Систолическое давление"
        self.fields['arterial_low'].label = "Диастолическое давление"
        self.fields['imt'].label = "Индекс массы тела (ИМТ)"
        self.fields['diagnosis'].label = "Диагноз"
        self.fields['cito'].label = "Срочно (CITO)"
        self.fields['for_sanatorium_treatment'].label = "Для санаторного лечения"
        self.fields['summary'].label = "Заключение"
        self.fields['recommendation'].label = "Рекомендации"
        self.fields['state'].label = "Статус приема"