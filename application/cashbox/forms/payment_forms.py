from django import forms
from decimal import Decimal
from django.db.models import Sum
from core.models import TransactionsModel, BookingBilling


class PaymentAcceptanceForm(forms.Form):
    """Form for accepting payment for a booking"""

    PAYMENT_METHOD_CHOICES = [
        ('cash', 'Наличные (Cash)'),
        ('card', 'Банковская карта (Card)'),
        ('uzcard', 'UzCard'),
        ('humo', 'Humo'),
        ('payme', 'PayMe'),
        ('click', 'Click'),
        ('transfer', 'Банковский перевод (Transfer)'),
    ]

    amount = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        label='Сумма оплаты',
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите сумму',
            'step': '0.01',
            'min': '0'
        })
    )

    payment_method = forms.ChoiceField(
        choices=PAYMENT_METHOD_CHOICES,
        label='Способ оплаты',
        widget=forms.Select(attrs={
            'class': 'form-control select2'
        })
    )

    reference_number = forms.CharField(
        max_length=100,
        required=False,
        label='Номер транзакции (необязательно)',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Номер чека, карты и т.д.'
        }),
        help_text='Для карт/онлайн платежей укажите номер транзакции'
    )

    notes = forms.CharField(
        required=False,
        label='Примечания',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Дополнительная информация'
        })
    )

    def __init__(self, *args, billing=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.billing = billing

        if billing:
            # Pre-fill amount with remaining balance
            remaining = self.calculate_remaining_balance(billing)
            self.fields['amount'].initial = remaining
            self.fields['amount'].widget.attrs['max'] = str(remaining)

    def calculate_remaining_balance(self, billing):
        """Calculate how much is still owed"""
        total_paid = billing.transactions.filter(
            status='COMPLETED'
        ).aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0')

        remaining = Decimal(str(billing.total_amount)) - total_paid
        return max(remaining, Decimal('0'))

    def clean_amount(self):
        """Validate payment amount"""
        amount = self.cleaned_data.get('amount')

        if amount <= 0:
            raise forms.ValidationError('Сумма должна быть больше нуля')

        if self.billing:
            remaining = self.calculate_remaining_balance(self.billing)
            if amount > remaining:
                raise forms.ValidationError(
                    f'Сумма превышает остаток: {remaining:,.2f} сум'
                )

        return amount

    def clean(self):
        """Validate form data"""
        cleaned_data = super().clean()
        payment_method = cleaned_data.get('payment_method')
        reference_number = cleaned_data.get('reference_number')

        # Require reference number for non-cash payments
        if payment_method in ['card', 'payme', 'click', 'uzcard', 'humo']:
            if not reference_number:
                self.add_error(
                    'reference_number',
                    'Номер транзакции обязателен для безналичных платежей'
                )

        return cleaned_data


class RefundPaymentForm(forms.Form):
    """Form for refunding a payment"""

    refund_amount = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        label='Сумма возврата',
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите сумму возврата',
            'step': '0.01',
            'min': '0'
        }),
        help_text='Оставьте пустым для полного возврата'
    )

    refund_reason = forms.CharField(
        max_length=500,
        required=True,
        label='Причина возврата',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Укажите причину возврата (обязательно)'
        })
    )

    confirm = forms.BooleanField(
        required=True,
        label='Подтверждаю возврат средств',
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )

    def __init__(self, *args, payment=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.payment = payment

        if payment:
            # Pre-fill with full payment amount
            self.fields['refund_amount'].initial = payment.amount
            self.fields['refund_amount'].widget.attrs['max'] = str(payment.amount)

    def clean_refund_amount(self):
        """Validate refund amount"""
        amount = self.cleaned_data.get('refund_amount')

        if amount <= 0:
            raise forms.ValidationError('Сумма возврата должна быть больше нуля')

        if self.payment and amount > self.payment.amount:
            raise forms.ValidationError(
                f'Сумма возврата не может превышать сумму платежа: {self.payment.amount:,.2f} сум'
            )

        return amount

    def clean(self):
        """Additional validation"""
        cleaned_data = super().clean()

        if self.payment:
            if self.payment.status == 'REFUNDED':
                raise forms.ValidationError('Этот платеж уже возвращен')

            if self.payment.status != 'COMPLETED':
                raise forms.ValidationError('Можно вернуть только завершенные платежи')

        return cleaned_data
