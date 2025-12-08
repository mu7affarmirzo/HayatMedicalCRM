from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db import transaction
from django.db.models import Sum, Q, Count
from django.core.paginator import Paginator
from decimal import Decimal
from datetime import datetime, timedelta

from HayatMedicalCRM.auth.decorators import cashbox_required
from core.models import Booking, BookingBilling, TransactionsModel, PatientModel
from application.cashbox.forms.payment_forms import PaymentAcceptanceForm, RefundPaymentForm


@cashbox_required
@require_POST
def accept_payment(request, booking_id):
    """
    Accept payment for a booking

    POST parameters:
        - amount: Decimal amount being paid
        - payment_method: Payment method code
        - reference_number: External transaction reference (optional)
        - notes: Payment notes (optional)
    """
    booking = get_object_or_404(Booking, id=booking_id)
    billing = get_object_or_404(
        BookingBilling,
        booking=booking
    )

    # Validate billing status
    if billing.billing_status not in ['calculated', 'invoiced', 'partially_paid']:
        messages.error(
            request,
            'Невозможно принять оплату. Счет должен быть рассчитан.'
        )
        return redirect('cashbox:billing_detail', booking_id=booking.id)

    # Process form
    form = PaymentAcceptanceForm(request.POST, billing=billing)

    if form.is_valid():
        try:
            with transaction.atomic():
                # Create transaction record
                payment = TransactionsModel.objects.create(
                    booking=booking,
                    billing=billing,
                    patient=booking.details.first().client,  # Primary patient
                    amount=form.cleaned_data['amount'],
                    transaction_type=form.cleaned_data['payment_method'],
                    reference_number=form.cleaned_data.get('reference_number', ''),
                    notes=form.cleaned_data.get('notes', ''),
                    status='COMPLETED',
                    created_by=request.user,
                    modified_by=request.user
                )

                # Update billing status
                total_paid = billing.transactions.filter(
                    status='COMPLETED'
                ).aggregate(
                    total=Sum('amount')
                )['total'] or Decimal('0')

                if total_paid >= Decimal(str(billing.total_amount)):
                    billing.billing_status = 'paid'
                elif total_paid > 0:
                    billing.billing_status = 'partially_paid'

                billing.modified_by = request.user
                billing.save()

                messages.success(
                    request,
                    f'Оплата {form.cleaned_data["amount"]:,.2f} сум принята успешно. '
                    f'Способ: {dict(form.PAYMENT_METHOD_CHOICES).get(form.cleaned_data["payment_method"])}'
                )

                # Return JSON for AJAX requests
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': True,
                        'transaction_id': payment.id,
                        'amount': float(payment.amount),
                        'billing_status': billing.billing_status,
                        'message': 'Оплата принята успешно'
                    })

                # Redirect to receipt or billing detail
                return redirect('cashbox:billing_detail', booking_id=booking.id)

        except Exception as e:
            messages.error(
                request,
                f'Ошибка при обработке оплаты: {str(e)}'
            )

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': str(e)
                }, status=500)

    else:
        # Form validation failed
        error_messages = []
        for field, errors in form.errors.items():
            for error in errors:
                error_messages.append(f"{field}: {error}")

        messages.error(request, 'Ошибка валидации: ' + '; '.join(error_messages))

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'errors': form.errors
            }, status=400)

    return redirect('cashbox:billing_detail', booking_id=booking.id)


@cashbox_required
def payment_receipt(request, transaction_id):
    """
    Display payment receipt
    """
    payment = get_object_or_404(
        TransactionsModel,
        id=transaction_id
    )

    context = {
        'payment': payment,
        'booking': payment.booking,
        'billing': payment.billing,
        'patient': payment.patient,
    }

    return render(request, 'cashbox/payment/receipt.html', context)


