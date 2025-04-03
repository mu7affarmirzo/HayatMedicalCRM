# views.py
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from datetime import datetime
from core.applications.logus.services.rooms import get_availability_matrix

from datetime import datetime, timedelta
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from core.models import Room, RoomType, Tariff, TariffRoomPrice, Booking, BookingDetail

# Dictionary for weekday names
WEEKDAYS = {
    1: 'Понедельник',
    2: 'Вторник',
    3: 'Среда',
    4: 'Четверг',
    5: 'Пятница',
    6: 'Суббота',
    7: 'Воскресенье'
}


def get_available_rooms(start_date, end_date, room_type_id=None):
    """Get available rooms for a date range and optional room type"""
    # Find rooms that have bookings overlapping with our date range
    booked_room_ids = BookingDetail.objects.filter(
        booking__start_date__lt=end_date,
        booking__end_date__gt=start_date,
        booking__status__in=['pending', 'confirmed', 'checked_in']
    ).values_list('room_id', flat=True)

    # Query for available rooms
    available_rooms = Room.objects.filter(is_active=True).exclude(id__in=booked_room_ids)

    # Filter by room type if specified
    if room_type_id:
        available_rooms = available_rooms.filter(room_type_id=room_type_id)

    return available_rooms


def get_the_days_list(start_str, end_str):
    """Generate list of days between start and end date"""
    start_date = datetime.strptime(start_str, '%m/%d/%Y')
    end_date = datetime.strptime(end_str, '%m/%d/%Y')

    date_list = []
    current_date = start_date

    while current_date <= end_date:
        day = current_date.strftime("%d-%B")
        week_day = WEEKDAYS[current_date.weekday() + 1]
        date_list.append([day, week_day])
        current_date += timedelta(days=1)

    return date_list


@login_required
def available_room_view(request):
    context = {}
    staff = request.user

    today = datetime.today()

    tariffs = Tariff.objects.filter(is_active=True)
    room_types = RoomType.objects.all()

    # Create a matrix dictionary to store the room type and tariff values
    matrix = {}
    for room_type in room_types:
        matrix[room_type] = []
        for tariff in tariffs:
            try:
                value = TariffRoomPrice.objects.get(tariff=tariff, room_type=room_type).price
            except TariffRoomPrice.DoesNotExist:
                value = None
            matrix[room_type].append(value)

    next_14_days = [today + timedelta(days=i) for i in range(14)]
    formatted_dates = []
    for date in next_14_days:
        day = date.strftime("%d-%B")
        week_day = WEEKDAYS[date.weekday() + 1]
        formatted_dates.append([day, week_day])

    context = {
        'user': staff,
        'days': formatted_dates,
        'tariffs': tariffs,
        'room_types': room_types,
        'matrix': matrix
    }

    if request.method == 'POST':
        date_range = request.POST.get('reservation_time')
        room_type_id = request.POST.get('room_type')

        if date_range and room_type_id:
            start_str, end_str = date_range.split(' - ')

            start_date = datetime.strptime(start_str, '%m/%d/%Y')
            end_date = datetime.strptime(end_str, '%m/%d/%Y')

            available_rooms = get_available_rooms(start_date, end_date, room_type_id)

            # Get tariff pricing for the selected room type
            room_type = RoomType.objects.get(id=room_type_id)
            tariff_prices = {}
            for tariff in tariffs:
                try:
                    price = TariffRoomPrice.objects.get(tariff=tariff, room_type=room_type).price
                    tariff_prices[tariff.id] = price
                except TariffRoomPrice.DoesNotExist:
                    tariff_prices[tariff.id] = None

            formatted_dates = get_the_days_list(start_str, end_str)

            context.update({
                'days': formatted_dates,
                'rooms': available_rooms,
                'selected_room_type': room_type,
                'tariff_prices': tariff_prices,
                'start_date': start_date,
                'end_date': end_date,
                'date_range': date_range
            })

    return render(request, 'logus/available_rooms.html', context)



# @login_required
# def check_availability(request):
#     """View to check room availability for a date range"""
#     if request.method == 'GET':
#         return render(request, 'logus/check_availability.html')
#
#     elif request.method == 'POST':
#         try:
#             start_date = request.POST.get('start_date')
#             end_date = request.POST.get('end_date')
#
#             # Convert to datetime objects
#             start_date = datetime.strptime(start_date, '%Y-%m-%d')
#             end_date = datetime.strptime(end_date, '%Y-%m-%d')
#
#             # Get the availability matrix
#             availability_data = get_availability_matrix(start_date, end_date)
#
#             # For AJAX requests
#             if request.headers.get('x-requested-with') == 'XMLHttpRequest':
#                 return JsonResponse(availability_data)
#
#             # For regular form submissions
#             return render(request, 'logus/availability_matrix.html', {
#                 'start_date': start_date,
#                 'end_date': end_date,
#                 'tariffs': availability_data['tariffs'],
#                 'matrix': availability_data['matrix']
#             })
#
#         except Exception as e:
#             if request.headers.get('x-requested-with') == 'XMLHttpRequest':
#                 return JsonResponse({'error': str(e)}, status=400)
#             else:
#                 return render(request, 'logus/check_availability.html', {
#                     'error': str(e)
#                 })
