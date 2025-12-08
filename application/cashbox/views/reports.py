from django.shortcuts import render
from django.db.models import Sum, Count, Q, F
from django.db.models.functions import TruncDate
from decimal import Decimal
from datetime import datetime, timedelta

from HayatMedicalCRM.auth.decorators import cashbox_required
from core.models import TransactionsModel, Account


@cashbox_required
def report_daily(request):
    """
    Daily cash report for the current cashier
    """
    # Get date parameter or use today
    date_str = request.GET.get('date', '')
    if date_str:
        try:
            report_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            report_date = datetime.now().date()
    else:
        report_date = datetime.now().date()

    # Get transactions for the selected date
    transactions = TransactionsModel.objects.filter(
        created_at__date=report_date,
        created_by=request.user,
        status='COMPLETED'
    ).select_related('patient', 'booking', 'billing')

    # Calculate totals by payment method
    payment_methods_stats = {}
    for method in TransactionsModel.TransactionType.choices:
        method_transactions = transactions.filter(transaction_type=method[0])
        total = method_transactions.aggregate(Sum('amount'))['amount__sum'] or Decimal('0')
        count = method_transactions.count()

        payment_methods_stats[method[0]] = {
            'label': method[1],
            'count': count,
            'total': total,
            'transactions': method_transactions
        }

    # Overall statistics
    total_payments = transactions.filter(amount__gt=0).aggregate(Sum('amount'))['amount__sum'] or Decimal('0')
    total_refunds = abs(transactions.filter(amount__lt=0).aggregate(Sum('amount'))['amount__sum'] or Decimal('0'))
    net_total = total_payments - total_refunds

    context = {
        'report_date': report_date,
        'transactions': transactions,
        'payment_methods_stats': payment_methods_stats,
        'total_payments': total_payments,
        'total_refunds': total_refunds,
        'net_total': net_total,
        'transaction_count': transactions.count(),
        'cashier': request.user,
    }

    return render(request, 'cashbox/reports/daily_report.html', context)


@cashbox_required
def report_period(request):
    """
    Period report with customizable date range
    """
    # Get date range parameters
    date_from_str = request.GET.get('date_from', '')
    date_to_str = request.GET.get('date_to', '')

    # Default to current month
    if date_from_str:
        try:
            date_from = datetime.strptime(date_from_str, '%Y-%m-%d').date()
        except ValueError:
            date_from = datetime.now().date().replace(day=1)
    else:
        date_from = datetime.now().date().replace(day=1)

    if date_to_str:
        try:
            date_to = datetime.strptime(date_to_str, '%Y-%m-%d').date()
        except ValueError:
            date_to = datetime.now().date()
    else:
        date_to = datetime.now().date()

    # Get transactions for the period
    transactions = TransactionsModel.objects.filter(
        created_at__date__gte=date_from,
        created_at__date__lte=date_to,
        status='COMPLETED'
    ).select_related('patient', 'booking', 'created_by')

    # Statistics by payment method
    payment_methods_stats = {}
    for method in TransactionsModel.TransactionType.choices:
        method_transactions = transactions.filter(transaction_type=method[0])
        total = method_transactions.aggregate(Sum('amount'))['amount__sum'] or Decimal('0')
        count = method_transactions.count()

        payment_methods_stats[method[0]] = {
            'label': method[1],
            'count': count,
            'total': total
        }

    # Statistics by cashier
    cashiers_stats = transactions.values(
        'created_by__id',
        'created_by__username',
        'created_by__f_name',
        'created_by__l_name'
    ).annotate(
        transaction_count=Count('id'),
        total_amount=Sum('amount')
    ).order_by('-total_amount')

    # Daily breakdown
    daily_stats = transactions.annotate(
        date=TruncDate('created_at')
    ).values('date').annotate(
        count=Count('id'),
        total=Sum('amount')
    ).order_by('date')

    # Overall statistics
    total_payments = transactions.filter(amount__gt=0).aggregate(Sum('amount'))['amount__sum'] or Decimal('0')
    total_refunds = abs(transactions.filter(amount__lt=0).aggregate(Sum('amount'))['amount__sum'] or Decimal('0'))
    net_total = total_payments - total_refunds

    context = {
        'date_from': date_from,
        'date_to': date_to,
        'transactions': transactions,
        'payment_methods_stats': payment_methods_stats,
        'cashiers_stats': cashiers_stats,
        'daily_stats': daily_stats,
        'total_payments': total_payments,
        'total_refunds': total_refunds,
        'net_total': net_total,
        'transaction_count': transactions.count(),
    }

    return render(request, 'cashbox/reports/period_report.html', context)


