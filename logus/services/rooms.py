# services.py
from django.db.models import Q
from core.models import Room, RoomType, Tariff, TariffRoomPrice, Booking, BookingDetail


def get_availability_matrix(start_date, end_date):
    """
    Generate a matrix of room x tariff with availability information
    """

    room_types = RoomType.objects.all().prefetch_related('rooms')
    tariffs = Tariff.objects.filter(is_active=True)

    # Get all bookings that overlap with the date range
    overlapping_bookings = BookingDetail.objects.filter(
        booking__start_date__lt=end_date,
        booking__end_date__gt=start_date,
        booking__status__in=['pending', 'confirmed', 'checked_in']
    ).select_related('room')

    # Create a set of room IDs that are already booked
    booked_room_ids = set(overlapping_bookings.values_list('room_id', flat=True))

    # Prefetch prices
    prices = {}
    for price in TariffRoomPrice.objects.all():
        prices[(price.tariff_id, price.room_type_id)] = price.price

    # Build the matrix
    matrix = []

    for room_type in room_types:
        rooms_data = []

        for room in room_type.rooms.filter(is_active=True):
            room_availability = []
            is_room_available = room.id not in booked_room_ids

            for tariff in tariffs:
                price_key = (tariff.id, room_type.id)
                price = prices.get(price_key)

                room_availability.append({
                    'tariff_id': tariff.id,
                    'tariff_name': tariff.name,
                    'is_available': is_room_available,
                    'price': price
                })

            rooms_data.append({
                'room_id': room.id,
                'room_name': room.name,
                'availability': room_availability
            })

        matrix.append({
            'room_type_id': room_type.id,
            'room_type_name': room_type.name,
            'rooms': rooms_data
        })

    return {
        'tariffs': [{'id': t.id, 'name': t.name} for t in tariffs],
        'matrix': matrix
    }
