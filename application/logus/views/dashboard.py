from datetime import datetime
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone
from core.models import Room, RoomType, BookingDetail, PatientModel, Tariff


def get_today_statistics():
    """
    Calculate dashboard statistics for today (total rooms, availability, check-ins/outs)
    """
    today = timezone.now().date()
    today_start = timezone.make_aware(datetime.combine(today, datetime.min.time()))
    today_end = timezone.make_aware(datetime.combine(today, datetime.max.time()))

    # Total active rooms
    total_rooms = Room.objects.filter(is_active=True).count()

    # Get occupied rooms for today
    occupied_today = BookingDetail.objects.filter(
        booking__start_date__lte=today_end,
        booking__end_date__gte=today_start,
        booking__status__in=['confirmed', 'checked_in']
    ).values_list('room_id', flat=True).distinct()

    available_today = Room.objects.filter(
        is_active=True
    ).exclude(id__in=occupied_today).count()

    # Get check-ins for today
    todays_checkins = BookingDetail.objects.filter(
        booking__start_date__gte=today_start,
        booking__start_date__lte=today_end,
        booking__status='confirmed'
    ).select_related('booking', 'client', 'room')

    # Get check-outs for today
    todays_checkouts = BookingDetail.objects.filter(
        booking__end_date__gte=today_start,
        booking__end_date__lte=today_end,
        booking__status='checked_in'
    ).select_related('booking', 'client', 'room')

    return {
        'total_rooms': total_rooms,
        'available_today': available_today,
        'todays_checkins': todays_checkins,
        'checkins_today': todays_checkins.count(),
        'todays_checkouts': todays_checkouts,
        'checkouts_today': todays_checkouts.count(),
    }


def parse_date_range(date_range_str):
    """
    Parse date range string and return start/end datetime objects
    Returns tuple (start_datetime, end_datetime) or raises ValueError
    """
    if not date_range_str:
        raise ValueError("Date range is required")

    try:
        start_str, end_str = date_range_str.split(' - ')
        start_date = datetime.strptime(start_str, '%d.%m.%Y')
        end_date = datetime.strptime(end_str, '%d.%m.%Y')

        # Add time components (14:00 check-in, 12:00 checkout)
        start_datetime = timezone.make_aware(
            datetime.combine(start_date, datetime(1, 1, 1, 14, 0).time())
        )
        end_datetime = timezone.make_aware(
            datetime.combine(end_date, datetime(1, 1, 1, 12, 0).time())
        )

        return start_datetime, end_datetime
    except ValueError as e:
        raise ValueError(f"Invalid date format: {str(e)}")


def get_occupied_rooms_data(start_datetime, end_datetime, room_type_id=None):
    """
    Get data about occupied rooms for the given date range
    Returns list of dictionaries with room and booking information
    """
    # Get occupied rooms for the date range
    occupied_bookings = BookingDetail.objects.filter(
        booking__start_date__lt=end_datetime,
        booking__end_date__gt=start_datetime,
        booking__status__in=['pending', 'confirmed', 'checked_in']
    ).select_related('room', 'client', 'booking', 'room__room_type')

    occupied_rooms_data = []
    for booking_detail in occupied_bookings:
        # Filter by room type if specified
        if room_type_id and str(booking_detail.room.room_type_id) != room_type_id:
            continue

        status_class = {
            'pending': 'warning',
            'confirmed': 'primary',
            'checked_in': 'info',
            'completed': 'success',
            'cancelled': 'danger'
        }.get(booking_detail.booking.status, 'secondary')

        occupied_rooms_data.append({
            'room': booking_detail.room,
            'client_name': booking_detail.client.full_name,
            'checkout_date': booking_detail.booking.end_date,
            'status_display': booking_detail.booking.get_status_display(),
            'status_class': status_class
        })

    return occupied_rooms_data


def get_available_rooms_data(start_datetime, end_datetime, room_type_id=None):
    """
    Get available rooms for the given date range
    Returns QuerySet of available Room objects
    """
    # Get occupied room IDs
    occupied_room_ids = list(BookingDetail.objects.filter(
        booking__start_date__lt=end_datetime,
        booking__end_date__gt=start_datetime,
        booking__status__in=['pending', 'confirmed', 'checked_in']
    ).values_list('room_id', flat=True))

    # Build query for available rooms
    available_rooms_query = Room.objects.filter(
        is_active=True
    ).exclude(id__in=occupied_room_ids).select_related('room_type')

    # Filter by room type if specified
    if room_type_id:
        available_rooms_query = available_rooms_query.filter(room_type_id=room_type_id)

    return available_rooms_query


def calculate_occupancy_statistics(available_rooms, occupied_rooms_data):
    """
    Calculate occupancy rate and capacity statistics
    Returns dictionary with statistics
    """
    total_rooms = available_rooms.count() + len(occupied_rooms_data)
    total_capacity = (
            sum(room.capacity for room in available_rooms) +
            sum(data['room'].capacity for data in occupied_rooms_data)
    )

    occupancy_rate = (len(occupied_rooms_data) / total_rooms * 100) if total_rooms > 0 else 0

    return {
        'total_capacity': total_capacity,
        'occupancy_rate': occupancy_rate,
    }


def build_base_context():
    """
    Build base context data needed for the dashboard
    """
    return {
        'room_types': RoomType.objects.all(),
        'patients': PatientModel.objects.filter(is_active=True).order_by('f_name', 'l_name'),
        'tariffs': Tariff.objects.filter(is_active=True),
        'show_results': False,
    }


def handle_availability_search(request):
    """
    Handle form submission for availability search
    Returns dictionary with search results or None if no search performed
    """
    if request.method != 'POST':
        return None

    date_range = request.POST.get('date_range', '')
    room_type_id = request.POST.get('room_type_id', '')

    if not date_range:
        return None

    try:
        # Parse date range
        start_datetime, end_datetime = parse_date_range(date_range)

        # Get room data
        occupied_rooms_data = get_occupied_rooms_data(start_datetime, end_datetime, room_type_id)
        available_rooms = get_available_rooms_data(start_datetime, end_datetime, room_type_id)

        # Calculate statistics
        occupancy_stats = calculate_occupancy_statistics(available_rooms, occupied_rooms_data)

        # Build results context
        results_context = {
            'start_date': start_datetime,
            'end_date': end_datetime,
            'date_range': date_range,
            'show_results': True,
            'available_rooms': available_rooms,
            'occupied_rooms': occupied_rooms_data,
            **occupancy_stats
        }

        # Add selected room type info if specified
        if room_type_id:
            results_context.update({
                'selected_room_type': RoomType.objects.get(id=room_type_id),
                'selected_room_type_id': room_type_id
            })

        return results_context

    except ValueError as e:
        messages.error(request, f'Неверный формат даты: {str(e)}')
        return None
    except RoomType.DoesNotExist:
        messages.error(request, 'Указанный тип комнаты не найден')
        return None


@login_required
def reception_dashboard(request):
    """
    Main dashboard view for reception staff to check room availability
    """
    # Build base context
    context = build_base_context()

    # Add today's statistics
    today_stats = get_today_statistics()
    context.update(today_stats)

    # Handle availability search if form was submitted
    search_results = handle_availability_search(request)
    if search_results:
        context.update(search_results)

    return render(request, 'logus/dashboard/reception_dashboard.html', context)