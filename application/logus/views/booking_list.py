from datetime import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Prefetch
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.views.decorators.http import require_POST

from core.models import Booking, BookingDetail, TariffService, IllnessHistory, CheckInLog
from core.models.booking import BookingHistory
from core.models.tariffs import ServiceSessionTracking


@login_required
def booking_detail_view(request, booking_id):
    """
    Display detailed information for a specific booking
    TASK-023: Now includes booking history
    """
    # Get the booking or return 404 if not found
    booking = get_object_or_404(Booking, id=booking_id)

    # Handle booking actions (if any)
    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'cancel':
            booking.status = 'cancelled'
            booking.modified_by = request.user
            booking.save()
            messages.success(request, f'Бронирование #{booking.booking_number} успешно отменено.')

        elif action == 'checkin':
            messages.info(
                request,
                'Используйте кнопку "Заселить" возле гостя, чтобы заполнить чек-лист заселения.'
            )

        elif action == 'complete':
            booking.status = 'completed'
            booking.modified_by = request.user
            booking.save()
            messages.success(request, f'Бронирование #{booking.booking_number} отмечено как завершенное.')

        elif action == 'confirm':
            booking.status = 'confirmed'
            booking.modified_by = request.user
            booking.save()
            messages.success(request, f'Бронирование #{booking.booking_number} подтверждено.')

        return redirect('logus:booking_detail', booking_id=booking.id)

    # Get all booking details with related data
    booking_details = booking.details.all().select_related(
        'client', 'room', 'room__room_type', 'tariff'
    )

    tariff_ids = [detail.tariff_id for detail in booking_details]
    booking_details = booking_details.prefetch_related(
        Prefetch(
            'tariff__tariff_services',
            queryset=TariffService.objects.select_related('service')
        )
    )

    # Get additional services if any
    additional_services = booking.additional_services.all().select_related('service', 'booking_detail')

    # Get illness histories associated with this booking
    illness_histories = IllnessHistory.objects.filter(booking=booking).select_related(
        'patient', 'doctor', 'initial_diagnosis', 'at_arrival_diagnosis', 'diagnosis', 'profession'
    ).prefetch_related('toxic_factors', 'nurses')

    # We'll just pass the illness_histories directly to the template
    # No need for a mapping dictionary since we'll loop through the histories in the template

    # Get service session tracking for all booking details (TASK-016)
    # Annotate each booking detail with its tracking records
    # Note: Using 'service_tracking_list' to avoid conflict with reverse relation
    for detail in booking_details:
        detail.service_tracking_list = ServiceSessionTracking.objects.filter(
            booking_detail=detail,
            booking_detail__is_current=True
        ).select_related('service', 'tariff_service').order_by('service__name')

    # Build a mapping of check-in logs for quick access in templates (TASK-026)
    booking_details = list(booking_details)
    check_in_logs = CheckInLog.objects.filter(
        booking_detail_id__in=[detail.id for detail in booking_details]
    ).select_related('booking_detail', 'booking_detail__client')
    check_in_log_map = {log.booking_detail_id: log for log in check_in_logs}

    for detail in booking_details:
        detail.check_in_log = check_in_log_map.get(detail.id)

    # Calculate stay duration
    stay_duration = (booking.end_date - booking.start_date).days
    if stay_duration == 0:  # Handle same-day stays
        stay_duration = 1

    # Calculate financial data
    booking_details_total = sum(detail.price for detail in booking_details)
    additional_services_total = sum(service.price for service in additional_services)
    total_price = booking_details_total + additional_services_total

    # Available actions based on booking status
    available_actions = []
    if booking.status == 'pending':
        available_actions = ['confirm', 'cancel']
    elif booking.status == 'confirmed':
        available_actions = ['cancel']
    elif booking.status == 'checked_in' or booking.status == 'in_progress':
        available_actions = ['complete']

    # TASK-023: Get booking history
    booking_history = BookingHistory.objects.filter(
        booking=booking
    ).select_related('changed_by', 'booking_detail', 'booking_detail__client').order_by('-changed_at')[:50]  # Limit to last 50 changes

    context = {
        'booking': booking,
        'booking_details': booking_details,  # Now includes service_tracking attribute (TASK-016)
        'additional_services': additional_services,
        'illness_histories': illness_histories,
        'stay_duration': stay_duration,
        'booking_details_total': booking_details_total,
        'additional_services_total': additional_services_total,
        'total_price': total_price,
        'available_actions': available_actions,
        'status_badge_class': get_status_badge_class(booking.status),
        'booking_history': booking_history,  # TASK-023: Add booking history to context
    }

    return render(request, 'logus/booking/booking_detail.html', context)


