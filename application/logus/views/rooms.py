# views.py

from datetime import datetime, timedelta
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from core.models import Room, RoomType, Tariff, TariffRoomPrice, BookingDetail

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


# logus/views/dashboard.py
from datetime import datetime, timedelta
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.http import JsonResponse
from django.db.models import Q, Count
from django.contrib import messages

from core.models import Room, RoomType, Booking, BookingDetail, PatientModel, Tariff


@login_required
def reception_dashboard(request):
    """
    Main dashboard view for reception staff to check room availability
    """
    context = {
        'room_types': RoomType.objects.all(),
        'show_results': False,
    }

    # Get today's date for summary statistics
    today = timezone.now().date()
    today_start = timezone.make_aware(datetime.combine(today, datetime.min.time()))
    today_end = timezone.make_aware(datetime.combine(today, datetime.max.time()))

    # Calculate summary statistics
    context['total_rooms'] = Room.objects.filter(is_active=True).count()

    # Get available rooms for today
    occupied_today = BookingDetail.objects.filter(
        booking__start_date__lte=today_end,
        booking__end_date__gte=today_start,
        booking__status__in=['confirmed', 'checked_in']
    ).values_list('room_id', flat=True).distinct()

    context['available_today'] = Room.objects.filter(
        is_active=True
    ).exclude(id__in=occupied_today).count()

    # Get check-ins for today
    context['todays_checkins'] = BookingDetail.objects.filter(
        booking__start_date__gte=today_start,
        booking__start_date__lte=today_end,
        booking__status='confirmed'
    ).select_related('booking', 'client', 'room')
    context['checkins_today'] = context['todays_checkins'].count()

    # Get check-outs for today
    context['todays_checkouts'] = BookingDetail.objects.filter(
        booking__end_date__gte=today_start,
        booking__end_date__lte=today_end,
        booking__status='checked_in'
    ).select_related('booking', 'client', 'room')
    context['checkouts_today'] = context['todays_checkouts'].count()

    # Handle form submission
    if request.method == 'POST':
        date_range = request.POST.get('date_range', '')
        room_type_id = request.POST.get('room_type_id', '')

        if date_range:
            try:
                # Parse date range
                start_str, end_str = date_range.split(' - ')
                start_date = datetime.strptime(start_str, '%d.%m.%Y')
                end_date = datetime.strptime(end_str, '%d.%m.%Y')

                # Add time components (14:00 check-in, 12:00 checkout)
                start_datetime = timezone.make_aware(
                    datetime.combine(start_date, datetime(1, 1, 1, 14, 0).time())
                )
                end_datetime = timezone.make_aware(
                    datetime.combine(end_date, datetime(1, 1, 1, 12, 0).time())
                )

                context['start_date'] = start_datetime
                context['end_date'] = end_datetime
                context['date_range'] = date_range
                context['show_results'] = True

                # Get occupied rooms for the date range
                occupied_bookings = BookingDetail.objects.filter(
                    booking__start_date__lt=end_datetime,
                    booking__end_date__gt=start_datetime,
                    booking__status__in=['pending', 'confirmed', 'checked_in']
                ).select_related('room', 'client', 'booking')

                occupied_room_ids = list(occupied_bookings.values_list('room_id', flat=True))

                # Build query for available rooms
                available_rooms_query = Room.objects.filter(
                    is_active=True
                ).exclude(id__in=occupied_room_ids)

                # Filter by room type if specified
                if room_type_id:
                    available_rooms_query = available_rooms_query.filter(room_type_id=room_type_id)
                    context['selected_room_type'] = RoomType.objects.get(id=room_type_id)
                    context['selected_room_type_id'] = room_type_id

                # Get available rooms
                context['available_rooms'] = available_rooms_query.select_related('room_type')

                # Process occupied rooms data
                occupied_rooms_data = []
                for booking_detail in occupied_bookings:
                    # Filter by room type if needed
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

                context['occupied_rooms'] = occupied_rooms_data

                # Calculate statistics
                total_rooms = available_rooms_query.count() + len(occupied_rooms_data)
                context['total_capacity'] = sum(room.capacity for room in context['available_rooms']) + \
                                            sum(data['room'].capacity for data in occupied_rooms_data)

                if total_rooms > 0:
                    context['occupancy_rate'] = (len(occupied_rooms_data) / total_rooms) * 100
                else:
                    context['occupancy_rate'] = 0

            except ValueError as e:
                messages.error(request, f'Неверный формат даты: {str(e)}')

    # Get patients and tariffs for quick booking modal
    context['patients'] = PatientModel.objects.filter(is_active=True).order_by('f_name', 'l_name')
    context['tariffs'] = Tariff.objects.filter(is_active=True)

    return render(request, 'logus/dashboard/reception_dashboard.html', context)


