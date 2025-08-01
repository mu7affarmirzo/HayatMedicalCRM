from django import forms
from django.utils.translation import gettext_lazy as _
import datetime

from core.models import PatientModel, Region, District


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


class PatientRegistrationForm(forms.ModelForm):


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
            'home_phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'mobile_phone_number': forms.TextInput(attrs={'class': 'form-control'}),
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
