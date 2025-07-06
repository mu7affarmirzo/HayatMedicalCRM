from django import forms

from core.models import PatientModel


class PatientRegistrationForm(forms.ModelForm):
    date_of_birth = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'placeholder': 'YYYY-MM-DD'}),
        input_formats=['%Y-%m-%d', '%m/%d/%Y', '%m/%d/%y']
    )

    class Meta:
        model = PatientModel
        fields = [
            'f_name', 'mid_name', 'l_name', 'address',
            'date_of_birth', 'mobile_phone_number', 'gender', 'INN'
        ]


class PatientForm(forms.ModelForm):
    class Meta:
        model = PatientModel
        fields = [
            'f_name', 'l_name', 'mid_name', 'date_of_birth', 'gender',
            'gestational_age', 'mobile_phone_number',
            'home_phone_number',
            'email', 'country', 'region', 'district', 'address',
            'doc_type', 'doc_number', 'INN', 'additional_info'
        ]