@cashbox_required
def report_cashier(request):
    """
    Individual cashier performance report
    """
    # Get cashier ID or use current user
    cashier_id = request.GET.get('cashier_id', '')
    if cashier_id:
        try:
            cashier = Account.objects.get(id=cashier_id)
        except Account.DoesNotExist:
            cashier = request.user
    else:
        cashier = request.user

    # Get date range
    date_from_str = request.GET.get('date_from', '')
    date_to_str = request.GET.get('date_to', '')

    if date_from_str:
        try:
            date_from = datetime.strptime(date_from_str, '%Y-%m-%d').date()
        except ValueError:
            date_from = datetime.now().date().replace(day=1)
    else:
        date_from = datetime.now().date().replace(day=1)

    if date_to_str:
        try:
            date_to = datetime.strptime(date_to_str, '%Y-%m-%d').date()
        except ValueError:
            date_to = datetime.now().date()
    else:
        date_to = datetime.now().date()

    # Get cashier's transactions
    transactions = TransactionsModel.objects.filter(
        created_by=cashier,
        created_at__date__gte=date_from,
        created_at__date__lte=date_to,
        status='COMPLETED'
    ).select_related('patient', 'booking')

    # Statistics by payment method
    payment_methods_stats = {}
    for method in TransactionsModel.TransactionType.choices:
        method_transactions = transactions.filter(transaction_type=method[0])
        total = method_transactions.aggregate(Sum('amount'))['amount__sum'] or Decimal('0')
        count = method_transactions.count()

        payment_methods_stats[method[0]] = {
            'label': method[1],
            'count': count,
            'total': total
        }

    # Daily breakdown
    daily_stats = transactions.annotate(
        date=TruncDate('created_at')
    ).values('date').annotate(
        count=Count('id'),
        total=Sum('amount')
    ).order_by('date')

    # Overall statistics
    total_payments = transactions.filter(amount__gt=0).aggregate(Sum('amount'))['amount__sum'] or Decimal('0')
    total_refunds = abs(transactions.filter(amount__lt=0).aggregate(Sum('amount'))['amount__sum'] or Decimal('0'))
    net_total = total_payments - total_refunds

    # Get list of all cashiers for the filter
    all_cashiers = Account.objects.filter(
        roles__name='cashbox'
    ).distinct()

    context = {
        'cashier': cashier,
        'date_from': date_from,
        'date_to': date_to,
        'transactions': transactions,
        'payment_methods_stats': payment_methods_stats,
        'daily_stats': daily_stats,
        'total_payments': total_payments,
        'total_refunds': total_refunds,
        'net_total': net_total,
        'transaction_count': transactions.count(),
        'all_cashiers': all_cashiers,
    }

    return render(request, 'cashbox/reports/cashier_report.html', context)


@cashbox_required
def report_payment_methods(request):
    """
    Detailed report by payment methods
    """
    # Get date range
    date_from_str = request.GET.get('date_from', '')
    date_to_str = request.GET.get('date_to', '')

    if date_from_str:
        try:
            date_from = datetime.strptime(date_from_str, '%Y-%m-%d').date()
        except ValueError:
            date_from = datetime.now().date().replace(day=1)
    else:
        date_from = datetime.now().date().replace(day=1)

    if date_to_str:
        try:
            date_to = datetime.strptime(date_to_str, '%Y-%m-%d').date()
        except ValueError:
            date_to = datetime.now().date()
    else:
        date_to = datetime.now().date()

    # Get transactions for the period
    transactions = TransactionsModel.objects.filter(
        created_at__date__gte=date_from,
        created_at__date__lte=date_to,
        status='COMPLETED'
    ).select_related('patient', 'booking', 'created_by')

    # Detailed statistics by payment method
    payment_methods_detailed = {}
    for method in TransactionsModel.TransactionType.choices:
        method_transactions = transactions.filter(transaction_type=method[0])

        # Daily breakdown for this method
        daily_breakdown = method_transactions.annotate(
            date=TruncDate('created_at')
        ).values('date').annotate(
            count=Count('id'),
            total=Sum('amount')
        ).order_by('date')

        total_payments = method_transactions.filter(amount__gt=0).aggregate(Sum('amount'))['amount__sum'] or Decimal('0')
        total_refunds = abs(method_transactions.filter(amount__lt=0).aggregate(Sum('amount'))['amount__sum'] or Decimal('0'))

        payment_methods_detailed[method[0]] = {
            'label': method[1],
            'total_payments': total_payments,
            'total_refunds': total_refunds,
            'net_total': total_payments - total_refunds,
            'count': method_transactions.count(),
            'daily_breakdown': daily_breakdown,
            'transactions': method_transactions
        }

    # Overall totals
    total_payments = transactions.filter(amount__gt=0).aggregate(Sum('amount'))['amount__sum'] or Decimal('0')
    total_refunds = abs(transactions.filter(amount__lt=0).aggregate(Sum('amount'))['amount__sum'] or Decimal('0'))
    net_total = total_payments - total_refunds

    context = {
        'date_from': date_from,
        'date_to': date_to,
        'payment_methods_detailed': payment_methods_detailed,
        'total_payments': total_payments,
        'total_refunds': total_refunds,
        'net_total': net_total,
        'transaction_count': transactions.count(),
    }

    return render(request, 'cashbox/reports/payment_methods_report.html', context)
