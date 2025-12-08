import uuid
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_http_methods

from application.logus.forms.patient_form import PatientRegistrationForm
from core.models import Booking, BookingDetail, Room, PatientModel, Tariff, RoomType, TariffRoomPrice, District, Region
from core.models.tariffs import ServiceSessionTracking
from application.logus.forms.booking import (
    BookingInitialForm, RoomSelectionForm, BookingConfirmationForm,
    TariffChangeForm, ServiceSessionRecordForm
)
from application.logus.utils.room_capacity import (
    get_rooms_with_capacity, validate_booking_capacity, check_room_capacity
)

logger = logging.getLogger(__name__)


@login_required
def booking_start(request):
    """
    First step of booking process - select patient, dates, and guests count
    """
    # Default date range (today to week later)
    today = timezone.now().date()
    week_later = today + timezone.timedelta(days=7)
    default_date_range = f"{today.strftime('%d.%m.%Y')} - {week_later.strftime('%d.%m.%Y')}"

    if request.method == 'POST':
        form = BookingInitialForm(request.POST)
        if form.is_valid():
            # Store form data in session
            request.session['booking_data'] = {
                'patient_id': form.cleaned_data['patient'].id,
                'start_date': form.cleaned_data['start_date'].isoformat(),
                'end_date': form.cleaned_data['end_date'].isoformat(),
                'guests_count': form.cleaned_data['guests_count'],
                'date_range': form.cleaned_data['date_range']  # Store the original date range string
            }
            return redirect('logus:booking_select_rooms')
    else:
        form = BookingInitialForm(initial={'date_range': default_date_range})

    return render(request, 'logus/booking/booking_start.html', {
        'form': form,
        'step': 1,
        'total_steps': 3
    })


@login_required
def booking_select_rooms(request):
    """
    Second step of booking process - select rooms based on availability
    """
    # Check if we have the necessary data from step 1
    booking_data = request.session.get('booking_data')
    if not booking_data:
        messages.error(request, 'Пожалуйста, начните процесс бронирования сначала')
        return redirect('logus:booking_start')

    # Convert session data back to Python objects
    start_date = timezone.datetime.fromisoformat(booking_data['start_date'])
    end_date = timezone.datetime.fromisoformat(booking_data['end_date'])
    guests_count = booking_data['guests_count']

    # Get available rooms for the date range
    available_rooms = get_available_rooms(start_date, end_date)

    if request.method == 'POST':
        form = RoomSelectionForm(request.POST, available_rooms=available_rooms, guests_count=guests_count)
        if form.is_valid():
            # Store room selections in session
            selected_rooms = []
            for i in range(guests_count):
                field_name = f'room_{i}'
                if field_name in form.cleaned_data:
                    selected_rooms.append(form.cleaned_data[field_name])

            booking_data['selected_rooms'] = selected_rooms
            request.session['booking_data'] = booking_data
            return redirect('logus:booking_confirm')
    else:
        form = RoomSelectionForm(available_rooms=available_rooms, guests_count=guests_count)

    # Get room type availability data for the table display
    room_type_availability = get_room_type_availability(start_date, end_date)

    return render(request, 'logus/booking/booking_select_rooms.html', {
        'form': form,
        'step': 2,
        'total_steps': 3,
        'room_type_availability': room_type_availability,
        'start_date': start_date,
        'end_date': end_date,
        'date_range': get_date_range(start_date, end_date)
    })


