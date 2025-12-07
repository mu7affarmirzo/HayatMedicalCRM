from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db import transaction
from django.db.models import Sum
from decimal import Decimal

from HayatMedicalCRM.auth.decorators import cashbox_required
from core.models import Booking, BookingBilling, TransactionsModel
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
