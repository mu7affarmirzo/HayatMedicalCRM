"""
Room Availability Matrix V2 (RM2) Service Layer

This module implements the service functions for the RM2 feature,
providing comprehensive room availability data for the visual matrix interface.

FEATURE: RM2 - Room Availability V2
"""

from datetime import date, timedelta
from typing import Dict, List, Any, Tuple
from django.db.models import Q, Count
from django.utils import timezone

from core.models.rooms import Room, RoomType, RoomMaintenance
from core.models.booking import Booking, BookingDetail
from core.models.clients import PatientModel


def get_availability_matrix_v2(
    start_date: date,
    end_date: date,
    room_type_id: int = None,
    include_inactive: bool = False
) -> Dict[str, Any]:
    """
    Generate comprehensive availability matrix for RM2 feature.

    Args:
        start_date: Period start date
        end_date: Period end date
        room_type_id: Optional filter for specific room type
        include_inactive: Include inactive rooms in results

    Returns:
        Dictionary with structure containing period info, statistics,
        and detailed room availability data
    """

    # 1. Generate date range
    days = []
    current_date = start_date
    while current_date <= end_date:
        days.append(current_date)
        current_date += timedelta(days=1)
    total_days = len(days)

    # 2. Get room types with filters
    room_types_query = RoomType.objects.all()
    if room_type_id:
        room_types_query = room_types_query.filter(id=room_type_id)

    # 3. For each room type, get rooms
    room_types_data = []
    for room_type in room_types_query:
        rooms_query = room_type.rooms.all()
        if not include_inactive:
            rooms_query = rooms_query.filter(is_active=True)

        # 4. For each room, calculate daily status
        rooms_data = []
        for room in rooms_query:
            daily_status = []

            for day in days:
                # Convert date to datetime for comparison
                day_start = timezone.make_aware(
                    timezone.datetime.combine(day, timezone.datetime.min.time())
                )
                day_end = timezone.make_aware(
                    timezone.datetime.combine(day + timedelta(days=1), timezone.datetime.min.time())
                )

                # Get bookings for this room on this day
                bookings = BookingDetail.objects.filter(
                    room=room,
                    booking__status__in=['pending', 'confirmed', 'checked_in', 'in_progress'],
                    start_date__lt=day_end,
                    end_date__gt=day_start,
                    is_current=True
                ).select_related('booking', 'client', 'tariff')

                # Get maintenance records
                maintenance = RoomMaintenance.objects.filter(
                    room=room,
                    start_date__lt=day_end,
                    end_date__gt=day_start,
                    status__in=['scheduled', 'in_progress']
                ).first()

                # Calculate status
                current_occupancy = bookings.count()
                status = 'available'
                is_bookable = True

                if maintenance:
                    status = 'maintenance'
                    is_bookable = False
                elif current_occupancy == 0:
                    status = 'available'
                elif current_occupancy >= room.capacity:
                    status = 'occupied'
                    is_bookable = False
                else:
                    status = 'partial'

                # Check for check-in/check-out
                for booking in bookings:
                    # Check if this is a check-in day (start_date matches)
                    if booking.start_date.date() == day:
                        status = 'checkin'
                    # Check if this is a check-out day (end_date matches)
                    elif booking.end_date.date() == day:
                        status = 'checkout'

                # Build guest information
                guests = []
                for booking_detail in bookings:
                    patient = booking_detail.client
                    age = None
                    if patient.date_of_birth:
                        today = day
                        age = today.year - patient.date_of_birth.year
                        if today.month < patient.date_of_birth.month or \
                           (today.month == patient.date_of_birth.month and today.day < patient.date_of_birth.day):
                            age -= 1

                    guests.append({
                        'id': patient.id,
                        'full_name': patient.get_full_name() if hasattr(patient, 'get_full_name') else f"{patient.f_name} {patient.l_name}",
                        'gender': patient.gender if patient.gender else 'N/A',
                        'age': age,
                        'booking_number': booking_detail.booking.booking_number,
                        'booking_id': booking_detail.booking.id,
                        'booking_detail_id': booking_detail.id,
                        'start_date': booking_detail.start_date.date(),
                        'end_date': booking_detail.end_date.date(),
                        'tariff_name': booking_detail.tariff.name if booking_detail.tariff else 'N/A',
                        'is_checkin_day': booking_detail.start_date.date() == day,
                        'is_checkout_day': booking_detail.end_date.date() == day
                    })

                daily_status.append({
                    'date': day,
                    'status': status,
                    'occupancy': {
                        'current': current_occupancy,
                        'capacity': room.capacity,
                        'percentage': (current_occupancy / room.capacity * 100) if room.capacity > 0 else 0
                    },
                    'guests': guests,
                    'maintenance': {
                        'type': maintenance.get_maintenance_type_display(),
                        'status': maintenance.get_status_display(),
                        'description': maintenance.description
                    } if maintenance else None,
                    'is_bookable': is_bookable,
                    'booking_conflicts': []  # Can add conflict detection logic if needed
                })

            rooms_data.append({
                'id': room.id,
                'name': room.name,
                'capacity': room.capacity,
                'price': room.price or 0,
                'is_active': room.is_active,
                'daily_status': daily_status
            })

        # 5. Aggregate daily availability for room type
        daily_availability = []
        for day in days:
            total = len(rooms_data)
            occupied = 0
            under_maintenance = 0

            for room_data in rooms_data:
                day_status = next((d for d in room_data['daily_status'] if d['date'] == day), None)
                if day_status:
                    if day_status['status'] == 'maintenance':
                        under_maintenance += 1
                    elif day_status['status'] in ['occupied', 'checkin']:
                        occupied += 1
                    elif day_status['status'] == 'partial':
                        # Count as partially occupied
                        occupied += 0.5

            available = total - occupied - under_maintenance
            occupancy_pct = (occupied / total * 100) if total > 0 else 0

            daily_availability.append({
                'date': day,
                'total': total,
                'occupied': int(occupied),
                'available': int(available),
                'under_maintenance': under_maintenance,
                'occupancy_percentage': round(occupancy_pct, 2)
            })

        room_types_data.append({
            'id': room_type.id,
            'name': room_type.name,
            'total_rooms': len(rooms_data),
            'active_rooms': len([r for r in rooms_data if r['is_active']]),
            'daily_availability': daily_availability,
            'rooms': rooms_data
        })

    # 6. Calculate overall statistics
    total_rooms = sum(rt['total_rooms'] for rt in room_types_data)

    # Calculate average occupancy
    total_occupancy = 0
    if room_types_data and total_days > 0:
        for rt in room_types_data:
            for day_data in rt['daily_availability']:
                total_occupancy += day_data['occupancy_percentage']
        avg_occupancy = total_occupancy / (len(room_types_data) * total_days)
    else:
        avg_occupancy = 0

    # Upcoming check-ins/check-outs (next 24 hours)
    today = timezone.now().date()
    tomorrow = today + timedelta(days=1)

    today_start = timezone.make_aware(
        timezone.datetime.combine(today, timezone.datetime.min.time())
    )
    tomorrow_start = timezone.make_aware(
        timezone.datetime.combine(tomorrow, timezone.datetime.min.time())
    )

    upcoming_checkins = BookingDetail.objects.filter(
        start_date__gte=today_start,
        start_date__lt=tomorrow_start,
        booking__status__in=['confirmed', 'pending'],
        is_current=True
    ).count()

    upcoming_checkouts = BookingDetail.objects.filter(
        end_date__gte=today_start,
        end_date__lt=tomorrow_start,
        booking__status__in=['checked_in', 'in_progress'],
        is_current=True
    ).count()

    # Current maintenance count
    now = timezone.now()
    maintenance_count = RoomMaintenance.objects.filter(
        start_date__lte=now,
        end_date__gt=now,
        status__in=['scheduled', 'in_progress']
    ).count()

    return {
        'period': {
            'start': start_date,
            'end': end_date,
            'days': days,
            'total_days': total_days
        },
        'statistics': {
            'total_rooms': total_rooms,
            'average_occupancy': round(avg_occupancy, 2),
            'upcoming_checkins': upcoming_checkins,
            'upcoming_checkouts': upcoming_checkouts,
            'maintenance_count': maintenance_count
        },
        'room_types': room_types_data
    }