@login_required
def booking_confirm(request):
    """
    Final step of booking process - review and confirm booking
    """
    # Check if we have the necessary data from previous steps
    booking_data = request.session.get('booking_data')
    if not booking_data or 'selected_rooms' not in booking_data:
        messages.error(request, 'Пожалуйста, начните процесс бронирования сначала')
        return redirect('booking_start')  # Fixed: removed 'logus:' namespace

    start_date = timezone.datetime.fromisoformat(booking_data['start_date'])
    end_date = timezone.datetime.fromisoformat(booking_data['end_date'])
    patient = get_object_or_404(PatientModel, id=booking_data['patient_id'])
    selected_room_ids = booking_data['selected_rooms']
    selected_rooms = Room.objects.filter(id__in=selected_room_ids)

    if request.method == 'POST':
        form = BookingConfirmationForm(request.POST)
        if form.is_valid():
            try:
                # TASK-007: Validate room capacity before creating booking
                booking_details_data = [{'room_id': room_id, 'client_id': patient.id}
                                       for room_id in selected_room_ids]
                is_valid, capacity_errors = validate_booking_capacity(
                    booking_details_data, start_date, end_date
                )

                if not is_valid:
                    for error in capacity_errors:
                        messages.error(request, error)
                    logger.warning(
                        f"Booking capacity validation failed for patient {patient.id}: {capacity_errors}"
                    )
                    # Redirect back to room selection
                    return redirect('logus:booking_select_rooms')

                # Create the main booking
                booking = Booking.objects.create(
                    booking_number=generate_booking_number(),
                    staff=request.user,
                    start_date=start_date,
                    end_date=end_date,
                    notes=form.cleaned_data.get('notes', ''),
                    status='confirmed',
                    created_by=request.user  # Add this for audit trail
                )

                # Default tariff - you may want to make this selectable
                default_tariff = Tariff.objects.first()

                if not default_tariff:
                    raise ValueError("Нет доступных тарифов. Пожалуйста, создайте тариф в административной панели.")

                # Create booking details for each room
                for room_id in selected_room_ids:
                    room = Room.objects.get(id=room_id)

                    # Calculate price based on tariff and room type
                    try:
                        tariff_price = TariffRoomPrice.objects.get(
                            tariff=default_tariff,
                            room_type=room.room_type
                        )
                        price = tariff_price.price
                    except TariffRoomPrice.DoesNotExist:
                        # Fallback to room's base price or 0
                        price = room.price or 0

                    BookingDetail.objects.create(
                        booking=booking,
                        client=patient,
                        room=room,
                        tariff=default_tariff,
                        price=price,  # Set the price explicitly
                        created_by=request.user
                    )

                # Clear session data
                if 'booking_data' in request.session:
                    del request.session['booking_data']

                messages.success(request, f'Бронирование #{booking.booking_number} успешно создано!')

                # Fixed: Use correct URL name without namespace
                return redirect('logus:booking_detail', booking_id=booking.id)

            except Exception as e:
                messages.error(request, f'Ошибка при создании бронирования: {str(e)}')
        else:
            messages.error(request, 'Пожалуйста, исправьте ошибки в форме')
    else:
        form = BookingConfirmationForm()

    return render(request, 'logus/booking/booking_confirm.html', {  # Fixed template path
        'form': form,
        'step': 3,
        'total_steps': 3,
        'patient': patient,
        'start_date': start_date,
        'end_date': end_date,
        'selected_rooms': selected_rooms
    })


