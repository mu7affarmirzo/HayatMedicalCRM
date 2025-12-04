# Add these to your existing forms.py file
from django import forms

from core.models import MedicationModel, CompanyModel


class MedicationForm(forms.ModelForm):
    """
    Form for creating and updating medications
    """

    class Meta:
        model = MedicationModel
        fields = ['name', 'company', 'in_pack', 'unit', 'batch_number',
                  'manufacture_date', 'description',
                  'dosage_form', 'active_ingredients', 'contraindications', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'company': forms.Select(attrs={'class': 'form-control select2bs4'}),
            'in_pack': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'unit': forms.Select(attrs={'class': 'form-control'}),
            'batch_number': forms.TextInput(attrs={'class': 'form-control'}),
            'manufacture_date': forms.DateInput(attrs={'class': 'form-control datepicker', 'type': 'date'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'dosage_form': forms.TextInput(attrs={'class': 'form-control'}),
            'active_ingredients': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'contraindications': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['company'].queryset = CompanyModel.objects.all()

        # Set field labels in Russian
        self.fields['name'].label = 'Наименование'
        self.fields['company'].label = 'Компания-производитель'
        self.fields['in_pack'].label = 'Количество в упаковке'
        self.fields['unit'].label = 'Единица измерения'
        self.fields['batch_number'].label = 'Номер партии'
        self.fields['manufacture_date'].label = 'Дата производства'
        self.fields['description'].label = 'Описание'
        self.fields['dosage_form'].label = 'Форма выпуска'
        self.fields['active_ingredients'].label = 'Активные ингредиенты'
        self.fields['contraindications'].label = 'Противопоказания'
        self.fields['is_active'].label = 'Активен'

        # Make required fields
        self.fields['name'].required = True
        self.fields['company'].required = True
        self.fields['in_pack'].required = True
        self.fields['unit'].required = True

