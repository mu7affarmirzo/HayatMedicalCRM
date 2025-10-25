from django import forms
from core.models import BookingBilling, Booking


class BillingFilterForm(forms.Form):
    """Form for filtering billing records"""
    
    STATUS_CHOICES = [
        ('', 'Все статусы'),
    ] + list(Booking.BookingStatus.choices)
    
    BILLING_STATUS_CHOICES = [
        ('', 'Все статусы'),
    ] + list(BookingBilling.BillingStatus.choices)
    
    search = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Поиск по номеру или пациенту'
        })
    )
    
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control select2'})
    )
    
    billing_status = forms.ChoiceField(
        choices=BILLING_STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control select2'})
    )
    
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )


class BillingActionForm(forms.Form):
    """Form for performing actions on billing records"""
    
    ACTION_CHOICES = [
        ('calculate_billing', 'Рассчитать счет'),
        ('mark_invoiced', 'Выставить счет'),
        ('mark_paid', 'Отметить как оплачено'),
    ]
    
    action = forms.ChoiceField(
        choices=ACTION_CHOICES,
        widget=forms.HiddenInput()
    )