from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
import datetime
import logging

from core.models import PatientModel, Region, District
from application.logus.utils.patient_validation import (
    check_duplicate_patient,
    validate_uzbekistan_phone,
    check_patient_data_quality
)

logger = logging.getLogger(__name__)


class SimplePatientForm(forms.ModelForm):
    date_of_birth = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'placeholder': 'YYYY-MM-DD'}),
        input_formats=['%Y-%m-%d', '%m/%d/%Y', '%m/%d/%y']
    )

    class Meta:
        model = PatientModel
        fields = [
            'f_name', 'mid_name', 'l_name', 'address',
            'date_of_birth', 'mobile_phone_number', 'gender', 'INN', 'additional_info'
        ]

    def clean_mobile_phone_number(self):
        """Validate mobile phone number format"""
        phone = self.cleaned_data.get('mobile_phone_number')
        if phone:
            validation = validate_uzbekistan_phone(phone)
            if not validation['valid']:
                raise ValidationError(validation['error'])
            return validation['raw']
        return phone

    def clean_date_of_birth(self):
        """Validate date of birth"""
        dob = self.cleaned_data.get('date_of_birth')
        if dob and dob > datetime.date.today():
            raise ValidationError(_('Дата рождения не может быть в будущем'))
        return dob


class PatientRegistrationForm(forms.ModelForm):
    """
    DEPRECATED: Use PatientForm or SimplePatientForm instead.
    This is kept for backward compatibility.
    """
    date_of_birth = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'placeholder': 'YYYY-MM-DD'}),
        input_formats=['%Y-%m-%d', '%m/%d/%Y', '%m/%d/%y']
    )

    class Meta:
        model = PatientModel
        fields = [
            'f_name', 'mid_name', 'l_name', 'address',
            'date_of_birth', 'mobile_phone_number', 'gender', 'INN', 'additional_info'
        ]

    def clean_mobile_phone_number(self):
        """Validate mobile phone number format"""
        phone = self.cleaned_data.get('mobile_phone_number')
        if phone:
            validation = validate_uzbekistan_phone(phone)
            if not validation['valid']:
                raise ValidationError(validation['error'])
            return validation['raw']
        return phone

    def clean_date_of_birth(self):
        """Validate date of birth"""
        dob = self.cleaned_data.get('date_of_birth')
        if dob and dob > datetime.date.today():
            raise ValidationError(_('Дата рождения не может быть в будущем'))
        return dob