@login_required
def create_quick_booking(request):
    """
    AJAX endpoint for creating quick bookings from the dashboard
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request method'})

    try:
        # Get data from request
        room_id = request.POST.get('room_id')
        patient_id = request.POST.get('patient_id')
        tariff_id = request.POST.get('tariff_id')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        notes = request.POST.get('notes', '')

        # Check if creating new patient
        is_new_patient = request.POST.get('is_new_patient') == 'true'

        if is_new_patient:
            # Create new patient
            patient = PatientModel.objects.create(
                f_name=request.POST.get('f_name'),
                l_name=request.POST.get('l_name'),
                mid_name=request.POST.get('mid_name', ''),
                date_of_birth=request.POST.get('date_of_birth'),
                gender=request.POST.get('gender') == '1',  # Convert to boolean
                mobile_phone_number=request.POST.get('mobile_phone_number', ''),
                home_phone_number=request.POST.get('home_phone_number', ''),
                email=request.POST.get('email', '') or None,  # Convert empty string to None
                country=request.POST.get('country', ''),
                address=request.POST.get('address', ''),
                doc_type=request.POST.get('doc_type', ''),
                doc_number=request.POST.get('doc_number', ''),
                is_active=True,
                created_by=request.user,
                modified_by=request.user
            )
            new_patient_created = True
        else:
            # Get existing patient
            patient_id = request.POST.get('patient_id')
            if not patient_id:
                return JsonResponse({'success': False, 'message': 'Patient ID is required'})
            patient = PatientModel.objects.get(id=patient_id)
            new_patient_created = False

        # Validate required fields
        if not all([room_id, patient_id, tariff_id, start_date, end_date]):
            return JsonResponse({'success': False, 'message': 'Missing required fields'})

        # Get objects
        room = Room.objects.get(id=room_id)
        # patient = PatientModel.objects.get(id=patient_id)
        tariff = Tariff.objects.get(id=tariff_id)

        # Parse dates and add times
        start_datetime = timezone.make_aware(
            datetime.strptime(start_date + ' 14:00', '%Y-%m-%d %H:%M')
        )
        end_datetime = timezone.make_aware(
            datetime.strptime(end_date + ' 12:00', '%Y-%m-%d %H:%M')
        )

        # Check if room is available
        existing_bookings = BookingDetail.objects.filter(
            room=room,
            booking__start_date__lt=end_datetime,
            booking__end_date__gt=start_datetime,
            booking__status__in=['pending', 'confirmed', 'checked_in']
        ).exists()

        if existing_bookings:
            return JsonResponse({
                'success': False,
                'message': 'Комната уже забронирована на эти даты'
            })

        # Generate booking number
        booking_number = generate_booking_number()

        # Create booking
        booking = Booking.objects.create(
            booking_number=booking_number,
            staff=request.user,
            start_date=start_datetime,
            end_date=end_datetime,
            notes=notes,
            status='confirmed',
            created_by=request.user,
            modified_by=request.user
        )

        # Create booking detail
        BookingDetail.objects.create(
            booking=booking,
            client=patient,
            room=room,
            tariff=tariff,
            created_by=request.user,
            modified_by=request.user
        )

        return JsonResponse({
            'success': True,
            'booking_number': booking_number,
            'booking_id': booking.id,
            'new_patient_created': new_patient_created
        })

    except Room.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Комната не найдена'})
    except PatientModel.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Пациент не найден'})
    except Tariff.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Тариф не найден'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


def generate_booking_number():
    """Generate a unique booking number"""
    import uuid
    prefix = "HMC"
    timestamp = timezone.now().strftime("%Y%m%d")
    random_suffix = str(uuid.uuid4().int)[:4]
    return f"{prefix}-{timestamp}-{random_suffix}"