def get_room_booking_timeline(
    room_id: int,
    start_date: date,
    end_date: date
) -> Dict[str, Any]:
    """
    Get detailed booking timeline for a specific room.
    Used for room detail modal/tooltip.

    Args:
        room_id: Room ID
        start_date: Period start date
        end_date: Period end date

    Returns:
        Dictionary with room info, bookings, and daily details
    """
    try:
        room = Room.objects.select_related('room_type').get(id=room_id)
    except Room.DoesNotExist:
        return {
            'error': 'Room not found',
            'room': None,
            'bookings': [],
            'maintenance_periods': [],
            'daily_details': []
        }

    # Get bookings for this room in the period
    day_start = timezone.make_aware(
        timezone.datetime.combine(start_date, timezone.datetime.min.time())
    )
    day_end = timezone.make_aware(
        timezone.datetime.combine(end_date + timedelta(days=1), timezone.datetime.min.time())
    )

    bookings = BookingDetail.objects.filter(
        room=room,
        start_date__lt=day_end,
        end_date__gt=day_start,
        booking__status__in=['pending', 'confirmed', 'checked_in', 'in_progress'],
        is_current=True
    ).select_related('booking', 'client', 'tariff')

    # Get maintenance periods
    maintenance_periods = RoomMaintenance.objects.filter(
        room=room,
        start_date__lt=day_end,
        end_date__gt=day_start
    )

    return {
        'room': {
            'id': room.id,
            'name': room.name,
            'room_type': room.room_type.name,
            'capacity': room.capacity,
            'price': room.price or 0,
            'is_active': room.is_active
        },
        'bookings': [
            {
                'id': bd.id,
                'booking_number': bd.booking.booking_number,
                'client_name': bd.client.get_full_name() if hasattr(bd.client, 'get_full_name') else f"{bd.client.f_name} {bd.client.l_name}",
                'start_date': bd.start_date.date(),
                'end_date': bd.end_date.date(),
                'tariff': bd.tariff.name if bd.tariff else 'N/A'
            }
            for bd in bookings
        ],
        'maintenance_periods': [
            {
                'id': mp.id,
                'type': mp.get_maintenance_type_display(),
                'status': mp.get_status_display(),
                'start_date': mp.start_date.date(),
                'end_date': mp.end_date.date(),
                'description': mp.description
            }
            for mp in maintenance_periods
        ]
    }


