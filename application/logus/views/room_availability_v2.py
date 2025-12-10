"""
Room Availability Matrix V2 (RM2) Views

This module implements the view functions for the RM2 feature,
handling HTTP requests and responses for the room availability matrix interface.

FEATURE: RM2 - Room Availability V2
"""

import json
from datetime import datetime, date, timedelta

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db import transaction
from django.utils import timezone

from application.logus.services.room_availability_v2 import (
    get_availability_matrix_v2,
    get_room_booking_timeline,
    validate_booking_from_matrix
)
from core.models.rooms import Room, RoomType
from core.models.booking import Booking, BookingDetail, BookingHistory
from core.models.clients import PatientModel
from core.models.tariffs import Tariff, TariffService, ServiceSessionTracking


@login_required
def room_availability_matrix_v2_view(request):
    """
    Main view for RM2 feature.
    Renders the period x room types matrix interface.
    """
    # Get period from request or use defaults
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    room_type_id = request.GET.get('room_type_id')

    # Default period: today + 14 days
    if start_date_str and end_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%d.%m.%Y').date()
            end_date = datetime.strptime(end_date_str, '%d.%m.%Y').date()
        except ValueError:
            start_date = date.today()
            end_date = date.today() + timedelta(days=14)
    else:
        start_date = date.today()
        end_date = date.today() + timedelta(days=14)

    # Validate period
    if end_date <= start_date:
        end_date = start_date + timedelta(days=1)

    if (end_date - start_date).days > 90:
        # Limit to 90 days
        end_date = start_date + timedelta(days=90)

    # Get matrix data
    matrix_data = get_availability_matrix_v2(
        start_date=start_date,
        end_date=end_date,
        room_type_id=int(room_type_id) if room_type_id else None,
        include_inactive=False
    )

    # Get all room types for filter dropdown
    all_room_types = RoomType.objects.all()

    context = {
        'matrix_data': matrix_data,
        'all_room_types': all_room_types,
        'selected_room_type_id': int(room_type_id) if room_type_id else None,
        'start_date': start_date,
        'end_date': end_date,
        'start_date_str': start_date.strftime('%d.%m.%Y'),
        'end_date_str': end_date.strftime('%d.%m.%Y'),
    }

    return render(request, 'logus/room_availability_v2/matrix.html', context)


@login_required
@require_http_methods(["GET"])
def get_room_details_ajax(request):
    """
    AJAX endpoint to get detailed room information for dropdown.
    Called when user clicks on a matrix cell.
    """
    room_type_id = request.GET.get('room_type_id')
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    selected_date_str = request.GET.get('selected_date')

    try:
        start_date = datetime.strptime(start_date_str, '%d.%m.%Y').date()
        end_date = datetime.strptime(end_date_str, '%d.%m.%Y').date()
        room_type_id = int(room_type_id)
    except (ValueError, TypeError):
        return JsonResponse({'error': 'Invalid parameters'}, status=400)

    # Get detailed data for all rooms of this type
    matrix_data = get_availability_matrix_v2(
        start_date=start_date,
        end_date=end_date,
        room_type_id=room_type_id,
        include_inactive=False
    )

    # Extract rooms data and convert dates to strings for JSON serialization
    if matrix_data['room_types']:
        rooms_data = matrix_data['room_types'][0]['rooms']

        # Convert date objects to strings
        for room in rooms_data:
            for day_status in room['daily_status']:
                day_status['date'] = day_status['date'].strftime('%Y-%m-%d')
                for guest in day_status['guests']:
                    guest['start_date'] = guest['start_date'].strftime('%d.%m.%Y')
                    guest['end_date'] = guest['end_date'].strftime('%d.%m.%Y')

        room_type_name = matrix_data['room_types'][0]['name']
    else:
        rooms_data = []
        room_type_name = ''

    return JsonResponse({
        'success': True,
        'rooms': rooms_data,
        'room_type_name': room_type_name
    })


