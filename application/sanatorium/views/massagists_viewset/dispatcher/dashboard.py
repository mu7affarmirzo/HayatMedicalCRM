from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q, Count
from django.core.paginator import Paginator

from core.models import ProcedureServiceModel, IndividualProcedureSessionModel, Account, Service


@login_required
def dispatcher_dashboard(request):
    """
    Main dispatcher dashboard view
    """
    # Get filter parameters
    state = request.GET.get('state')
    therapist_id = request.GET.get('therapist')
    service_id = request.GET.get('service')
    start_date = request.GET.get('start_date')

    # Base query
    procedures = ProcedureServiceModel.objects.all().select_related(
        'illness_history__patient', 'medical_service', 'therapist'
    ).prefetch_related('individual_sessions')

    # Apply filters
    if state:
        procedures = procedures.filter(state=state)

    if therapist_id:
        procedures = procedures.filter(therapist_id=therapist_id)

    if service_id:
        procedures = procedures.filter(medical_service_id=service_id)

    if start_date:
        try:
            date_obj = timezone.datetime.strptime(start_date, '%d.%m.%Y').date()
            procedures = procedures.filter(start_date=date_obj)
        except ValueError:
            # Invalid date format, ignore this filter
            pass

    # Order by start date (newest first)
    procedures = procedures.order_by('-start_date')

    # Pagination
    paginator = Paginator(procedures, 10)  # Show 10 procedures per page
    page = request.GET.get('page')
    procedures = paginator.get_page(page)

    # Get statistics for dashboard
    total_procedures = ProcedureServiceModel.objects.count()
    completed_sessions = IndividualProcedureSessionModel.objects.filter(status='completed').count()
    pending_sessions = IndividualProcedureSessionModel.objects.filter(status='pending').count()
    cancelled_sessions = IndividualProcedureSessionModel.objects.filter(status='canceled').count()

    # Get lists for filter dropdowns
    therapists = Account.objects.filter(is_therapist=True).order_by('f_name')
    services = Service.objects.filter(is_active=True).order_by('name')

    context = {
        'procedures': procedures,
        'total_procedures': total_procedures,
        'completed_sessions': completed_sessions,
        'pending_sessions': pending_sessions,
        'cancelled_sessions': cancelled_sessions,
        'therapists': therapists,
        'services': services,
    }

    return render(request, 'sanatorium/massagists/dispatcher/massagists_dashboard.html', context)


@login_required
def procedure_detail(request, procedure_id):
    """
    View for detailed information about a procedure
    """
    procedure = get_object_or_404(
        ProcedureServiceModel.objects.select_related(
            'illness_history__patient', 'medical_service', 'therapist'
        ).prefetch_related('individual_sessions'),
        id=procedure_id
    )

    # Get all sessions for this procedure
    sessions = procedure.individual_sessions.all().order_by('session_number')

    context = {
        'procedure': procedure,
        'sessions': sessions,
        'therapists': Account.objects.filter(is_therapist=True).order_by('f_name'),
    }

    return render(request, 'sanatorium/massagists/dispatcher/procedure_detail.html', context)


@login_required
def procedure_edit(request, procedure_id):
    """
    View for editing a procedure
    """
    procedure = get_object_or_404(ProcedureServiceModel, id=procedure_id)

    if request.method == 'POST':
        # Update procedure data
        procedure.state = request.POST.get('state')

        therapist_id = request.POST.get('therapist')
        if therapist_id:
            procedure.therapist_id = therapist_id
        else:
            procedure.therapist = None

        procedure.quantity = int(request.POST.get('quantity', procedure.quantity))
        procedure.start_date = request.POST.get('start_date')
        procedure.frequency = request.POST.get('frequency')
        procedure.comments = request.POST.get('comments')

        procedure.save()

        messages.success(request, f'Процедура #{procedure.id} успешно обновлена')
        return redirect('procedure_detail', procedure_id=procedure.id)

    context = {
        'procedure': procedure,
        'therapists': Account.objects.filter(is_therapist=True).order_by('f_name'),
        'state_choices': ProcedureServiceModel.STATE_CHOICES,
        'frequency_choices': ProcedureServiceModel.FREQUENCY_CHOICES,
    }

    return render(request, 'sanatorium/massagists/dispatcher/procedure_edit.html', context)