class PatientForm(forms.ModelForm):
    class Meta:
        model = PatientModel
        fields = [
            'l_name', 'f_name', 'mid_name', 'email', 'date_of_birth',
            'home_phone_number', 'mobile_phone_number', 'address',
            'doc_type', 'doc_number',
            'INN', 'country', 'gender', 'gestational_age',
            'region', 'district'
        ]
        widgets = {
            'l_name': forms.TextInput(attrs={'class': 'form-control'}),
            'f_name': forms.TextInput(attrs={'class': 'form-control'}),
            'mid_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'home_phone_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+998 XX XXX-XX-XX'
            }),
            'mobile_phone_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+998 XX XXX-XX-XX',
                'data-inputmask': '"mask": "+\\9\\98 99 999-99-99"',
                'data-mask': True
            }),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'doc_type': forms.TextInput(attrs={'class': 'form-control'}),
            'doc_number': forms.TextInput(attrs={'class': 'form-control'}),
            'INN': forms.TextInput(attrs={'class': 'form-control'}),
            'country': forms.TextInput(attrs={'class': 'form-control'}),
            'gender': forms.RadioSelect(choices=((True, 'Мужской'), (False, 'Женский'))),
            'gestational_age': forms.NumberInput(attrs={'class': 'form-control'}),
            'region': forms.Select(attrs={'class': 'form-control'}),
            'district': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set queryset for regions - only active ones
        self.fields['region'].queryset = Region.objects.filter(is_active=True)

        # Set empty queryset for districts initially
        self.fields['district'].queryset = District.objects.none()

        # If form is bound and has a region value, or if instance has a region
        if self.is_bound and 'region' in self.data and self.data['region']:
            try:
                region_id = int(self.data['region'])
                self.fields['district'].queryset = District.objects.filter(
                    region_id=region_id, is_active=True
                )
            except (ValueError, TypeError):
                pass
        elif self.instance and self.instance.pk and self.instance.region:
            self.fields['district'].queryset = District.objects.filter(
                region=self.instance.region, is_active=True
            )

    def clean_mobile_phone_number(self):
        """Validate mobile phone number format"""
        phone = self.cleaned_data.get('mobile_phone_number')
        if not phone:
            raise ValidationError(_('Мобильный телефон обязателен для заполнения'))

        # Validate Uzbekistan format
        validation = validate_uzbekistan_phone(phone)
        if not validation['valid']:
            raise ValidationError(validation['error'])

        # Return standardized format
        return validation['raw']

    def clean_home_phone_number(self):
        """Validate home phone number format if provided"""
        phone = self.cleaned_data.get('home_phone_number')
        if phone:
            validation = validate_uzbekistan_phone(phone)
            if not validation['valid']:
                raise ValidationError(validation['error'])
            return validation['raw']
        return phone

    def clean_date_of_birth(self):
        """Validate date of birth"""
        dob = self.cleaned_data.get('date_of_birth')
        if not dob:
            raise ValidationError(_('Дата рождения обязательна'))

        # Check not in future
        if dob > datetime.date.today():
            raise ValidationError(_('Дата рождения не может быть в будущем'))

        # Check reasonable age (0-120 years)
        age = (datetime.date.today() - dob).days // 365
        if age > 120:
            raise ValidationError(_('Пожалуйста, проверьте правильность даты рождения'))

        return dob

    def clean(self):
        """Validate entire form and check for duplicates"""
        cleaned_data = super().clean()

        # Check data quality
        quality_check = check_patient_data_quality(cleaned_data)

        # Add warnings as messages (don't block form)
        if quality_check['has_warnings']:
            for warning in quality_check['warnings']:
                logger.warning(f"Patient form warning: {warning}")

        # Errors block the form
        if quality_check['has_errors']:
            for error in quality_check['errors']:
                raise ValidationError(error)

        # Check for duplicate patients
        f_name = cleaned_data.get('f_name')
        l_name = cleaned_data.get('l_name')
        dob = cleaned_data.get('date_of_birth')
        phone = cleaned_data.get('mobile_phone_number')
        email = cleaned_data.get('email')
        doc_number = cleaned_data.get('doc_number')

        if f_name and l_name and dob:
            # Exclude current instance if editing
            exclude_id = self.instance.pk if self.instance and self.instance.pk else None

            duplicates = check_duplicate_patient(
                f_name=f_name,
                l_name=l_name,
                date_of_birth=dob,
                mobile_phone=phone,
                email=email,
                doc_number=doc_number,
                exclude_id=exclude_id
            )

            if duplicates:
                # Get highest confidence duplicate
                top_match = duplicates[0]

                if top_match['confidence'] == 'high':
                    # High confidence - block the form
                    raise ValidationError(
                        f"{top_match['message']}. "
                        f"Если это тот же пациент, используйте существующую запись. "
                        f"ID: {top_match['patient'].id}"
                    )
                elif top_match['confidence'] == 'medium':
                    # Medium confidence - show warning
                    logger.warning(f"Potential duplicate patient: {top_match['message']}")
                    # We'll let it pass but log it
                    # In production, you might want to add a confirmation step here

        return cleaned_data

class PatientQuickForm(forms.ModelForm):
    """Simplified form for quick patient registration during booking"""

    gender = forms.ChoiceField(
        label=_('Пол'),
        choices=((True, _('Мужской')), (False, _('Женский'))),
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=True
    )

    class Meta:
        model = PatientModel
        fields = ['f_name', 'l_name', 'mid_name', 'date_of_birth', 'gender', 'mobile_phone_number']
        labels = {
            'f_name': _('Имя'),
            'l_name': _('Фамилия'),
            'mid_name': _('Отчество'),
            'date_of_birth': _('Дата рождения'),
            'mobile_phone_number': _('Мобильный телефон'),
        }
        widgets = {
            'f_name': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'l_name': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'mid_name': forms.TextInput(attrs={'class': 'form-control'}),
            'date_of_birth': forms.DateInput(attrs={
                'class': 'form-control datetimepicker-input',
                'data-target': '#quickDateOfBirth',
                'placeholder': 'ДД.MM.ГГГГ',
                'required': True
            }),
            'mobile_phone_number': forms.TextInput(attrs={
                'class': 'form-control',
                'data-inputmask': '"mask": "+\\9\\98 99 999-99-99"',
                'data-mask': True,
                'required': True
            }),
        }
