from django import forms
from core.models import RepeatedAppointmentWithDoctorModel


class RepeatedAppointmentForm(forms.ModelForm):
    """Form for creating and updating repeated doctor appointments."""

    class Meta:
        model = RepeatedAppointmentWithDoctorModel
        exclude = ['created_by', 'modified_by', 'created_at', 'modified_at', 'doctor', 'illness_history']
        widgets = {
            # Primary fields
            'state': forms.Select(attrs={'class': 'form-control'}),

            # Patient examination data
            'complaint': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Жалобы пациента'}),
            'objective_data': forms.Textarea(
                attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Объективные данные'}),

            # Vitals
            'arterial_high': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '120'}),
            'arterial_low': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '80'}),
            'arterial_high_low': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'мм рт.ст.'}),
            'imt': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Индекс массы тела'}),

            # Diagnosis and conclusion
            'diagnosis': forms.Select(attrs={'class': 'form-control select2', 'style': 'width: 100%;'}),
            'cito': forms.CheckboxInput(attrs={'class': 'custom-control-input'}),
            'summary': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Заключение врача'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set custom field labels
        self.fields['complaint'].label = "Жалобы"
        self.fields['objective_data'].label = "Объективные данные"
        self.fields['arterial_high'].label = "Систолическое давление"
        self.fields['arterial_low'].label = "Диастолическое давление"
        self.fields['arterial_high_low'].label = "Единицы измерения АД"
        self.fields['imt'].label = "Индекс массы тела (ИМТ)"
        self.fields['diagnosis'].label = "Диагноз"
        self.fields['cito'].label = "Срочно (Cito)"
        self.fields['summary'].label = "Заключение"
        self.fields['state'].label = "Статус приёма"