@login_required
def booking_detail(request, booking_id):
    """
    View booking details with support for status change actions
    """
    booking = get_object_or_404(Booking, id=booking_id)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'checkin':
            # Handle check-in action
            if booking.status in ['pending', 'confirmed']:
                booking.status = 'checked_in'
                booking.modified_by = request.user
                booking.save()

                messages.success(
                    request,
                    f'Бронирование #{booking.booking_number} успешно переведено в статус "Заселен"'
                )

                # Log the action (optional)
                import logging
                logger = logging.getLogger(__name__)
                logger.info(f'Booking {booking.booking_number} checked in by {request.user.username}')

            else:
                messages.error(
                    request,
                    f'Невозможно заселить бронирование со статусом "{booking.get_status_display()}"'
                )

        elif action == 'cancel':
            # Handle cancellation action
            if booking.status in ['pending', 'confirmed']:
                cancel_reason = request.POST.get('cancel_reason', '')

                booking.status = 'cancelled'
                booking.modified_by = request.user

                # Add cancel reason to notes if provided
                if cancel_reason:
                    current_notes = booking.notes or ''
                    booking.notes = f"{current_notes}\n\nОтменено {timezone.now().strftime('%d.%m.%Y %H:%M')}: {cancel_reason}".strip()

                booking.save()

                messages.success(
                    request,
                    f'Бронирование #{booking.booking_number} отменено'
                )

                # Log the action (optional)
                import logging
                logger = logging.getLogger(__name__)
                logger.info(
                    f'Booking {booking.booking_number} cancelled by {request.user.username}. Reason: {cancel_reason}')

            else:
                messages.error(
                    request,
                    f'Невозможно отменить бронирование со статусом "{booking.get_status_display()}"'
                )

        elif action == 'checkout':
            # Handle checkout action
            if booking.status == 'checked_in':
                booking.status = 'completed'
                booking.modified_by = request.user
                booking.save()

                messages.success(
                    request,
                    f'Бронирование #{booking.booking_number} завершено (выселение)'
                )

                # Log the action (optional)
                import logging
                logger = logging.getLogger(__name__)
                logger.info(f'Booking {booking.booking_number} checked out by {request.user.username}')

            else:
                messages.error(
                    request,
                    f'Невозможно выселить из бронирования со статусом "{booking.get_status_display()}"'
                )

        else:
            messages.error(request, 'Неизвестное действие')

        # Redirect to prevent re-submission on refresh
        return redirect('logus:booking_detail', booking_id=booking.id)

    # Calculate some additional info for the template
    context = {
        'booking': booking,
        'can_checkin': booking.status in ['pending', 'confirmed'],
        'can_cancel': booking.status in ['pending', 'confirmed'],
        'can_checkout': booking.status == 'checked_in',
        'total_guests': booking.details.count(),
        'duration_days': (booking.end_date.date() - booking.start_date.date()).days,
    }

    return render(request, 'logus/booking/booking_detail.html', context)


def get_available_rooms(start_date, end_date):
    """
    Get rooms that have available capacity in the given date range.
    Updated to check room capacity instead of binary availability (TASK-007).
    """
    # Use the capacity-aware utility function
    rooms_with_capacity = get_rooms_with_capacity(start_date, end_date)

    # Convert list back to queryset-like structure for compatibility
    # Extract room IDs that have capacity
    room_ids_with_capacity = [room.id for room in rooms_with_capacity]

    # Return as queryset
    available_rooms = Room.objects.filter(id__in=room_ids_with_capacity, is_active=True)

    return available_rooms


def get_room_type_availability(start_date, end_date):
    """
    Get availability counts for each room type for the date range
    """
    date_range = get_date_range(start_date, end_date)

    # Initialize result structure
    result = {}

    for date in date_range:
        current_date = date.replace(hour=12, minute=0, second=0, microsecond=0)
        next_date = current_date + timezone.timedelta(days=1)

        room_types = RoomType.objects.all()

        for room_type in room_types:
            if room_type.id not in result:
                result[room_type.id] = {
                    'name': room_type.name,
                    'dates': {}
                }

            # Count total rooms of this type
            total_rooms = Room.objects.filter(room_type=room_type).count()

            # Count booked rooms of this type for the current date
            booked_rooms = BookingDetail.objects.filter(
                room__room_type=room_type,
                booking__start_date__lt=next_date,
                booking__end_date__gt=current_date,
                booking__status__in=['pending', 'confirmed', 'checked_in']
            ).values('room').distinct().count()

            # Calculate available rooms
            available_rooms = total_rooms - booked_rooms

            # Store in result
            date_str = current_date.strftime('%Y-%m-%d')
            result[room_type.id]['dates'][date_str] = {
                'total': total_rooms,
                'available': available_rooms
            }

    return result


def get_date_range(start_date, end_date):
    """
    Generate a list of dates between start_date and end_date
    """
    delta = end_date.date() - start_date.date()
    dates = [start_date + timezone.timedelta(days=i) for i in range(delta.days + 1)]
    return dates


def generate_booking_number():
    """
    Generate a unique booking number
    """
    prefix = "HMC"
    timestamp = timezone.now().strftime("%Y%m%d")
    random_suffix = str(uuid.uuid4().int)[:4]
    return f"{prefix}-{timestamp}-{random_suffix}"


