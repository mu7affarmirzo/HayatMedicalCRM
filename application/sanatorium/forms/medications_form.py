# forms.py
from datetime import datetime, timedelta

from django import forms
from django.utils import timezone

from core.models import PrescribedMedication, MedicationAdministration, MedicationsInStockModel, Account


class PrescribedMedicationForm(forms.ModelForm):
    # Fields defined outside Meta for custom behavior
    medication = forms.ModelChoiceField(
        queryset=MedicationsInStockModel.objects.all(),
        required=True,
        label="Medication",
        widget=forms.Select(attrs={'class': 'form-control select2', 'id': 'medication-select'})
    )

    class Meta:
        model = PrescribedMedication
        fields = [
            'medication',
            'dosage',
            'frequency',
            'route',
            'start_date',
            'end_date',
            'duration_days',
            'status',
            'is_prn',
            'instructions',
            'reason'
        ]
        widgets = {
            'dosage': forms.TextInput(attrs={'class': 'form-control'}),
            'frequency': forms.Select(attrs={'class': 'form-control select2'}),
            'route': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Введите способ применения'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control datepicker', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control datepicker', 'type': 'date'}),
            'duration_days': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'status': forms.Select(attrs={'class': 'form-control select2'}),
            'is_prn': forms.CheckboxInput(attrs={'class': 'custom-control-input'}),
            'instructions': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.illness_history = kwargs.pop('illness_history', None)

        super().__init__(*args, **kwargs)

        # Add any placeholder text or help text
        self.fields['dosage'].widget.attrs['placeholder'] = 'e.g., 500mg'
        self.fields['instructions'].widget.attrs['placeholder'] = 'Administration instructions...'
        self.fields['reason'].widget.attrs['placeholder'] = 'Reason for prescribing...'

        # Set initial values if needed
        if not self.instance.pk:  # Only for new instances
            is_assigned_doctor = False
            if self.user and self.illness_history:
                is_assigned_doctor = self.illness_history.doctor == self.user

            # Set initial status based on doctor assignment
            if is_assigned_doctor:
                self.fields['status'].initial = 'assigned'
            else:
                self.fields['status'].initial = 'prescribed'

            self.fields['start_date'].initial = timezone.now().date()

        # Calculate suggested end date based on duration if provided
        if 'duration_days' in self.data and self.data.get('duration_days'):
            try:
                duration = int(self.data.get('duration_days'))
                start_date = self.fields['start_date'].initial or timezone.now().date()
                if 'start_date' in self.data and self.data.get('start_date'):
                    try:
                        start_date = datetime.strptime(self.data.get('start_date'), '%Y-%m-%d').date()
                    except ValueError:
                        pass

                end_date = start_date + timedelta(days=duration - 1)  # -1 because duration includes start date
                self.fields['end_date'].initial = end_date
            except (ValueError, TypeError):
                pass

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        is_prn = cleaned_data.get('is_prn')
        duration_days = cleaned_data.get('duration_days')

        if not cleaned_data.get('medication'):
            raise forms.ValidationError("Medication is required")

        # Validate that start date is not in the past
        if start_date and start_date < timezone.now().date():
            self.add_error('start_date', 'Start date cannot be in the past')

        # Validate end date is after start date
        if start_date and end_date and end_date < start_date:
            self.add_error('end_date', 'End date must be after start date')

        # Set duration based on dates if not explicitly provided
        if start_date and end_date and not duration_days:
            duration = (end_date - start_date).days + 1  # +1 to include both start and end dates
            cleaned_data['duration_days'] = duration

        # For PRN medications, certain fields are not required
        if is_prn:
            if 'frequency' in self._errors:
                del self._errors['frequency']
            if 'end_date' in self._errors:
                del self._errors['end_date']
            if 'duration_days' in self._errors:
                del self._errors['duration_days']

        return cleaned_data


class MedicationAdministrationForm(forms.ModelForm):
    # Fields outside Meta for custom behavior
    administered_by = forms.ModelChoiceField(
        queryset=Account.objects.filter(is_staff=True),  # Assuming staff can administer medications
        required=True,
        label="Administered By",
        widget=forms.Select(attrs={'class': 'form-control select2', 'id': 'administrator-select'})
    )

    class Meta:
        model = MedicationAdministration
        fields = [
            'administered_at',
            'dosage_given',
            'notes',
            'patient_response',
            'side_effects'
        ]
        widgets = {
            'administered_at': forms.DateTimeInput(
                attrs={'class': 'form-control datetimepicker', 'type': 'datetime-local'}
            ),
            'dosage_given': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'patient_response': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'side_effects': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Set initial values
        if not self.instance.pk:  # Only for new instances
            self.fields['administered_at'].initial = timezone.now()

            # If the user is logged in and is staff, set them as the default administrator
            request = getattr(kwargs.get('request', None), '_request', None)
            if request and request.user.is_authenticated and request.user.is_staff:
                self.fields['administered_by'].initial = request.user.id

        # Add placeholders
        self.fields['dosage_given'].widget.attrs['placeholder'] = 'Actual dosage administered'
        self.fields['notes'].widget.attrs['placeholder'] = 'Administration notes...'
        self.fields['patient_response'].widget.attrs['placeholder'] = 'How did the patient respond?'
        self.fields['side_effects'].widget.attrs['placeholder'] = 'Any observed side effects?'

    def clean(self):
        cleaned_data = super().clean()
        administered_at = cleaned_data.get('administered_at')

        # Validate administration time is not in the future
        if administered_at and administered_at > timezone.now():
            self.add_error('administered_at', 'Administration time cannot be in the future')

        # If this is linked to a prescribed medication, verify dosage is appropriate
        prescribed_med = getattr(self.instance, 'prescribed_medication', None)
        if prescribed_med and 'dosage_given' in cleaned_data:
            # This would require custom validation logic based on your requirements
            # For example, comparing the given dosage with the prescribed dosage
            pass

        return cleaned_data