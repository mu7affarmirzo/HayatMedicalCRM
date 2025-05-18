# forms.py
from datetime import datetime, timedelta

from django import forms
from django.utils import timezone

from core.models import PrescribedMedication, MedicationSession, MedicationsInStockModel, Account


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


class MedicationSessionForm(forms.ModelForm):
    # Fields outside Meta for custom behavior
    created_by = forms.ModelChoiceField(
        queryset=Account.objects.filter(is_staff=True),  # Assuming staff can administer medications
        required=False,  # Can be null in our model
        label="Administered By",
        widget=forms.Select(attrs={'class': 'form-control select2', 'id': 'administrator-select'})
    )

    status = forms.ChoiceField(
        choices=MedicationSession.STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'status-select'})
    )

    class Meta:
        model = MedicationSession
        fields = [
            'status',
            'notes',
        ]
        widgets = {
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

        # Add placeholders
        self.fields['notes'].widget.attrs['placeholder'] = 'Administration notes, side effects, or patient response...'

        # Show/hide fields based on status
        instance_status = self.instance.status if self.instance.pk else 'pending'
        current_status = self.data.get('status', instance_status)

    def clean(self):
        cleaned_data = super().clean()
        status = cleaned_data.get('status')

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)

        # Additional logic based on status
        if instance.status == 'administered' and not instance.created_at:
            instance.created_at = timezone.now()

        if commit:
            instance.save()

        return instance

