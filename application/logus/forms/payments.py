from decimal import Decimal

from django import forms
from django.db.models import Sum

from core.models import Booking, PatientModel, TransactionsModel


class PaymentForm(forms.ModelForm):
    amount = forms.DecimalField(
        label='Сумма платежа',
        min_value=Decimal('0.01'),
        max_digits=20,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'})
    )

    class Meta:
        model = TransactionsModel
        fields = ['booking', 'patient', 'amount', 'transaction_type']
        labels = {
            'booking': 'Бронирование',
            'patient': 'Пациент',
            'transaction_type': 'Способ оплаты',
        }
        widgets = {
            'booking': forms.Select(attrs={'class': 'form-control select2'}),
            'patient': forms.Select(attrs={'class': 'form-control select2'}),
            'transaction_type': forms.Select(attrs={'class': 'form-control select2'}),
        }

    def __init__(self, *args, booking_queryset=None, outstanding_map=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['booking'].queryset = booking_queryset or Booking.objects.order_by('-created_at')
        self.fields['patient'].queryset = PatientModel.objects.filter(is_active=True).order_by('l_name', 'f_name')

        self.outstanding_map = outstanding_map or {}

        booking_value = self.data.get(self.add_prefix('booking')) or self.initial.get('booking')
        if self.instance and self.instance.pk:
            booking_value = booking_value or self.instance.booking_id

        try:
            booking_id = int(booking_value) if booking_value else None
        except (TypeError, ValueError):
            booking_id = None

        if booking_id:
            patients_qs = PatientModel.objects.filter(bookings__booking_id=booking_id).distinct()
            if patients_qs.exists():
                self.fields['patient'].queryset = patients_qs.order_by('l_name', 'f_name')

    def clean(self):
        cleaned_data = super().clean()
        booking = cleaned_data.get('booking')
        patient = cleaned_data.get('patient')
        amount = cleaned_data.get('amount')

        if booking and patient:
            if not booking.details.filter(client=patient).exists():
                self.add_error('patient', 'Выбранный пациент не связан с этим бронированием.')

        if booking and amount:
            outstanding = self.outstanding_map.get(booking.id)
            if outstanding is None:
                outstanding = self._calculate_outstanding(booking)
            if outstanding <= Decimal('0.00'):
                self.add_error('booking', 'По данному бронированию нет задолженности.')
            elif amount > outstanding:
                self.add_error('amount', 'Сумма платежа превышает текущую задолженность.')

        return cleaned_data

    def _calculate_outstanding(self, booking):
        details_total = booking.details.aggregate(total=Sum('price'))['total'] or Decimal('0.00')
        services_total = booking.additional_services.aggregate(total=Sum('price'))['total'] or Decimal('0.00')
        paid_total = booking.transactions.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        return details_total + services_total - paid_total
