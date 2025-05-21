# Add these to your existing forms.py file
from django import forms

from core.models import Warehouse, MedicationModel, MedicationsInStockModel


class WarehouseForm(forms.ModelForm):
    """
    Form for creating and updating warehouses
    """

    class Meta:
        model = Warehouse
        fields = ['name', 'address', 'email', 'is_main', 'is_emergency']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'is_main': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_emergency': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Set field labels in Russian
        self.fields['name'].label = 'Название'
        self.fields['address'].label = 'Адрес'
        self.fields['email'].label = 'Email'
        self.fields['is_main'].label = 'Основной склад'
        self.fields['is_emergency'].label = 'Экстренный склад'

        # Make required fields
        self.fields['name'].required = True
        self.fields['address'].required = True
        self.fields['email'].required = True

    def clean(self):
        cleaned_data = super().clean()
        is_main = cleaned_data.get('is_main')

        # Check if another warehouse is already set as main
        if is_main and not self.instance.pk:
            # This is a new warehouse being created with is_main=True
            if Warehouse.objects.filter(is_main=True).exists():
                self.add_error('is_main', 'Уже существует основной склад. Может быть только один основной склад.')

        if is_main and self.instance.pk:
            # This is an existing warehouse being updated with is_main=True
            if Warehouse.objects.exclude(pk=self.instance.pk).filter(is_main=True).exists():
                self.add_error('is_main', 'Уже существует основной склад. Может быть только один основной склад.')

        return cleaned_data


class TransferForm(forms.Form):
    """
    Form for transferring medications between warehouses
    """
    source_warehouse = forms.ModelChoiceField(
        queryset=Warehouse.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control select2bs4'}),
        label='Склад-источник'
    )

    destination_warehouse = forms.ModelChoiceField(
        queryset=Warehouse.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control select2bs4'}),
        label='Склад-получатель'
    )

    medication = forms.ModelChoiceField(
        queryset=MedicationModel.objects.filter(is_active=True),
        widget=forms.Select(attrs={'class': 'form-control select2bs4'}),
        label='Лекарство'
    )

    batch = forms.ChoiceField(
        choices=[],
        widget=forms.Select(attrs={'class': 'form-control select2bs4'}),
        label='Партия',
        required=False
    )

    quantity = forms.IntegerField(
        min_value=0,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
        label='Количество (упаковок)'
    )

    unit_quantity = forms.IntegerField(
        min_value=0,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
        label='Количество (единиц)',
        required=False,
        initial=0
    )

    notes = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        label='Примечания',
        required=False
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Initialize with empty batch choices
        self.fields['batch'].choices = [('', '-- Выберите партию --')]

        # If form is being re-rendered after an invalid submission
        if 'source_warehouse' in self.data and 'medication' in self.data:
            try:
                source_warehouse_id = int(self.data.get('source_warehouse'))
                medication_id = int(self.data.get('medication'))

                # Get batches for this medication in source warehouse
                batches = MedicationsInStockModel.objects.filter(
                    warehouse_id=source_warehouse_id,
                    item_id=medication_id,
                    quantity__gt=0
                ).values_list('income_seria', 'expire_date', 'quantity', 'unit_quantity')

                batch_choices = []
                for seria, expire_date, qty, unit_qty in batches:
                    label = f"{seria} - Срок годности: {expire_date.strftime('%d.m.Y')} - Остаток: {qty} уп. + {unit_qty} ед."
                    batch_choices.append((seria, label))

                self.fields['batch'].choices = [('', '-- Выберите партию --')] + batch_choices
            except (ValueError, TypeError):
                pass

    def clean(self):
        cleaned_data = super().clean()
        source_warehouse = cleaned_data.get('source_warehouse')
        destination_warehouse = cleaned_data.get('destination_warehouse')
        medication = cleaned_data.get('medication')
        batch = cleaned_data.get('batch')
        quantity = cleaned_data.get('quantity', 0)
        unit_quantity = cleaned_data.get('unit_quantity', 0)

        # Check that source and destination warehouses are different
        if source_warehouse and destination_warehouse and source_warehouse == destination_warehouse:
            self.add_error('destination_warehouse', 'Склад-источник и склад-получатель должны быть разными.')

        # Check that the requested quantity is available
        if source_warehouse and medication and batch and (quantity > 0 or unit_quantity > 0):
            try:
                stock_item = MedicationsInStockModel.objects.get(
                    warehouse=source_warehouse,
                    item=medication,
                    income_seria=batch
                )

                # Calculate total units
                requested_total_units = (quantity * medication.in_pack) + unit_quantity
                available_total_units = (stock_item.quantity * medication.in_pack) + stock_item.unit_quantity

                if requested_total_units > available_total_units:
                    self.add_error('quantity',
                                   f'Недостаточно запасов. Доступно: {stock_item.quantity} упаковок + {stock_item.unit_quantity} единиц.')
            except MedicationsInStockModel.DoesNotExist:
                self.add_error('batch', 'Выбранная партия не найдена.')

        return cleaned_data

