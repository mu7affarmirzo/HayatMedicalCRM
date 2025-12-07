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

    # Build detailed breakdown per patient/illness history
    from core.models import IllnessHistory, ServiceSessionTracking
    patient_breakdowns = []

    for detail in booking_details:
        # Get illness history for this patient
        illness_histories = IllnessHistory.objects.filter(
            booking=booking,
            patient=detail.client
        ).select_related('patient')

        for illness_history in illness_histories:
            patient_data = {
                'booking_detail': detail,
                'illness_history': illness_history,
                'patient': detail.client,
                'tariff': detail.tariff,
                'room': detail.room,
                'tariff_base_price': detail.price,
                'services': {'included': [], 'extra': []},
                'medications': [],
                'labs': [],
                'procedures': [],
                'totals': {
                    'tariff_base': detail.price,
                    'services_extra': 0,
                    'medications': 0,
                    'labs': 0,
                    'procedures': 0,
                    'subtotal': detail.price
                }
            }

            # Get service session tracking (included services in tariff)
            service_tracking = ServiceSessionTracking.objects.filter(
                booking_detail=detail
            ).select_related('service')

            for tracking in service_tracking:
                sessions_exceeded = tracking.sessions_used - tracking.sessions_included
                if sessions_exceeded > 0:
                    # Calculate extra cost
                    extra_cost = sessions_exceeded * (tracking.service.price or 0)
                    patient_data['totals']['services_extra'] += extra_cost

                    patient_data['services']['extra'].append({
                        'service': tracking.service,
                        'included': tracking.sessions_included,
                        'used': tracking.sessions_used,
                        'exceeded': sessions_exceeded,
                        'unit_price': tracking.service.price or 0,
                        'total_cost': extra_cost
                    })

                patient_data['services']['included'].append({
                    'service': tracking.service,
                    'included': tracking.sessions_included,
                    'used': tracking.sessions_used,
                    'exceeded': max(0, sessions_exceeded)
                })

            # Get medications for this illness history
            medications = MedicationSession.objects.filter(
                prescribed_medication__illness_history=illness_history
            ).select_related(
                'prescribed_medication__medication'
            )

            for med in medications:
                unit_price = getattr(med.prescribed_medication.medication, 'unit_price', 0) or 0
                total_cost = med.quantity * unit_price
                patient_data['medications'].append({
                    'medication': med.prescribed_medication.medication,
                    'quantity': med.quantity,
                    'unit_price': unit_price,
                    'total_cost': total_cost,
                    'session': med
                })
                patient_data['totals']['medications'] += total_cost

            # Get lab tests for this illness history
            labs = AssignedLabs.objects.filter(
                illness_history=illness_history
            ).select_related('lab')

            for lab in labs:
                # Check if lab is in billable state
                is_billable = lab.state in ['dispatched', 'results']
                lab_price = getattr(lab.lab, 'price', 0) or 0 if is_billable else 0

                patient_data['labs'].append({
                    'lab': lab.lab,
                    'state': lab.state,
                    'is_billable': is_billable,
                    'price': lab_price,
                    'assigned_lab': lab
                })

                if is_billable:
                    patient_data['totals']['labs'] += lab_price

            # Get procedures for this illness history
            procedures = IndividualProcedureSessionModel.objects.filter(
                assigned_procedure__illness_history=illness_history
            ).select_related(
                'assigned_procedure__medical_service'
            )

            for proc in procedures:
                # Check if billable
                is_billable = getattr(proc, 'is_billable', False)
                proc_price = getattr(proc, 'billed_amount', 0) or 0

                patient_data['procedures'].append({
                    'procedure': proc.assigned_procedure.medical_service,
                    'session': proc,
                    'is_billable': is_billable,
                    'price': proc_price
                })

                if is_billable:
                    patient_data['totals']['procedures'] += proc_price

            # Calculate subtotal
            patient_data['totals']['subtotal'] = (
                patient_data['totals']['tariff_base'] +
                patient_data['totals']['services_extra'] +
                patient_data['totals']['medications'] +
                patient_data['totals']['labs'] +
                patient_data['totals']['procedures']
            )

            patient_breakdowns.append(patient_data)

    # Calculate stay duration
    stay_duration = (booking.end_date - booking.start_date).days
    if stay_duration == 0:
        stay_duration = 1

    # Calculate grand total from all patient subtotals
    grand_total_from_patients = sum(
        patient['totals']['subtotal'] for patient in patient_breakdowns
    )

    # Prepare billing breakdown
    billing_breakdown = {
        'tariff_base': billing.tariff_base_amount,
        'additional_services': billing.additional_services_amount,
        'medications': billing.medications_amount,
        'lab_research': billing.lab_research_amount,
        'total': billing.total_amount,
        'grand_total_from_patients': grand_total_from_patients,  # Sum of all patient subtotals
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
        'patient_breakdowns': patient_breakdowns,
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
    
    # Calculate lab research amount (only billable states)
    lab_research_total = 0
    lab_tests = AssignedLabs.objects.filter(
        illness_history__booking=booking,
        state__in=['dispatched', 'results']  # Only billable states
    )
    for lab in lab_tests:
        # Add your lab pricing logic here
        lab_research_total += getattr(lab.lab, 'price', 0)
    
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