@login_required
@require_POST
def check_room_availability_ajax(request):
    """
    AJAX endpoint to check room availability for a specific date range
    """
    date_range = request.POST.get('date_range')

    try:
        # Parse the date range string (format: "DD.MM.YYYY - DD.MM.YYYY")
        start_date_str, end_date_str = date_range.split(' - ')

        # Add default check-in/check-out times (14:00 for check-in, 12:00 for check-out)
        start_date = timezone.datetime.strptime(start_date_str + ' 14:00', '%d.%m.%Y %H:%M')
        end_date = timezone.datetime.strptime(end_date_str + ' 12:00', '%d.%m.%Y %H:%M')

        # Convert to timezone-aware datetime if needed
        if timezone.is_naive(start_date):
            start_date = timezone.make_aware(start_date)
        if timezone.is_naive(end_date):
            end_date = timezone.make_aware(end_date)

        room_type_availability = get_room_type_availability(start_date, end_date)

        return JsonResponse({
            'status': 'success',
            'data': room_type_availability
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=400)


@login_required
@require_POST
def add_new_patient(request):
    """
    DEPRECATED: This is a duplicate of the patient creation view.
    Redirects to logus:patient_create_view instead.

    TODO: Update all references to use logus:patient_create_view and remove this function.
    """
    try:
        form = PatientRegistrationForm(request.POST)
        if form.is_valid():
            patient = form.save(commit=False)
            patient.created_by = request.user
            patient.modified_by = request.user
            patient.save()
            messages.success(request, f'Пациент "{patient.full_name}" успешно создан!')
            return redirect('logus:booking_start')
        else:
            logger.warning(f"Form validation errors: {form.errors}")
            messages.error(request, 'Пожалуйста, исправьте ошибки в форме')
            return redirect('logus:booking_start')
    except Exception as e:
        logger.error(f"Error creating patient: {e}", exc_info=True)
        messages.error(request, 'Произошла ошибка при создании пациента')
        return redirect('logus:booking_start')


def get_districts(request):
    region_id = request.GET.get('region_id')
    districts = District.objects.filter(region_id=region_id, is_active=True).values('id', 'name')
    return JsonResponse(list(districts), safe=False)


@login_required
@require_http_methods(["GET", "POST"])
def patient_registration(request):
    """
    DEPRECATED: This is a duplicate of the patient creation view.
    Use logus:patient_create_view instead.

    Patient registration view for booking flow.
    """
    try:
        if request.method == 'POST':
            form = PatientRegistrationForm(request.POST)
            if form.is_valid():
                patient = form.save(commit=False)
                patient.created_by = request.user
                patient.modified_by = request.user
                patient.save()
                messages.success(request, f'Пациент "{patient.full_name}" успешно создан!')
                return redirect('logus:booking_start')
            else:
                logger.warning(f"Form validation errors: {form.errors}")
                messages.error(request, 'Пожалуйста, исправьте ошибки в форме')
        else:
            form = PatientRegistrationForm()

        context = {
            'form': form,
            'regions': Region.objects.filter(is_active=True)
        }
        return render(request, 'logus/booking/patient_registration_page.html', context)

    except Exception as e:
        logger.error(f"Error in patient registration: {e}", exc_info=True)
        messages.error(request, 'Произошла ошибка при регистрации пациента')
        return redirect('logus:booking_start')


@login_required
@require_http_methods(["GET", "POST"])
def tariff_change_view(request, detail_id):
    """
    Handle mid-stay tariff and/or room change for a booking detail.
    Implements TASK-013 from RECEPTION_IMPROVEMENT_TASKS.md
    """
    try:
        # Get the current active booking detail
        booking_detail = get_object_or_404(BookingDetail, id=detail_id, is_current=True)
        booking = booking_detail.booking

        # Check if booking is in a state that allows tariff changes
        if booking.status not in ['confirmed', 'checked_in', 'in_progress']:
            messages.error(
                request,
                f'Невозможно изменить тариф для бронирования со статусом "{booking.get_status_display()}"'
            )
            return redirect('logus:booking_detail', booking_id=booking.id)

        if request.method == 'POST':
            form = TariffChangeForm(request.POST, booking_detail=booking_detail)
            if form.is_valid():
                try:
                    new_tariff = form.cleaned_data['new_tariff']
                    new_room = form.cleaned_data['new_room']
                    change_date = form.cleaned_data['change_date']
                    reason = form.cleaned_data['reason']

                    # Log the change attempt
                    logger.info(
                        f"Tariff change initiated by {request.user.username} for BookingDetail {detail_id}: "
                        f"Old: {booking_detail.tariff.name}/{booking_detail.room.name}, "
                        f"New: {new_tariff.name}/{new_room.name}, Date: {change_date}"
                    )

                    # Use the static method to create new booking detail
                    new_detail = BookingDetail.change_tariff(
                        booking=booking,
                        client=booking_detail.client,
                        new_tariff=new_tariff,
                        new_room=new_room,
                        change_datetime=change_date
                    )

                    # Set audit fields
                    new_detail.created_by = request.user
                    new_detail.modified_by = request.user
                    new_detail.save(update_fields=['created_by', 'modified_by', 'updated_at'])

                    # Add reason to booking notes
                    current_notes = booking.notes or ''
                    change_note = (
                        f"\n\n--- Изменение тарифа/комнаты {timezone.now().strftime('%d.%m.%Y %H:%M')} ---\n"
                        f"Пациент: {booking_detail.client.full_name}\n"
                        f"Старый тариф: {booking_detail.tariff.name}, Комната: {booking_detail.room.name}\n"
                        f"Новый тариф: {new_tariff.name}, Комната: {new_room.name}\n"
                        f"Вступает в силу: {change_date.strftime('%d.%m.%Y %H:%M')}\n"
                        f"Причина: {reason}\n"
                        f"Изменено: {request.user.get_full_name() or request.user.username}"
                    )
                    booking.notes = current_notes + change_note
                    booking.modified_by = request.user
                    booking.save(update_fields=['notes', 'modified_by', 'updated_at'])

                    # Log success
                    logger.info(
                        f"Tariff change completed successfully. New BookingDetail ID: {new_detail.id}"
                    )

                    messages.success(
                        request,
                        f'Тариф/комната успешно изменены для {booking_detail.client.full_name}. '
                        f'Новый тариф: {new_tariff.name}, Комната: {new_room.name}'
                    )

                    return redirect('logus:booking_detail', booking_id=booking.id)

                except Exception as e:
                    logger.error(f"Error during tariff change: {e}", exc_info=True)
                    messages.error(request, f'Ошибка при изменении тарифа: {str(e)}')
            else:
                logger.warning(f"Form validation errors: {form.errors}")
                messages.error(request, 'Пожалуйста, исправьте ошибки в форме')
        else:
            form = TariffChangeForm(booking_detail=booking_detail)

        context = {
            'form': form,
            'booking': booking,
            'booking_detail': booking_detail,
            'patient': booking_detail.client,
        }

        return render(request, 'logus/booking/booking_detail_tariff_change.html', context)

    except Exception as e:
        logger.error(f"Error in tariff_change_view: {e}", exc_info=True)
        messages.error(request, 'Произошла ошибка при загрузке формы изменения тарифа')
        return redirect('logus:booking_list')


@login_required
@require_http_methods(["GET", "POST"])
def record_service_session(request, tracking_id):
    """
    Record a service session as used for a patient.
    Implements TASK-015 from RECEPTION_IMPROVEMENT_TASKS.md

    Args:
        tracking_id: ServiceSessionTracking ID
    """
    try:
        # Get the service tracking record
        tracking = get_object_or_404(ServiceSessionTracking, id=tracking_id)
        booking_detail = tracking.booking_detail
        booking = booking_detail.booking

        # Check if booking is active
        if booking.status not in ['confirmed', 'checked_in', 'in_progress']:
            messages.error(
                request,
                f'Невозможно записать сеанс для бронирования со статусом "{booking.get_status_display()}"'
            )
            return redirect('logus:booking_detail', booking_id=booking.id)

        if request.method == 'POST':
            form = ServiceSessionRecordForm(request.POST, tracking=tracking)
            if form.is_valid():
                try:
                    session_date = form.cleaned_data['session_date']
                    notes = form.cleaned_data.get('notes', '')
                    performed_by = form.cleaned_data.get('performed_by', '')

                    # Check if session exceeds included amount
                    sessions_before = tracking.sessions_used
                    is_billable = sessions_before >= tracking.sessions_included

                    # Increment session counter
                    tracking.increment_session(is_billable=is_billable)

                    # Log the session recording
                    logger.info(
                        f"Service session recorded by {request.user.username}: "
                        f"Tracking ID {tracking_id}, Service: {tracking.service.name}, "
                        f"Patient: {booking_detail.client.full_name}, "
                        f"Session {tracking.sessions_used}/{tracking.sessions_included}, "
                        f"Billable: {is_billable}"
                    )

                    # Add note to booking
                    session_note = (
                        f"\n\n--- Сеанс записан {timezone.now().strftime('%d.%m.%Y %H:%M')} ---\n"
                        f"Пациент: {booking_detail.client.full_name}\n"
                        f"Услуга: {tracking.service.name}\n"
                        f"Дата сеанса: {session_date.strftime('%d.%m.%Y %H:%M')}\n"
                        f"Сеанс: {tracking.sessions_used} из {tracking.sessions_included} включённых\n"
                    )
                    if performed_by:
                        session_note += f"Исполнитель: {performed_by}\n"
                    if notes:
                        session_note += f"Заметки: {notes}\n"
                    if is_billable:
                        session_note += "⚠️ ДОПОЛНИТЕЛЬНАЯ ОПЛАТА: Сеанс превышает включённое количество\n"
                    session_note += f"Записано: {request.user.get_full_name() or request.user.username}"

                    current_notes = booking.notes or ''
                    booking.notes = current_notes + session_note
                    booking.modified_by = request.user
                    booking.save(update_fields=['notes', 'modified_by', 'updated_at'])

                    # If session is billable, create ServiceUsage record for billing
                    if is_billable:
                        from core.models.services import ServiceUsage

                        ServiceUsage.objects.create(
                            booking_detail=booking_detail,
                            service=tracking.service,
                            quantity=1,
                            price=tracking.service.base_price or 0,
                            date_used=session_date,
                            notes=f"Дополнительный сеанс (превышение тарифа). {notes}",
                            created_by=request.user,
                            modified_by=request.user
                        )

                        logger.info(
                            f"ServiceUsage created for billable session: "
                            f"Service {tracking.service.name}, Price {tracking.service.base_price}"
                        )

                    # Success message
                    if is_billable:
                        messages.warning(
                            request,
                            f'Сеанс записан ({tracking.sessions_used}/{tracking.sessions_included}). '
                            f'⚠️ Это дополнительный сеанс, требуется оплата: {tracking.service.base_price} сум'
                        )
                    else:
                        messages.success(
                            request,
                            f'Сеанс успешно записан для {booking_detail.client.full_name}. '
                            f'Использовано: {tracking.sessions_used}/{tracking.sessions_included}'
                        )

                    return redirect('logus:booking_detail', booking_id=booking.id)

                except Exception as e:
                    logger.error(f"Error recording service session: {e}", exc_info=True)
                    messages.error(request, f'Ошибка при записи сеанса: {str(e)}')
            else:
                logger.warning(f"Form validation errors: {form.errors}")
                messages.error(request, 'Пожалуйста, исправьте ошибки в форме')
        else:
            form = ServiceSessionRecordForm(tracking=tracking)

        context = {
            'form': form,
            'tracking': tracking,
            'booking': booking,
            'booking_detail': booking_detail,
            'patient': booking_detail.client,
            'sessions_remaining': tracking.sessions_remaining,
            'will_be_billable': tracking.sessions_used >= tracking.sessions_included,
        }

        return render(request, 'logus/booking/record_service_session.html', context)

    except Exception as e:
        logger.error(f"Error in record_service_session view: {e}", exc_info=True)
        messages.error(request, 'Произошла ошибка при загрузке формы записи сеанса')
        return redirect('logus:booking_list')