@cashbox_required
@require_POST
def refund_payment(request, transaction_id):
    """
    Refund a payment

    POST parameters:
        - refund_amount: Amount to refund
        - refund_reason: Reason for refund
        - confirm: Confirmation checkbox
    """
    payment = get_object_or_404(TransactionsModel, id=transaction_id)

    # Process form
    form = RefundPaymentForm(request.POST, payment=payment)

    if form.is_valid():
        refund_amount = form.cleaned_data['refund_amount']
        refund_reason = form.cleaned_data['refund_reason']

        try:
            with transaction.atomic():
                # Create refund transaction
                refund = TransactionsModel.objects.create(
                    booking=payment.booking,
                    billing=payment.billing,
                    patient=payment.patient,
                    amount=-refund_amount,  # Negative amount for refund
                    transaction_type=payment.transaction_type,
                    reference_number=f"REFUND-{payment.id}",
                    notes=f"Возврат платежа #{payment.id}. Причина: {refund_reason}",
                    status='COMPLETED',
                    created_by=request.user,
                    modified_by=request.user
                )

                # Update original payment status
                if refund_amount == payment.amount:
                    # Full refund
                    payment.status = 'REFUNDED'
                    payment.notes = (payment.notes or '') + f'\n[ВОЗВРАТ] Полный возврат {refund_amount} сум. ID возврата: {refund.id}'
                else:
                    # Partial refund
                    payment.notes = (payment.notes or '') + f'\n[ВОЗВРАТ] Частичный возврат {refund_amount} сум. ID возврата: {refund.id}'

                payment.modified_by = request.user
                payment.save()

                # Recalculate billing status
                billing = payment.billing
                total_paid = billing.transactions.filter(
                    status='COMPLETED'
                ).aggregate(
                    total=Sum('amount')
                )['total'] or Decimal('0')

                if total_paid <= 0:
                    billing.billing_status = 'calculated'
                elif total_paid >= Decimal(str(billing.total_amount)):
                    billing.billing_status = 'paid'
                else:
                    billing.billing_status = 'partially_paid'

                billing.modified_by = request.user
                billing.save()

                messages.success(
                    request,
                    f'Возврат {refund_amount:,.2f} сум выполнен успешно. ID возврата: {refund.id}'
                )

                # Return JSON for AJAX requests
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': True,
                        'refund_id': refund.id,
                        'refund_amount': float(refund_amount),
                        'billing_status': billing.billing_status,
                        'message': 'Возврат выполнен успешно'
                    })

        except Exception as e:
            messages.error(request, f'Ошибка при выполнении возврата: {str(e)}')

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': str(e)
                }, status=500)

    else:
        # Form validation failed
        error_messages = []
        for field, errors in form.errors.items():
            for error in errors:
                error_messages.append(f"{field}: {error}")

        messages.error(request, 'Ошибка валидации: ' + '; '.join(error_messages))

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'errors': form.errors
            }, status=400)

    return redirect('cashbox:billing_detail', booking_id=payment.booking.id)


@cashbox_required
def payments_list(request):
    """
    Display list of all payments with filtering and search
    """
    # Get filter parameters
    status = request.GET.get('status', '')
    payment_method = request.GET.get('payment_method', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    search = request.GET.get('search', '')

    # Base query
    payments = TransactionsModel.objects.all().select_related(
        'patient', 'booking', 'billing', 'created_by'
    ).order_by('-created_at')

    # Apply filters
    if status:
        payments = payments.filter(status=status)

    if payment_method:
        payments = payments.filter(transaction_type=payment_method)

    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
            payments = payments.filter(created_at__date__gte=date_from_obj)
        except ValueError:
            pass

    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
            payments = payments.filter(created_at__date__lte=date_to_obj)
        except ValueError:
            pass

    if search:
        payments = payments.filter(
            Q(patient__f_name__icontains=search) |
            Q(patient__l_name__icontains=search) |
            Q(booking__booking_number__icontains=search) |
            Q(reference_number__icontains=search) |
            Q(id__icontains=search)
        )

    # Calculate statistics
    stats = payments.aggregate(
        total_amount=Sum('amount'),
        count=Count('id')
    )

    # Statistics by status
    stats_by_status = {}
    for st in TransactionsModel.TransactionStatus.choices:
        count = payments.filter(status=st[0]).count()
        amount = payments.filter(status=st[0]).aggregate(Sum('amount'))['amount__sum'] or 0
        stats_by_status[st[0]] = {
            'count': count,
            'amount': amount,
            'label': st[1]
        }

    # Pagination
    paginator = Paginator(payments, 25)  # Show 25 payments per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'payments': page_obj.object_list,
        'stats': stats,
        'stats_by_status': stats_by_status,
        'status_choices': TransactionsModel.TransactionStatus.choices,
        'payment_method_choices': TransactionsModel.TransactionType.choices,
        # Filters
        'filter_status': status,
        'filter_payment_method': payment_method,
        'filter_date_from': date_from,
        'filter_date_to': date_to,
        'filter_search': search,
    }

    return render(request, 'cashbox/payments/payments_list.html', context)


@cashbox_required
def payment_detail(request, transaction_id):
    """
    Display detailed information about a specific payment
    """
    payment = get_object_or_404(
        TransactionsModel.objects.select_related(
            'patient', 'booking', 'billing', 'created_by', 'modified_by'
        ),
        id=transaction_id
    )

    # Get related transactions (e.g., refunds for this payment)
    related_transactions = TransactionsModel.objects.filter(
        Q(reference_number__contains=f'REFUND-{payment.id}') |
        Q(notes__contains=f'#{payment.id}')
    ).exclude(id=payment.id).order_by('-created_at')

    # Get all transactions for this booking
    booking_transactions = TransactionsModel.objects.filter(
        booking=payment.booking
    ).exclude(id=payment.id).select_related('created_by').order_by('-created_at')

    # Calculate refund total if this is a COMPLETED payment
    refund_total = Decimal('0')
    if payment.status == 'COMPLETED':
        refund_total = related_transactions.aggregate(
            Sum('amount')
        )['amount__sum'] or Decimal('0')
        refund_total = abs(refund_total)  # Make positive for display

    context = {
        'payment': payment,
        'related_transactions': related_transactions,
        'booking_transactions': booking_transactions,
        'refund_total': refund_total,
        'can_refund': payment.status == 'COMPLETED',
    }

    return render(request, 'cashbox/payments/payment_detail.html', context)
