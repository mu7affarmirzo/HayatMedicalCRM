from django import forms
from core.models import EkgAppointmentModel, DiagnosisTemplate


class EkgAppointmentForm(forms.ModelForm):
    """Form for creating and updating EKG appointments."""

    class Meta:
        model = EkgAppointmentModel
        exclude = ['created_by', 'modified_by', 'created_at', 'modified_at', 'doctor', 'illness_history']
        widgets = {
            # Status field
            'state': forms.Select(attrs={'class': 'form-control'}),

            # ECG measurements
            'rhythm': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ритм'}),
            'heart_s_count': forms.NumberInput(
                attrs={'class': 'form-control', 'placeholder': 'Число сердечных сокращений'}),
            'r_r': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'R-R'}),
            'p_q': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'P-Q'}),
            'qrs': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'QRS'}),
            'v1': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'V1'}),
            'v6': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'V6'}),
            'q_t': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Q-T'}),
            'la': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'LA'}),

            # ECG analysis
            'prong_p': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Зубец P'}),
            'complex_qrs': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Комплекс QRS'}),
            'prong_t': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Зубец T'}),
            'segment_st': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Сегмент ST'}),
            'electric_axis': forms.Select(attrs={'class': 'form-control'}),

            # Medical assessment
            'cito': forms.CheckboxInput(attrs={'class': 'custom-control-input'}),
            'diagnosis': forms.Select(attrs={'class': 'form-control select2', 'style': 'width: 100%;'}),
            'for_sanatorium_treatment': forms.Select(attrs={'class': 'form-control'}),
            'objective_data': forms.Textarea(
                attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Объективные данные'}),
            'summary': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Заключение'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Set diagnosis queryset
        self.fields['diagnosis'].queryset = DiagnosisTemplate.objects.all()

        # Set custom field labels
        self.fields['state'].label = "Статус приема"

        # ECG measurements
        self.fields['rhythm'].label = "Ритм"
        self.fields['heart_s_count'].label = "ЧСС (уд/мин)"
        self.fields['r_r'].label = "R-R (сек)"
        self.fields['p_q'].label = "P-Q (сек)"
        self.fields['qrs'].label = "QRS (сек)"
        self.fields['v1'].label = "V1"
        self.fields['v6'].label = "V6"
        self.fields['q_t'].label = "Q-T (сек)"
        self.fields['la'].label = "ЛА"

        # ECG analysis
        self.fields['prong_p'].label = "Зубец P"
        self.fields['complex_qrs'].label = "Комплекс QRS"
        self.fields['prong_t'].label = "Зубец T"
        self.fields['segment_st'].label = "Сегмент ST"
        self.fields['electric_axis'].label = "Электрическая ось"

        # Medical assessment
        self.fields['cito'].label = "Срочно (CITO)"
        self.fields['diagnosis'].label = "Диагноз"
        self.fields['for_sanatorium_treatment'].label = "Для санаторного лечения"
        self.fields['objective_data'].label = "Объективные данные"
        self.fields['summary'].label = "Заключение"