@login_required
def schedule_sessions(request):
    """
    View for scheduling sessions for a procedure
    """
    if request.method == 'POST':
        procedure_id = request.POST.get('procedure_id')
        therapist_id = request.POST.get('therapist')
        schedule_mode = request.POST.get('schedule_mode')

        procedure = get_object_or_404(ProcedureServiceModel, id=procedure_id)
        therapist = get_object_or_404(Account, id=therapist_id) if therapist_id else None

        # Update the procedure therapist if provided
        if therapist:
            procedure.therapist = therapist
            procedure.save()

        if schedule_mode == 'auto':
            # Automatic scheduling
            try:
                auto_start_date = request.POST.get('auto_start_date')
                auto_start_time = request.POST.get('auto_start_time')

                # Parse date and time
                start_datetime = timezone.datetime.strptime(
                    f"{auto_start_date} {auto_start_time}",
                    '%d.%m.%Y %H:%M'
                )

                # Make timezone aware
                if timezone.is_naive(start_datetime):
                    start_datetime = timezone.make_aware(start_datetime)

                # Generate session dates based on frequency
                remaining_sessions = procedure.quantity - procedure.proceeded_sessions

                if remaining_sessions > 0:
                    # Calculate interval days based on frequency
                    if procedure.frequency == 'каждый день':
                        interval_days = 1
                    elif procedure.frequency == 'через день':
                        interval_days = 2
                    else:
                        interval_days = 1  # Default to daily

                    # Create sessions
                    for i in range(remaining_sessions):
                        session_datetime = start_datetime + timezone.timedelta(days=i * interval_days)

                        # Skip if the session would be outside booking dates
                        if procedure._is_out_of_graphic(session_datetime):
                            continue

                        # Check if the same session number already exists
                        session_number = procedure.proceeded_sessions + i + 1
                        existing_session = IndividualProcedureSessionModel.objects.filter(
                            assigned_procedure=procedure,
                            session_number=session_number
                        ).first()

                        if existing_session:
                            # Update existing session
                            existing_session.therapist = therapist
                            existing_session.scheduled_to = session_datetime
                            existing_session.save()
                        else:
                            # Create new session
                            IndividualProcedureSessionModel.objects.create(
                                assigned_procedure=procedure,
                                session_number=session_number,
                                therapist=therapist,
                                scheduled_to=session_datetime,
                                status='pending'
                            )

                messages.success(request,
                                 f'Автоматическое планирование для процедуры #{procedure.id} выполнено успешно')

            except Exception as e:
                messages.error(request, f'Ошибка при планировании: {str(e)}')

        else:
            # Manual scheduling
            session_numbers = request.POST.getlist('session_number[]')
            session_datetimes = request.POST.getlist('session_datetime[]')

            if len(session_numbers) == len(session_datetimes):
                for i in range(len(session_numbers)):
                    try:
                        session_number = int(session_numbers[i])
                        session_datetime = timezone.datetime.strptime(
                            session_datetimes[i], '%d.%m.%Y %H:%M'
                        )

                        # Make timezone aware
                        if timezone.is_naive(session_datetime):
                            session_datetime = timezone.make_aware(session_datetime)

                        # Skip if the session would be outside booking dates
                        if procedure._is_out_of_graphic(session_datetime):
                            continue

                        # Check if the same session number already exists
                        existing_session = IndividualProcedureSessionModel.objects.filter(
                            assigned_procedure=procedure,
                            session_number=session_number
                        ).first()

                        if existing_session:
                            # Update existing session
                            existing_session.therapist = therapist
                            existing_session.scheduled_to = session_datetime
                            existing_session.save()
                        else:
                            # Create new session
                            IndividualProcedureSessionModel.objects.create(
                                assigned_procedure=procedure,
                                session_number=session_number,
                                therapist=therapist,
                                scheduled_to=session_datetime,
                                status='pending'
                            )

                    except Exception as e:
                        messages.error(request, f'Ошибка при планировании сеанса #{session_number}: {str(e)}')

                messages.success(request, f'Ручное планирование для процедуры #{procedure.id} выполнено успешно')
            else:
                messages.error(request, 'Ошибка в данных сеансов')

        return redirect('procedure_detail', procedure_id=procedure.id)

    # If not POST, redirect to dashboard
    return redirect('dispatcher_dashboard')


