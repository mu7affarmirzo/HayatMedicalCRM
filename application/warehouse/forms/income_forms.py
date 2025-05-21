from django import forms
from django.forms import formset_factory, inlineformset_factory
from core.models import IncomeModel, IncomeItemsModel, MedicationModel, Warehouse, CompanyModel


class IncomeForm(forms.ModelForm):
    """
    Form for creating and updating Income receipts
    """

    class Meta:
        model = IncomeModel
        fields = ['delivery_company', 'receiver', 'bill_amount', 'state']
        widgets = {
            'delivery_company': forms.Select(attrs={'class': 'form-control select2bs4'}),
            'receiver': forms.Select(attrs={'class': 'form-control select2bs4'}),
            'bill_amount': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'state': forms.Select(attrs={'class': 'form-control'})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['delivery_company'].queryset = CompanyModel.objects.all()
        self.fields['receiver'].queryset = Warehouse.objects.all()

        self.fields['delivery_company'].label = 'Компания-поставщик'
        self.fields['receiver'].label = 'Склад-получатель'
        self.fields['bill_amount'].label = 'Сумма счета'
        self.fields['state'].label = 'Статус'

        # Make receiver required
        self.fields['receiver'].required = True

        # Set default state to pending
        self.fields['state'].initial = 'в ожидании'


class IncomeItemForm(forms.ModelForm):
    """
    Form for Income Item entries
    """

    class Meta:
        model = IncomeItemsModel
        fields = ['item', 'quantity', 'unit_quantity', 'price', 'unit_price', 'nds', 'expire_date']
        widgets = {
            'item': forms.Select(attrs={'class': 'form-control select2bs4 medication-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control quantity-input', 'min': '0'}),
            'unit_quantity': forms.NumberInput(attrs={'class': 'form-control unit-quantity-input', 'min': '0'}),
            'price': forms.NumberInput(attrs={'class': 'form-control price-input', 'min': '0'}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control unit-price-input', 'min': '0'}),
            'nds': forms.NumberInput(attrs={'class': 'form-control nds-input', 'min': '0', 'max': '100'}),
            'expire_date': forms.DateInput(attrs={'class': 'form-control datepicker', 'type': 'date'})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['item'].queryset = MedicationModel.objects.all()

        self.fields['item'].label = 'Лекарство'
        self.fields['quantity'].label = 'Количество (упаковок)'
        self.fields['unit_quantity'].label = 'Количество (единиц)'
        self.fields['price'].label = 'Цена (за упаковку)'
        self.fields['unit_price'].label = 'Цена (за единицу)'
        self.fields['nds'].label = 'НДС (%)'
        self.fields['expire_date'].label = 'Срок годности'

        # Make item and quantity required
        self.fields['item'].required = True
        self.fields['quantity'].required = True
        self.fields['expire_date'].required = True

        # Make unit_quantity, unit_price, and nds optional with defaults
        self.fields['unit_quantity'].required = False
        self.fields['unit_quantity'].initial = 0

        self.fields['unit_price'].required = False
        self.fields['unit_price'].initial = 0

        self.fields['nds'].required = False
        self.fields['nds'].initial = 0


# Create a formset for IncomeItems
IncomeItemFormSet = inlineformset_factory(
    IncomeModel,
    IncomeItemsModel,
    form=IncomeItemForm,
    extra=1,
    can_delete=True
)