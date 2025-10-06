import csv
from datetime import datetime
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.utils import timezone

from application.logus.forms.payments import PaymentForm
from core.models import Booking, TransactionsModel


@login_required
def payments_dashboard(request):
    date_from_str = request.GET.get('date_from')
    date_to_str = request.GET.get('date_to')

    date_from = _parse_date(date_from_str)
    date_to = _parse_date(date_to_str)

    bookings_qs = Booking.objects.select_related('staff').prefetch_related(
        'details__client',
        'additional_services',
        'transactions'
    ).order_by('-created_at')

    bookings_data = []
    outstanding_map = {}
    booking_patients_map = {}
    total_expected = Decimal('0.00')
    total_collected = Decimal('0.00')

    for booking in bookings_qs:
        details_total = sum((detail.price or Decimal('0.00')) for detail in booking.details.all())
        services_total = sum((service.price or Decimal('0.00')) for service in booking.additional_services.all())
        booking_total = details_total + services_total
        paid_amount = sum((payment.amount or Decimal('0.00')) for payment in booking.transactions.all())
        outstanding = booking_total - paid_amount

        total_expected += booking_total
        total_collected += paid_amount

        clients = [
            {
                'id': detail.client.id,
                'name': detail.client.full_name,
                'phone': detail.client.mobile_phone_number
            }
            for detail in booking.details.all()
        ]

        booking_patients_map[booking.id] = [
            {'id': client['id'], 'name': client['name']}
            for client in clients
        ]
        outstanding_map[booking.id] = outstanding

        last_payment = None
        if booking.transactions.exists():
            last_payment = booking.transactions.order_by('-created_at').first()

        bookings_data.append({
            'booking': booking,
            'clients': clients,
            'details_total': details_total,
            'services_total': services_total,
            'total_amount': booking_total,
            'paid_amount': paid_amount,
            'outstanding': outstanding,
            'last_payment': last_payment,
        })

    bookings_with_outstanding = [b for b in bookings_data if b['outstanding'] > Decimal('0.00')]
    bookings_with_outstanding.sort(key=lambda item: item['outstanding'], reverse=True)

    total_outstanding = total_expected - total_collected

    outstanding_display_map = {
        booking_id: format(amount, '.2f')
        for booking_id, amount in outstanding_map.items()
    }

    today = timezone.localdate()
    today_collected = TransactionsModel.objects.filter(created_at__date=today).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    transactions_qs = TransactionsModel.objects.select_related('booking', 'patient', 'created_by')
    if date_from:
        transactions_qs = transactions_qs.filter(created_at__date__gte=date_from)
    if date_to:
        transactions_qs = transactions_qs.filter(created_at__date__lte=date_to)

    if request.GET.get('export') == 'transactions':
        return _export_transactions(transactions_qs, date_from, date_to)

    transaction_breakdown = []
    for row in transactions_qs.values('transaction_type').annotate(total=Sum('amount')).order_by('-total'):
        transaction_code = row['transaction_type']
        try:
            transaction_label = TransactionsModel.TransactionType(transaction_code).label
        except ValueError:
            transaction_label = 'Не указано'
        transaction_breakdown.append({
            'code': transaction_code,
            'label': transaction_label,
            'total': row['total'] or Decimal('0.00')
        })

    recent_transactions = transactions_qs.order_by('-created_at')[:10]

    report_total = sum(
        (item['total'] or Decimal('0.00')) for item in transaction_breakdown
    , Decimal('0.00'))
    report_count = transactions_qs.count()

    form_kwargs = {
        'booking_queryset': Booking.objects.order_by('-created_at'),
        'outstanding_map': outstanding_map,
    }

    if request.method == 'POST':
        form = PaymentForm(request.POST, **form_kwargs)
        if form.is_valid():
            with transaction.atomic():
                payment = form.save(commit=False)
                payment.created_by = request.user
                payment.modified_by = request.user
                payment.save()
            messages.success(request, 'Платеж успешно зарегистрирован.')
            return redirect('logus:payments_dashboard')
        else:
            messages.error(request, 'Пожалуйста, исправьте ошибки в форме платежа.')
    else:
        form = PaymentForm(**form_kwargs)

    context = {
        'form': form,
        'bookings': bookings_data,
        'bookings_with_outstanding': bookings_with_outstanding,
        'recent_transactions': recent_transactions,
        'transaction_breakdown': transaction_breakdown,
        'stats': {
            'total_expected': total_expected,
            'total_collected': total_collected,
            'total_outstanding': total_outstanding,
            'today_collected': today_collected,
            'outstanding_bookings': len(bookings_with_outstanding),
            'range_total': report_total,
            'range_count': report_count,
        },
        'booking_patients_map': booking_patients_map,
        'outstanding_display_map': outstanding_display_map,
        'filter_values': {
            'date_from': date_from_str or '',
            'date_to': date_to_str or '',
        },
        'report_summary': {
            'total': report_total,
            'count': report_count,
        },
        'filter_applied': bool(date_from or date_to),
    }

    return render(request, 'logus/payments/dashboard.html', context)


def _parse_date(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, '%Y-%m-%d').date()
    except (TypeError, ValueError):
        return None


def _export_transactions(transactions_qs, date_from, date_to):
    filename_parts = ['payments']
    if date_from:
        filename_parts.append(date_from.strftime('%Y%m%d'))
    if date_to:
        filename_parts.append(date_to.strftime('%Y%m%d'))
    filename = '_'.join(filename_parts) + '.csv'

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    writer = csv.writer(response)
    writer.writerow(['Дата', 'Бронирование', 'Пациент', 'Сумма', 'Способ оплаты', 'Кассир'])

    for transaction in transactions_qs.order_by('created_at'):
        writer.writerow([
            transaction.created_at.strftime('%d.%m.%Y %H:%M'),
            transaction.booking.booking_number if transaction.booking else '',
            transaction.patient.full_name if transaction.patient else '',
            format(transaction.amount, '.2f'),
            transaction.get_transaction_type_display(),
            transaction.created_by.full_name if transaction.created_by else '',
        ])

    return response