def get_status_badge_class(status):
    """Helper function to determine the CSS class for status badges"""
    status_classes = {
        'pending': 'warning',
        'confirmed': 'primary',
        'checked_in': 'info',
        'completed': 'success',
        'cancelled': 'danger',
    }
    return status_classes.get(status, 'secondary')


@login_required
def booking_list(request):
    """
    Main screen with list of all bookings
    Includes filtering options by date, status, and search term
    """
    # Get all bookings ordered by start date (most recent first)
    # TASK-053: Optimized with select_related and prefetch_related to avoid N+1 queries
    bookings = Booking.objects.all().select_related(
        'staff', 'created_by', 'modified_by'
    ).prefetch_related(
        'details__client',
        'details__client__region',
        'details__client__district',
        'details__room',
        'details__room__room_type',
        'details__tariff'
    ).order_by('-start_date')

    # Initialize filters
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    status = request.GET.get('status', '')
    search = request.GET.get('search', '')

    # Apply filters if provided
    if date_from:
        try:
            date_from = datetime.strptime(date_from, '%d.%m.%Y')
            bookings = bookings.filter(start_date__gte=date_from)
        except ValueError:
            messages.error(request, 'Неверный формат даты')

    if date_to:
        try:
            date_to = datetime.strptime(date_to, '%d.%m.%Y')
            # Add one day to include the end date fully
            date_to = date_to + timezone.timedelta(days=1)
            bookings = bookings.filter(start_date__lt=date_to)
        except ValueError:
            messages.error(request, 'Неверный формат даты')

    if status:
        bookings = bookings.filter(status=status)

    if search:
        # Search by booking number or patient name
        from django.db.models import Q
        patient_bookings = BookingDetail.objects.filter(
            Q(client__f_name__icontains=search) |
            Q(client__l_name__icontains=search)
        ).values_list('booking_id', flat=True)

        bookings = bookings.filter(
            Q(booking_number__icontains=search) |
            Q(id__in=patient_bookings)
        )

    # Get status choices for filter dropdown
    status_choices = Booking.BookingStatus

    # Add some statistics
    stats = {
        'total': bookings.count(),
        'pending': bookings.filter(status='pending').count(),
        'confirmed': bookings.filter(status='confirmed').count(),
        'checked_in': bookings.filter(status='checked_in').count(),
        'completed': bookings.filter(status='completed').count(),
        'cancelled': bookings.filter(status='cancelled').count(),
        'today': bookings.filter(start_date__date=timezone.now().date()).count(),
        'tomorrow': bookings.filter(start_date__date=timezone.now().date() + timezone.timedelta(days=1)).count(),
    }

    # Calculate upcoming check-ins (next 3 days)
    today = timezone.now().date()
    upcoming_range = [today + timezone.timedelta(days=i) for i in range(1, 4)]
    upcoming_checkins = []

    for date in upcoming_range:
        day_bookings = bookings.filter(start_date__date=date, status='confirmed')
        if day_bookings.exists():
            upcoming_checkins.append({
                'date': date,
                'count': day_bookings.count(),
                'bookings': day_bookings
            })

    context = {
        'bookings': bookings,
        'status_choices': status_choices,
        'filter_status': status,
        'filter_search': search,
        'filter_date_from': date_from.strftime('%d.%m.%Y') if isinstance(date_from, datetime) else '',
        'filter_date_to': (date_to - timezone.timedelta(days=1)).strftime('%d.%m.%Y') if isinstance(date_to,
                                                                                                    datetime) else '',
        'stats': stats,
        'upcoming_checkins': upcoming_checkins,
        'today': today,
    }

    return render(request, 'logus/booking/booking_list.html', context)


@login_required
@require_POST
def update_booking_status(request, booking_id):
    """AJAX endpoint to update booking status"""
    try:
        booking = Booking.objects.get(id=booking_id)
        new_status = request.POST.get('status')

        if new_status in dict(Booking.BookingStatus).keys():
            booking.status = new_status
            booking.save()
            return JsonResponse({'success': True, 'status': new_status,
                                 'status_display': dict(Booking.BookingStatus)[new_status]})
        else:
            return JsonResponse({'success': False, 'error': 'Invalid status'}, status=400)
    except Booking.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Booking not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
