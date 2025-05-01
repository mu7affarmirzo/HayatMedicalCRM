from django import forms
from django.utils import timezone
from core.models import ProcedureServiceModel, IndividualProcedureSessionModel, Service, ServiceTypeModel


class ProcedureForm(forms.ModelForm):
    service_type = forms.ModelChoiceField(
        queryset=ServiceTypeModel.objects.all(),
        required=True,
        label="Тип услуги",
        widget=forms.Select(attrs={'class': 'form-control select2', 'id': 'service-type'})
    )
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
            'medical_service': forms.Select(attrs={'class': 'form-control select2', 'id': 'medical-service'}),
            'therapist': forms.Select(attrs={'class': 'form-control select2'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control datepicker', 'type': 'date'}),
            'frequency': forms.Select(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'comments': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Set initial empty choice for medical_service
        self.fields['medical_service'].queryset = Service.objects.none()

        # If we have an instance with a selected medical_service
        if self.instance and self.instance.pk and self.instance.medical_service:
            service_type = self.instance.medical_service.type
            self.fields['service_type'].initial = service_type
            self.fields['medical_service'].queryset = Service.objects.filter(type=service_type)

        # If we have data with service_type already selected
        if 'service_type' in self.data:
            try:
                service_type_id = int(self.data.get('service_type'))
                self.fields['medical_service'].queryset = Service.objects.filter(
                    type_id=service_type_id
                )
            except (ValueError, TypeError):
                pass  # Invalid input, ignore

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