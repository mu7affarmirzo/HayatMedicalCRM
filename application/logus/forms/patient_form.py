from django import forms
from django.utils.translation import gettext_lazy as _
import datetime

from core.models import PatientModel


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
    """Form for patient registration with improved validation and UI enhancements"""

    # Override fields for better UI
    # date_of_birth = forms.DateField(
    #     label=_('Дата рождения'),
    #     widget=forms.TextInput(attrs={
    #         'class': 'form-control datetimepicker-input',
    #         'data-target': '#dateOfBirth',
    #         'placeholder': 'ДД.MM.ГГГГ'
    #     }),
    #     required=True,
    #     help_text=_('Формат: ДД.MM.ГГГГ')
    # )
    date_of_birth = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'placeholder': 'YYYY-MM-DD'}),
        input_formats=['%Y-%m-%d', '%m/%d/%Y', '%m/%d/%y']
    )

    gender = forms.ChoiceField(
        label=_('Пол'),
        choices=((True, _('Мужской')), (False, _('Женский'))),
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=True
    )

    # Convert Boolean field to more user-friendly ChoiceField
    is_active = forms.ChoiceField(
        label=_('Статус'),
        choices=((True, _('Активный')), (False, _('Неактивный'))),
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=False,
        initial=True
    )

    # Add widget attributes for all fields
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Apply custom styling to all fields
        for field_name, field in self.fields.items():
            # Skip fields that already have custom widgets
            if field_name in ['date_of_birth', 'gender', 'is_active']:
                continue

            # Add Bootstrap classes to form controls
            if isinstance(field.widget, (forms.TextInput, forms.NumberInput, forms.EmailInput)):
                field.widget.attrs.update({'class': 'form-control'})
            elif isinstance(field.widget, forms.Textarea):
                field.widget.attrs.update({'class': 'form-control', 'rows': 3})
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs.update({'class': 'form-control select2'})

        # Make region and district use select2
        if 'region' in self.fields:
            self.fields['region'].widget.attrs.update({'class': 'form-control select2', 'style': 'width: 100%;'})

        if 'district' in self.fields:
            self.fields['district'].widget.attrs.update({'class': 'form-control select2', 'style': 'width: 100%;'})

            # Disable district field initially if no region is selected
            if not self.initial.get('region'):
                self.fields['district'].widget.attrs['disabled'] = 'disabled'

    def clean(self):
        """Custom validation to ensure district belongs to selected region"""
        cleaned_data = super().clean()
        region = cleaned_data.get('region')
        district = cleaned_data.get('district')

        if district and region and district.region != region:
            self.add_error('district', _('Выбранный район не принадлежит выбранному региону'))

        return cleaned_data

    class Meta:
        model = PatientModel
        fields = [
            'f_name', 'l_name', 'mid_name',
            'date_of_birth', 'gender', 'gestational_age',
            'mobile_phone_number', 'home_phone_number', 'email',
            'country', 'region', 'district', 'address',
            'doc_type', 'doc_number', 'INN', 'additional_info',
            'is_active'
        ]
        labels = {
            'f_name': _('Имя'),
            'l_name': _('Фамилия'),
            'mid_name': _('Отчество'),
            'gestational_age': _('Гестационный возраст (недель)'),
            'mobile_phone_number': _('Мобильный телефон'),
            'home_phone_number': _('Домашний телефон'),
            'email': _('Email'),
            'country': _('Страна'),
            'region': _('Регион'),
            'district': _('Район'),
            'address': _('Адрес'),
            'doc_type': _('Тип документа'),
            'doc_number': _('Номер документа'),
            'INN': _('ИНН'),
            'additional_info': _('Дополнительная информация'),
            'is_active': _('Активный')
        }
        help_texts = {
            'mobile_phone_number': _('Формат: +998 XX XXX-XX-XX'),
            'home_phone_number': _('Формат: +998 XX XXX-XX-XX'),
            'INN': _('Индивидуальный номер налогоплательщика'),
            'gestational_age': _('Только для пациентов-младенцев')
        }
        error_messages = {
            'f_name': {'required': _('Необходимо указать имя')},
            'l_name': {'required': _('Необходимо указать фамилию')},
            'date_of_birth': {'required': _('Необходимо указать дату рождения')},
            'gender': {'required': _('Необходимо указать пол')}
        }


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
