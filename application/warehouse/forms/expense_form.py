from django import forms
from core.models import MedicationExpenseModel, MedicationsInStockModel, Warehouse


class MedicationExpenseForm(forms.ModelForm):
    """
    Form for creating medication expenses (write-offs)
    """

    # Custom fields for easier filtering
    warehouse = forms.ModelChoiceField(
        queryset=Warehouse.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'warehouse-filter'}),
        label='Склад'
    )

    class Meta:
        model = MedicationExpenseModel
        fields = ['stock_item', 'expense_type', 'quantity', 'unit_quantity', 'expense_date', 'reason']
        widgets = {
            'stock_item': forms.Select(attrs={'class': 'form-control select2bs4', 'id': 'stock-item-select'}),
            'expense_type': forms.Select(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'value': '0'}),
            'unit_quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'value': '0'}),
            'expense_date': forms.DateInput(attrs={'class': 'form-control datepicker', 'type': 'date'}),
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Filter only stock items with available quantity
        self.fields['stock_item'].queryset = MedicationsInStockModel.objects.filter(
            quantity__gt=0
        ).select_related('item', 'warehouse', 'item__company').order_by('item__name', 'expire_date')

        # Set field labels in Russian
        self.fields['stock_item'].label = 'Медикамент (партия)'
        self.fields['expense_type'].label = 'Тип расхода'
        self.fields['quantity'].label = 'Количество упаковок'
        self.fields['unit_quantity'].label = 'Количество единиц'
        self.fields['expense_date'].label = 'Дата расхода'
        self.fields['reason'].label = 'Причина/Примечание'

        # Make required fields
        self.fields['stock_item'].required = True
        self.fields['expense_type'].required = True
        self.fields['expense_date'].required = True

        # Custom label method to show more details in dropdown
        self.fields['stock_item'].label_from_instance = self.stock_item_label

    @staticmethod
    def stock_item_label(obj):
        """Custom label for stock items in dropdown"""
        available_packs = obj.quantity
        available_units = obj.unit_quantity
        warehouse_name = obj.warehouse.name
        expire_date = obj.expire_date.strftime('%d.%m.%Y') if obj.expire_date else 'Нет срока'

        return f"{obj.item.name} ({warehouse_name}) - {available_packs} уп. {available_units} ед. - Срок: {expire_date}"

    def clean(self):
        cleaned_data = super().clean()
        stock_item = cleaned_data.get('stock_item')
        quantity = cleaned_data.get('quantity', 0)
        unit_quantity = cleaned_data.get('unit_quantity', 0)

        if stock_item:
            # Check if there's enough stock
            available_packs = stock_item.quantity
            available_units = stock_item.unit_quantity

            # Convert everything to units for comparison
            in_pack = stock_item.item.in_pack
            requested_total_units = (quantity * in_pack) + unit_quantity
            available_total_units = (available_packs * in_pack) + available_units

            if requested_total_units > available_total_units:
                raise forms.ValidationError(
                    f'Недостаточно медикаментов на складе. Доступно: {available_packs} уп. {available_units} ед. '
                    f'(всего {available_total_units} единиц). Запрошено: {requested_total_units} единиц.'
                )

            # Ensure at least some quantity is specified
            if requested_total_units == 0:
                raise forms.ValidationError('Необходимо указать количество для списания.')

        return cleaned_data