@login_required
def add_session(request):
    """
    Add a new individual session to a procedure
    """
    if request.method == 'POST':
        procedure_id = request.POST.get('procedure_id')
        session_number = request.POST.get('session_number')
        therapist_id = request.POST.get('therapist')
        scheduled_to = request.POST.get('scheduled_to')
        notes = request.POST.get('notes')

        procedure = get_object_or_404(ProcedureServiceModel, id=procedure_id)

        try:
            # Create new session
            session = IndividualProcedureSessionModel(
                assigned_procedure=procedure,
                session_number=int(session_number),
                status='pending',
                notes=notes
            )

            # Set therapist if provided
            if therapist_id:
                session.therapist = get_object_or_404(Account, id=therapist_id)

            # Set scheduled datetime if provided
            if scheduled_to:
                scheduled_datetime = timezone.datetime.strptime(scheduled_to, '%d.%m.%Y %H:%M')
                if timezone.is_naive(scheduled_datetime):
                    scheduled_datetime = timezone.make_aware(scheduled_datetime)
                session.scheduled_to = scheduled_datetime

            session.save()
            messages.success(request, f'Сеанс #{session_number} успешно добавлен')

        except Exception as e:
            messages.error(request, f'Ошибка при добавлении сеанса: {str(e)}')

        return redirect('procedure_detail', procedure_id=procedure.id)

    # If not POST, redirect to dashboard
    return redirect('dispatcher_dashboard')


@login_required
def complete_session(request):
    """
    Mark a session as completed
    """
    if request.method == 'POST':
        session_id = request.POST.get('session_id')
        completed_at = request.POST.get('completed_at')
        notes = request.POST.get('notes')

        session = get_object_or_404(IndividualProcedureSessionModel, id=session_id)

        try:
            # Parse completed datetime
            completed_datetime = timezone.datetime.strptime(completed_at, '%d.%m.%Y %H:%M')
            if timezone.is_naive(completed_datetime):
                completed_datetime = timezone.make_aware(completed_datetime)

            # Update session
            session.status = 'completed'
            session.completed_at = completed_datetime
            if notes:
                session.notes = notes
            session.save()

            # Update procedure progress
            procedure = session.assigned_procedure
            procedure.proceeded_sessions += 1
            procedure.save()

            messages.success(request, f'Сеанс #{session.session_number} отмечен как проведенный')

        except Exception as e:
            messages.error(request, f'Ошибка при отметке сеанса: {str(e)}')

        return redirect('procedure_detail', procedure_id=session.assigned_procedure.id)

    # If not POST, redirect to dashboard
    return redirect('dispatcher_dashboard')


@login_required
def cancel_session(request):
    """
    Cancel a session
    """
    if request.method == 'POST':
        session_id = request.POST.get('session_id')
        cancel_reason = request.POST.get('cancel_reason')

        session = get_object_or_404(IndividualProcedureSessionModel, id=session_id)

        try:
            # Update session
            session.status = 'canceled'
            session.notes = f"Отменено: {cancel_reason}"
            session.save()

            messages.success(request, f'Сеанс #{session.session_number} отменен')

        except Exception as e:
            messages.error(request, f'Ошибка при отмене сеанса: {str(e)}')

        return redirect('procedure_detail', procedure_id=session.assigned_procedure.id)

    # If not POST, redirect to dashboard
    return redirect('dispatcher_dashboard')
