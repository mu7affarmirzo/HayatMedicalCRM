from datetime import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.http import require_POST

from core.models import Booking, BookingDetail, Room


@login_required
def booking_list(request):
    """
    Main screen with list of all bookings
    Includes filtering options by date, status, and search term
    """
    # Get all bookings ordered by start date (most recent first)
    bookings = Booking.objects.all().select_related('staff').prefetch_related(
        'details__client', 'details__room', 'details__tariff'
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
    status_choices = Booking.STATUS_CHOICES

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
def dashboard(request):
    """
    Dashboard/home page showing booking statistics and quick links
    """
    # Get booking stats
    today = timezone.now().date()
    tomorrow = today + timezone.timedelta(days=1)

    # Count bookings by status
    total_bookings = Booking.objects.count()
    active_bookings = Booking.objects.filter(
        status__in=['pending', 'confirmed', 'checked_in']
    ).count()

    # Today's check-ins and check-outs
    today_checkins = Booking.objects.filter(
        start_date__date=today,
        status='confirmed'
    ).select_related('staff').prefetch_related('details__client')

    today_checkouts = Booking.objects.filter(
        end_date__date=today,
        status='checked_in'
    ).select_related('staff').prefetch_related('details__client')

    # Tomorrow's check-ins
    tomorrow_checkins = Booking.objects.filter(
        start_date__date=tomorrow,
        status='confirmed'
    ).count()

    # Recent bookings
    recent_bookings = Booking.objects.all().order_by('-created_at')[:5]

    # Room availability stats
    total_rooms = Room.objects.filter(is_active=True).count()
    booked_rooms = BookingDetail.objects.filter(
        booking__start_date__lte=today,
        booking__end_date__gte=today,
        booking__status__in=['confirmed', 'checked_in']
    ).values('room').distinct().count()

    available_rooms = total_rooms - booked_rooms
    occupancy_rate = (booked_rooms / total_rooms * 100) if total_rooms > 0 else 0

    context = {
        'total_bookings': total_bookings,
        'active_bookings': active_bookings,
        'today_checkins': today_checkins,
        'today_checkouts': today_checkouts,
        'tomorrow_checkins': tomorrow_checkins,
        'recent_bookings': recent_bookings,
        'total_rooms': total_rooms,
        'booked_rooms': booked_rooms,
        'available_rooms': available_rooms,
        'occupancy_rate': occupancy_rate,
        'today': today,
    }

    return render(request, 'logus/booking/dashboard.html', context)


@login_required
@require_POST
def update_booking_status(request, booking_id):
    """AJAX endpoint to update booking status"""
    try:
        booking = Booking.objects.get(id=booking_id)
        new_status = request.POST.get('status')

        if new_status in dict(Booking.STATUS_CHOICES).keys():
            booking.status = new_status
            booking.save()
            return JsonResponse({'success': True, 'status': new_status,
                                 'status_display': dict(Booking.STATUS_CHOICES)[new_status]})
        else:
            return JsonResponse({'success': False, 'error': 'Invalid status'}, status=400)
    except Booking.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Booking not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