@login_required
@require_http_methods(["GET"])
def get_guest_details_ajax(request):
    """
    AJAX endpoint to get detailed guest information for tooltip.
    Called when user hovers over occupied cell.
    """
    booking_detail_id = request.GET.get('booking_detail_id')

    try:
        booking_detail = BookingDetail.objects.select_related(
            'booking', 'client', 'room', 'room__room_type', 'tariff'
        ).get(id=booking_detail_id)

        patient = booking_detail.client
        age = None
        if patient.date_of_birth:
            today = date.today()
            age = today.year - patient.date_of_birth.year
            if today.month < patient.date_of_birth.month or \
               (today.month == patient.date_of_birth.month and today.day < patient.date_of_birth.day):
                age -= 1

        # Get gender display
        gender_display = patient.gender if patient.gender else 'N/A'
        if hasattr(patient, 'get_gender_display'):
            gender_display = patient.get_gender_display()

        return JsonResponse({
            'success': True,
            'guest': {
                'full_name': patient.get_full_name() if hasattr(patient, 'get_full_name') else f"{patient.first_name} {patient.last_name}",
                'gender': gender_display,
                'age': age,
                'booking_number': booking_detail.booking.booking_number,
                'booking_status': booking_detail.booking.get_status_display(),
                'start_date': booking_detail.start_date.strftime('%d.%m.%Y'),
                'end_date': booking_detail.end_date.strftime('%d.%m.%Y'),
                'tariff_name': booking_detail.tariff.name if booking_detail.tariff else 'N/A',
                'room_name': booking_detail.room.name,
                'room_type': booking_detail.room.room_type.name
            }
        })
    except BookingDetail.DoesNotExist:
        return JsonResponse({'error': 'Booking detail not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def quick_book_from_matrix(request):
    """
    Create a quick booking directly from matrix.
    """
    try:
        data = json.loads(request.body)
        room_id = data.get('room_id')
        start_date_str = data.get('start_date')
        end_date_str = data.get('end_date')
        patient_id = data.get('patient_id')
        tariff_id = data.get('tariff_id')
        notes = data.get('notes', '')

        # Parse dates
        start_date = datetime.strptime(start_date_str, '%d.%m.%Y').date()
        end_date = datetime.strptime(end_date_str, '%d.%m.%Y').date()

        # Validate
        is_valid, message = validate_booking_from_matrix(
            room_id=int(room_id),
            start_date=start_date,
            end_date=end_date,
            patient_id=int(patient_id),
            tariff_id=int(tariff_id)
        )

        if not is_valid:
            return JsonResponse({'error': message}, status=400)

        # Create booking
        with transaction.atomic():
            # Get objects
            room = Room.objects.get(id=room_id)
            patient = PatientModel.objects.get(id=patient_id)
            tariff = Tariff.objects.get(id=tariff_id)

            # Convert dates to datetime
            start_datetime = timezone.make_aware(
                timezone.datetime.combine(start_date, timezone.datetime.min.time())
            )
            end_datetime = timezone.make_aware(
                timezone.datetime.combine(end_date, timezone.datetime.min.time())
            )

            # Create Booking
            booking = Booking.objects.create(
                staff=request.user,
                start_date=start_datetime,
                end_date=end_datetime,
                status='confirmed',
                notes=f'Quick booking created from RM2 matrix. {notes}' if notes else 'Quick booking created from RM2 matrix',
                booking_number=Booking.generate_booking_number()
            )

            # Create BookingDetail
            booking_detail = BookingDetail.objects.create(
                booking=booking,
                client=patient,
                room=room,
                tariff=tariff,
                price=tariff.price if hasattr(tariff, 'price') else 0,
                start_date=start_datetime,
                end_date=end_datetime,
                is_current=True,
                effective_from=start_datetime
            )

            # Initialize service session tracking
            tariff_services = TariffService.objects.filter(tariff=tariff)
            for ts in tariff_services:
                ServiceSessionTracking.objects.create(
                    booking_detail=booking_detail,
                    service=ts.service,
                    tariff_service=ts,
                    sessions_included=ts.sessions_included,
                    sessions_used=0,
                    sessions_billed=0
                )

            # Log in history
            BookingHistory.log_change(
                booking=booking,
                action='CREATED',
                description=f'Quick booking created from RM2 matrix for room {room.name}',
                changed_by=request.user
            )

            return JsonResponse({
                'success': True,
                'booking_id': booking.id,
                'booking_number': booking.booking_number,
                'redirect_url': f'/logus/booking/{booking.id}/'
            })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["GET"])
def export_matrix_excel(request):
    """
    Export availability matrix to Excel file.
    """
    # This would use openpyxl or xlsxwriter similar to existing report exports
    # For now, return a placeholder response
    return JsonResponse({
        'message': 'Excel export feature coming soon',
        'status': 'not_implemented'
    }, status=501)
