from django import forms
from django.utils import timezone
from core.models import ProcedureServiceModel, IndividualProcedureSessionModel, Service


class ProcedureForm(forms.ModelForm):
    class Meta:
        model = ProcedureServiceModel
        fields = [
            'medical_service',
            'therapist',
            'start_date',
            'frequency',
            'quantity',
            'comments'
        ]
        widgets = {
            'medical_service': forms.Select(attrs={'class': 'form-control select2'}),
            'therapist': forms.Select(attrs={'class': 'form-control select2'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control datepicker', 'autocomplete': 'off'}),
            'frequency': forms.Select(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'comments': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Filter medical services to only include procedures
        # self.fields['medical_service'].queryset = Service.objects.filter(
        #     type__name='procedure'
        # ).order_by('name')

        # Add "required" class to required fields for client-side validation
        for field_name, field in self.fields.items():
            if field.required:
                field.widget.attrs['class'] += ' required'

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')

        # Validate that start date is not in the past
        if start_date and start_date < timezone.now().date():
            self.add_error('start_date', 'Дата начала не может быть в прошлом')

        return cleaned_data


class ProcedureSessionForm(forms.ModelForm):
    class Meta:
        model = IndividualProcedureSessionModel
        fields = [
            'status',
            'therapist',
            'notes'
        ]
        widgets = {
            'status': forms.Select(attrs={'class': 'form-control'}),
            'therapist': forms.Select(attrs={'class': 'form-control select2'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }