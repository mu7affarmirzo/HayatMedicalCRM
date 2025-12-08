"""
Room capacity validation utilities for HayatMedicalCRM
Implements TASK-007: Room capacity validation enforcement

This module provides functions to check room availability based on capacity,
preventing overbooking of rooms.
"""

import logging
from django.db.models import Count, Q
from django.utils import timezone

logger = logging.getLogger(__name__)


def get_room_occupancy_count(room, start_date, end_date, exclude_booking_id=None):
    """
    Get the number of guests currently booked in a room for the given date range.

    Args:
        room: Room instance
        start_date: datetime - start of date range
        end_date: datetime - end of date range
        exclude_booking_id: Optional booking ID to exclude from count (for updates)

    Returns:
        int: Number of guests currently booked in the room
    """
    from core.models import BookingDetail

    # Build query for overlapping bookings
    query = Q(
        room=room,
        booking__start_date__lt=end_date,
        booking__end_date__gt=start_date,
        booking__status__in=['pending', 'confirmed', 'checked_in', 'in_progress']
    )

    # Exclude specific booking if updating
    if exclude_booking_id:
        query &= ~Q(booking_id=exclude_booking_id)

    # Count booking details (each represents one guest)
    occupancy = BookingDetail.objects.filter(query).count()

    return occupancy


def check_room_capacity(room, start_date, end_date, guests_to_add=1, exclude_booking_id=None):
    """
    Check if a room has capacity for additional guests.

    Args:
        room: Room instance
        start_date: datetime - start of date range
        end_date: datetime - end of date range
        guests_to_add: int - number of guests wanting to book (default 1)
        exclude_booking_id: Optional booking ID to exclude from count

    Returns:
        tuple: (has_capacity: bool, current_occupancy: int, available_spots: int, message: str)
    """
    current_occupancy = get_room_occupancy_count(room, start_date, end_date, exclude_booking_id)
    available_spots = room.capacity - current_occupancy
    has_capacity = available_spots >= guests_to_add

    if has_capacity:
        message = f"Комната {room.name} имеет {available_spots} свободных мест"
    else:
        message = (
            f"Комната {room.name} переполнена: "
            f"занято {current_occupancy}/{room.capacity}, "
            f"требуется {guests_to_add} мест, доступно {available_spots}"
        )

    logger.debug(
        f"Capacity check for room {room.name}: "
        f"occupancy={current_occupancy}, capacity={room.capacity}, "
        f"available={available_spots}, guests_to_add={guests_to_add}, "
        f"has_capacity={has_capacity}"
    )

    return has_capacity, current_occupancy, available_spots, message


def get_rooms_with_capacity(start_date, end_date, room_type_id=None):
    """
    Get all rooms that have available capacity for the given date range.

    Args:
        start_date: datetime - start of date range
        end_date: datetime - end of date range
        room_type_id: Optional room type filter

    Returns:
        QuerySet of rooms with annotated capacity information
    """
    from core.models import Room, BookingDetail

    # Get all active rooms
    rooms_query = Room.objects.filter(is_active=True)

    if room_type_id:
        rooms_query = rooms_query.filter(room_type_id=room_type_id)

    # For each room, we need to check if it has capacity
    rooms_with_capacity = []

    for room in rooms_query.select_related('room_type'):
        current_occupancy = get_room_occupancy_count(room, start_date, end_date)
        available_spots = room.capacity - current_occupancy

        if available_spots > 0:
            # Annotate the room with capacity info
            room.current_occupancy = current_occupancy
            room.available_spots = available_spots
            rooms_with_capacity.append(room)

    return rooms_with_capacity


def validate_booking_capacity(booking_details_data, start_date, end_date, exclude_booking_id=None):
    """
    Validate that a booking doesn't exceed room capacities.

    Args:
        booking_details_data: List of dicts with 'room_id' and 'client_id'
        start_date: datetime
        end_date: datetime
        exclude_booking_id: Optional booking ID to exclude (for updates)

    Returns:
        tuple: (is_valid: bool, errors: list of error messages)
    """
    from core.models import Room
    from collections import defaultdict

    # Count how many guests are being booked per room
    room_guest_counts = defaultdict(int)
    for detail in booking_details_data:
        room_guest_counts[detail['room_id']] += 1

    errors = []

    for room_id, guest_count in room_guest_counts.items():
        try:
            room = Room.objects.get(id=room_id)
            has_capacity, current_occupancy, available_spots, message = check_room_capacity(
                room, start_date, end_date, guest_count, exclude_booking_id
            )

            if not has_capacity:
                errors.append(message)

        except Room.DoesNotExist:
            errors.append(f"Комната с ID {room_id} не найдена")

    is_valid = len(errors) == 0

    if is_valid:
        logger.info(f"Booking capacity validation passed for {len(booking_details_data)} guests")
    else:
        logger.warning(f"Booking capacity validation failed: {errors}")

    return is_valid, errors


def get_room_availability_details(room, start_date, end_date):
    """
    Get detailed availability information for a specific room.

    Args:
        room: Room instance
        start_date: datetime
        end_date: datetime

    Returns:
        dict with detailed availability information
    """
    from core.models import BookingDetail

    current_occupancy = get_room_occupancy_count(room, start_date, end_date)
    available_spots = room.capacity - current_occupancy
    occupancy_percentage = (current_occupancy / room.capacity * 100) if room.capacity > 0 else 0

    # Get booking details for this room in the date range
    overlapping_bookings = BookingDetail.objects.filter(
        room=room,
        booking__start_date__lt=end_date,
        booking__end_date__gt=start_date,
        booking__status__in=['pending', 'confirmed', 'checked_in', 'in_progress']
    ).select_related('booking', 'client').order_by('booking__start_date')

    return {
        'room': room,
        'capacity': room.capacity,
        'current_occupancy': current_occupancy,
        'available_spots': available_spots,
        'is_fully_booked': available_spots == 0,
        'has_capacity': available_spots > 0,
        'occupancy_percentage': occupancy_percentage,
        'bookings': list(overlapping_bookings),
        'booking_count': overlapping_bookings.count(),
    }
