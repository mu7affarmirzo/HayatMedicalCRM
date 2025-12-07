from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from HayatMedicalCRM.auth.decorators import cashbox_required
from django.db.models import Q, Prefetch
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from core.models import (
    Booking, BookingBilling, BookingDetail, ServiceUsage,
    AssignedLabs, MedicationSession, IndividualProcedureSessionModel
)


@cashbox_required
def billing_list(request):
    """
    Display list of bookings with their billing information for payment processing
    """
    # Get bookings that are ready for billing (checked_in, in_progress, completed, discharged)
    bookings = Booking.objects.filter(
        status__in=['checked_in', 'in_progress', 'completed', 'discharged']
    ).select_related('staff').prefetch_related(
        'details__client', 
        'details__room', 
        'details__tariff',
        'billing'
    ).order_by('-start_date')

    # Initialize filters
    status = request.GET.get('status', '')
    billing_status = request.GET.get('billing_status', '')
    search = request.GET.get('search', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')

    # Apply filters
    if status:
        bookings = bookings.filter(status=status)

    if billing_status:
        bookings = bookings.filter(billing__billing_status=billing_status)

    if search:
        # Search by booking number or patient name
        patient_bookings = BookingDetail.objects.filter(
            Q(client__f_name__icontains=search) |
            Q(client__l_name__icontains=search)
        ).values_list('booking_id', flat=True)

        bookings = bookings.filter(
            Q(booking_number__icontains=search) |
            Q(id__in=patient_bookings)
        )

    if date_from:
        from datetime import datetime
        try:
            date_from = datetime.strptime(date_from, '%Y-%m-%d')
            bookings = bookings.filter(start_date__gte=date_from)
        except ValueError:
            messages.error(request, 'Неверный формат даты начала')

    if date_to:
        from datetime import datetime
        try:
            date_to = datetime.strptime(date_to, '%Y-%m-%d')
            bookings = bookings.filter(start_date__lte=date_to)
        except ValueError:
            messages.error(request, 'Неверный формат даты окончания')

    # Pagination
    paginator = Paginator(bookings, 20)
    page = request.GET.get('page')
    bookings_page = paginator.get_page(page)

    # Get filter choices
    status_choices = Booking.BookingStatus.choices
    billing_status_choices = BookingBilling.BillingStatus.choices

    # Calculate statistics
    stats = {
        'total': bookings.count(),
        'pending_billing': bookings.filter(billing__billing_status='pending').count(),
        'calculated': bookings.filter(billing__billing_status='calculated').count(),
        'invoiced': bookings.filter(billing__billing_status='invoiced').count(),
    }

    context = {
        'bookings': bookings_page,
        'status_choices': status_choices,
        'billing_status_choices': billing_status_choices,
        'filter_status': status,
        'filter_billing_status': billing_status,
        'filter_search': search,
        'filter_date_from': date_from,
        'filter_date_to': date_to,
        'stats': stats,
    }

    return render(request, 'cashbox/billing/billing_list.html', context)


@cashbox_required
def billing_detail(request, booking_id):
    """
    Display detailed billing information for a specific booking with breakdown of all charges
    """
    booking = get_object_or_404(Booking, id=booking_id)
    
    # Get or create billing record
    billing, created = BookingBilling.objects.get_or_create(
        booking=booking,
        defaults={
            'created_by': request.user,
            'modified_by': request.user
        }
    )

    # Handle billing actions
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'calculate_billing':
            calculate_billing_amounts(booking, billing, request.user)
            messages.success(request, f'Счет для бронирования #{booking.booking_number} пересчитан.')
            return redirect('cashbox:billing_detail', booking_id=booking.id)
        
        elif action == 'mark_invoiced':
            billing.billing_status = 'invoiced'
            billing.modified_by = request.user
            billing.save()
            messages.success(request, f'Счет для бронирования #{booking.booking_number} помечен как выставлен.')
            return redirect('cashbox:billing_detail', booking_id=booking.id)

    # Get booking details with tariff information
    booking_details = booking.details.all().select_related(
        'client', 'room', 'room__room_type', 'tariff'
    ).prefetch_related(
        'tariff__tariff_services__service'
    )

    # Get additional services beyond tariff
    additional_services = ServiceUsage.objects.filter(
        booking=booking
    ).select_related('service', 'booking_detail__client')

    # Get prescribed medications not included in tariff
    prescribed_medications = MedicationSession.objects.filter(
        prescribed_medication__illness_history__booking=booking
    ).select_related(
        'prescribed_medication__medication',
        'prescribed_medication__illness_history__patient'
    )
    
    # Add total_cost calculation for each medication session
    for med in prescribed_medications:
        unit_price = getattr(med.prescribed_medication.medication, 'unit_price', 0) or 0
        med.total_cost = med.quantity * unit_price

    # Get lab tests beyond tariff inclusions
    lab_tests = AssignedLabs.objects.filter(
        illness_history__booking=booking
    )

    # Get procedures beyond tariff inclusions
    procedures = IndividualProcedureSessionModel.objects.filter(
        assigned_procedure__illness_history__booking=booking
    ).select_related(
        'assigned_procedure__medical_service',
        'assigned_procedure__illness_history__patient'
    )

    # Calculate stay duration
    stay_duration = (booking.end_date - booking.start_date).days
    if stay_duration == 0:
        stay_duration = 1

    # Prepare billing breakdown
    billing_breakdown = {
        'tariff_base': billing.tariff_base_amount,
        'additional_services': billing.additional_services_amount,
        'medications': billing.medications_amount,
        'lab_research': billing.lab_research_amount,
        'total': billing.total_amount,
    }

    # Calculate payment totals
    from django.db.models import Sum
    total_paid = billing.transactions.filter(
        status='COMPLETED'
    ).aggregate(
        total=Sum('amount')
    )['total'] or 0

    remaining = billing.total_amount - float(total_paid)

    # Available actions based on billing status
    available_actions = []
    if billing.billing_status == 'pending':
        available_actions = ['calculate_billing']
    elif billing.billing_status == 'calculated':
        available_actions = ['calculate_billing', 'mark_invoiced']
    elif billing.billing_status in ['invoiced', 'partially_paid']:
        available_actions = ['calculate_billing', 'accept_payment']

    context = {
        'booking': booking,
        'billing': billing,
        'booking_details': booking_details,
        'additional_services': additional_services,
        'prescribed_medications': prescribed_medications,
        'lab_tests': lab_tests,
        'procedures': procedures,
        'stay_duration': stay_duration,
        'billing_breakdown': billing_breakdown,
        'available_actions': available_actions,
        'total_paid': total_paid,
        'remaining': remaining,
    }

    return render(request, 'cashbox/billing/billing_detail.html', context)


def calculate_billing_amounts(booking, billing, user):
    """
    Calculate all billing amounts for a booking
    """
    # Calculate tariff base amount
    tariff_base = sum(detail.price for detail in booking.details.all())
    
    # Calculate additional services amount
    additional_services_total = sum(
        service.price for service in ServiceUsage.objects.filter(booking=booking)
    )
    
    # Calculate medications amount (simplified - you may need to adjust based on your pricing logic)
    medications_total = 0
    prescribed_medications = MedicationSession.objects.filter(
        prescribed_medication__illness_history__booking=booking
    )
    for med_session in prescribed_medications:
        # Add your medication pricing logic here
        medications_total += med_session.quantity * getattr(med_session.prescribed_medication.medication, 'unit_price', 0)
    
    # Calculate lab research amount
    lab_research_total = 0
    lab_tests = AssignedLabs.objects.filter(illness_history__booking=booking)
    for lab in lab_tests:
        # Add your lab pricing logic here
        lab_research_total += getattr(lab.lab_research, 'price', 0)
    
    # Update billing record
    billing.tariff_base_amount = int(tariff_base)
    billing.additional_services_amount = int(additional_services_total)
    billing.medications_amount = int(medications_total)
    billing.lab_research_amount = int(lab_research_total)
    billing.billing_status = 'calculated'
    billing.modified_by = user
    billing.save()  # This will automatically calculate total_amount


@cashbox_required
@require_POST
def update_billing_status(request, booking_id):
    """AJAX endpoint to update billing status"""
    try:
        booking = Booking.objects.get(id=booking_id)
        billing, created = BookingBilling.objects.get_or_create(
            booking=booking,
            defaults={'created_by': request.user, 'modified_by': request.user}
        )
        
        new_status = request.POST.get('status')
        
        if new_status in dict(BookingBilling.BillingStatus).keys():
            billing.billing_status = new_status
            billing.modified_by = request.user
            billing.save()
            
            return JsonResponse({
                'success': True, 
                'status': new_status,
                'status_display': dict(BookingBilling.BillingStatus)[new_status]
            })
        else:
            return JsonResponse({'success': False, 'error': 'Invalid status'}, status=400)
            
    except Booking.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Booking not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)