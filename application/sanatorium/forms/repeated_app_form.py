from django import forms
from core.models import RepeatedAppointmentWithDoctorModel

class RepeatedAppointmentForm(forms.ModelForm):
    class Meta:
        model = RepeatedAppointmentWithDoctorModel
        exclude = ['created_by', 'modified_by', 'created_at', 'modified_at', 'illness_history', 'doctor']
        fields = [
            'complaint', 'objective_data',
            'arterial_high_low', 'arterial_high', 'arterial_low', 'imt',
            'diagnosis', 'cito', 'summary', 'state'
        ]
        widgets = {
            'complaint': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'objective_data': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'arterial_high_low': forms.TextInput(attrs={'class': 'form-control'}),
            'arterial_high': forms.NumberInput(attrs={'class': 'form-control'}),
            'arterial_low': forms.NumberInput(attrs={'class': 'form-control'}),
            'imt': forms.TextInput(attrs={'class': 'form-control'}),
            'summary': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'state': forms.Select(attrs={'class': 'form-control'}),
            'diagnosis': forms.Select(attrs={'class': 'form-control select2', 'style': 'width: 100%;'}),
            'cito': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
