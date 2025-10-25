from django import forms
from core.models import DeliveryCompanyModel


class DeliveryCompanyForm(forms.ModelForm):
    class Meta:
        model = DeliveryCompanyModel
        fields = [
            'name', 'contact_person', 'phone_number', 'email',
            'address', 'city', 'country', 'postal_code',
            'contract_number', 'contract_start_date', 'contract_end_date',
            'is_active', 'notes'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Название компании'}),
            'contact_person': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Контактное лицо'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Номер телефона'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Адрес', 'rows': 3}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Город'}),
            'country': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Страна'}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Почтовый индекс'}),
            'contract_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Номер контракта'}),
            'contract_start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'contract_end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Примечания', 'rows': 3}),
        }

    def clean_name(self):
        name = self.cleaned_data['name']
        # Check if name already exists for a different company
        if DeliveryCompanyModel.objects.filter(name__iexact=name).exclude(
                pk=self.instance.pk if self.instance else None).exists():
            raise forms.ValidationError('Компания доставки с таким названием уже существует.')
        return name