def validate_booking_from_matrix(
    room_id: int,
    start_date: date,
    end_date: date,
    patient_id: int,
    tariff_id: int
) -> Tuple[bool, str]:
    """
    Validate if a booking can be created from matrix selection.

    Args:
        room_id: Room ID
        start_date: Booking start date
        end_date: Booking end date
        patient_id: Patient ID
        tariff_id: Tariff ID

    Returns:
        Tuple of (is_valid, error_message)
    """
    from application.logus.utils.room_capacity import check_room_capacity

    # Check room exists and is active
    try:
        room = Room.objects.get(id=room_id, is_active=True)
    except Room.DoesNotExist:
        return False, "Room not found or inactive"

    # Convert dates to datetime for capacity check
    start_datetime = timezone.make_aware(
        timezone.datetime.combine(start_date, timezone.datetime.min.time())
    )
    end_datetime = timezone.make_aware(
        timezone.datetime.combine(end_date, timezone.datetime.min.time())
    )

    # Check capacity
    has_capacity, current, available, msg = check_room_capacity(
        room=room,
        start_date=start_datetime,
        end_date=end_datetime,
        guests_to_add=1
    )

    if not has_capacity:
        return False, msg

    # Check maintenance conflicts
    if RoomMaintenance.is_room_under_maintenance(room, start_datetime, end_datetime):
        return False, "Room is under maintenance during selected period"

    # Check patient exists
    try:
        PatientModel.objects.get(id=patient_id)
    except PatientModel.DoesNotExist:
        return False, "Patient not found"

    # Check tariff exists and is active
    from core.models.tariffs import Tariff
    try:
        Tariff.objects.get(id=tariff_id, is_active=True)
    except Tariff.DoesNotExist:
        return False, "Tariff not found or inactive"

    return True, "Validation successful"
