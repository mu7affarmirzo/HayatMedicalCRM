from django.http import JsonResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta
from django.db.models import Q
from django.utils.dateparse import parse_datetime

from core.models import ProcedureServiceModel, IndividualProcedureSessionModel, Account


@login_required
def calendar_view(request):
    """
    Calendar view for visualizing all scheduled sessions
    """
    # Get all therapists for filter
    therapists = Account.objects.filter(is_therapist=True).order_by('f_name')

    # Get statistics for the current week
    today = timezone.now().date()
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)

    # Sessions statistics for the current week
    pending_sessions_week = IndividualProcedureSessionModel.objects.filter(
        status='pending',
        scheduled_to__date__range=[week_start, week_end]
    ).count()

    completed_sessions_week = IndividualProcedureSessionModel.objects.filter(
        status='completed',
        completed_at__date__range=[week_start, week_end]
    ).count()

    cancelled_sessions_week = IndividualProcedureSessionModel.objects.filter(
        status='canceled',
        scheduled_to__date__range=[week_start, week_end]
    ).count()

    # Calculate occupancy percentage (assuming 10 hours per day, 5 days a week, 2 therapists)
    max_sessions_capacity = 10 * 5 * 2  # 10 hours, 5 days, 2 therapists (example)
    total_sessions_week = pending_sessions_week + completed_sessions_week
    occupancy_percentage = int((total_sessions_week / max_sessions_capacity) * 100) if max_sessions_capacity > 0 else 0
    occupancy_percentage = min(occupancy_percentage, 100)  # Cap at 100%

    context = {
        'therapists': therapists,
        'pending_sessions_week': pending_sessions_week,
        'completed_sessions_week': completed_sessions_week,
        'cancelled_sessions_week': cancelled_sessions_week,
        'occupancy_percentage': occupancy_percentage,
    }

    return render(request, 'sanatorium/massagists/dispatcher/calendar_view.html', context)


@login_required
def calendar_events(request):
    """
    AJAX endpoint for getting calendar events
    """
    # Parse date range from request
    start_date = request.GET.get('start')
    end_date = request.GET.get('end')

    # Parse filters
    status_filters = request.GET.get('status', '').split(',')
    therapist_id = request.GET.get('therapist')

    # Base query
    sessions = IndividualProcedureSessionModel.objects.select_related(
        'assigned_procedure__illness_history__patient',
        'assigned_procedure__medical_service',
        'therapist'
    )

    # Apply date range filter
    if start_date and end_date:
        sessions = sessions.filter(scheduled_to__range=[start_date, end_date])

    # Apply status filter
    if status_filters and status_filters[0]:
        sessions = sessions.filter(status__in=status_filters)

    # Apply therapist filter
    if therapist_id:
        sessions = sessions.filter(therapist_id=therapist_id)

    # Prepare events for FullCalendar
    events = []
    for session in sessions:
        procedure = session.assigned_procedure
        patient = procedure.illness_history.patient

        # Prepare scheduled and completed times
        scheduled_time = session.scheduled_to.strftime('%d.%m.%Y %H:%M') if session.scheduled_to else None
        completed_time = session.completed_at.strftime('%d.%m.%Y %H:%M') if session.completed_at else None

        # Calculate session end time (default to 30 minutes if not specified)
        session_start = session.scheduled_to
        session_end = session_start + timedelta(
            minutes=procedure.medical_service.duration_minutes or 30) if session_start else None

        # Prepare event title
        title = f"{patient.full_name} - {procedure.medical_service.name} #{session.session_number}"

        # Create event object
        event = {
            'id': session.id,
            'title': title,
            'start': session_start.isoformat() if session_start else None,
            'end': session_end.isoformat() if session_end else None,
            'status': session.status,
            'session_number': session.session_number,
            'procedure_id': procedure.id,
            'service_name': procedure.medical_service.name,
            'patient_name': patient.full_name,
            'illness_history': procedure.illness_history.series_number,
            'therapist_name': session.therapist.full_name if session.therapist else None,
            'scheduled': scheduled_time,
            'completed': completed_time,
            'notes': session.notes
        }

        events.append(event)

    return JsonResponse({'events': events})


@login_required
def procedures_calendar_view(request):
    """
    Calendar view for visualizing procedures and sessions
    """
    # Get all therapists for filter dropdown
    therapists = Account.objects.filter(is_therapist=True).order_by('f_name')

    context = {
        'therapists': therapists,
    }

    return render(request, 'sanatorium/massagists/dispatcher/procedures_calendar.html', context)


@login_required
def procedures_calendar_events(request):
    """
    AJAX endpoint for getting calendar events (procedures and sessions)
    """
    try:
        # Parse date range from request - handle ISO 8601 format
        start_str = request.GET.get('start')
        end_str = request.GET.get('end')

        # Parse ISO 8601 dates to datetime objects
        if start_str:
            start_date = parse_datetime(start_str)
            # Extract just the date part
            start_date_only = start_date.date() if start_date else None
        else:
            start_date = None
            start_date_only = None

        if end_str:
            end_date = parse_datetime(end_str)
            # Extract just the date part
            end_date_only = end_date.date() if end_date else None
        else:
            end_date = None
            end_date_only = None

        # Parse filter values
        procedure_states = request.GET.get('procedure_states', '').split(',')
        session_statuses = request.GET.get('session_statuses', '').split(',')

        # Check which types of events to show
        show_procedures = request.GET.get('show_procedures') == '1'
        show_sessions = request.GET.get('show_sessions') == '1'

        procedures = []
        sessions = []

        # Get procedures if requested
        if show_procedures and start_date_only and end_date_only:
            procedures_query = ProcedureServiceModel.objects.select_related(
                'illness_history__patient', 'medical_service', 'therapist'
            ).prefetch_related('individual_sessions')

            print(procedures_query, '-------')

            # Apply date range filter - procedures should overlap with calendar range
            procedures_query = procedures_query.filter(
                Q(start_date__range=[start_date_only, end_date_only]) |
                Q(start_date__lte=start_date_only, illness_history__booking__end_date__gte=start_date_only)
            )

            # # Apply state filter if provided
            # if procedure_states and procedure_states[0]:
            #     procedures_query = procedures_query.filter(state__in=procedure_states)

            # Map state values to display names
            state_displays = dict(ProcedureServiceModel.STATE_CHOICES)

            # Process each procedure into a format suitable for FullCalendar
            for procedure in procedures_query:
                # Get end date from the booking or add a default duration
                if procedure.illness_history.booking and procedure.illness_history.booking.end_date:
                    end_date = procedure.illness_history.booking.end_date
                else:
                    # If no booking end date, use start_date + some default duration (e.g., 7 days)
                    end_date = procedure.start_date + timedelta(days=7)

                # Format procedure for calendar
                procedure_event = {
                    'id': procedure.id,
                    'title': f"{procedure.illness_history.patient.full_name} - {procedure.medical_service.name}",
                    'start': procedure.start_date.isoformat(),
                    'end': end_date.isoformat(),
                    'state': procedure.state,
                    'state_display': state_displays.get(procedure.state, procedure.state),
                    'service_name': procedure.medical_service.name,
                    'patient_name': procedure.illness_history.patient.full_name,
                    'therapist_name': procedure.therapist.full_name if procedure.therapist else None,
                    'start_date': procedure.start_date.strftime('%d.%m.%Y'),
                    'frequency': procedure.frequency,
                    'quantity': procedure.quantity,
                    'proceeded_sessions': procedure.proceeded_sessions,
                    'progress_percentile': procedure.progres_percentile,
                    'comments': procedure.comments,
                    'sessions': []
                }

                # Include individual sessions
                for session in procedure.individual_sessions.all():
                    session_data = {
                        'id': session.id,
                        'session_number': session.session_number,
                        'status': session.status,
                        'therapist_name': session.therapist.full_name if session.therapist else None,
                        'scheduled_to': session.scheduled_to.strftime(
                            '%d.%m.%Y %H:%M') if session.scheduled_to else None,
                        'completed_at': session.completed_at.strftime(
                            '%d.%m.%Y %H:%M') if session.completed_at else None,
                        'notes': session.notes
                    }
                    procedure_event['sessions'].append(session_data)

                procedures.append(procedure_event)

        # Get individual sessions if requested
        if show_sessions and start_date and end_date:
            sessions_query = IndividualProcedureSessionModel.objects.select_related(
                'assigned_procedure__illness_history__patient',
                'assigned_procedure__medical_service',
                'therapist'
            )

            # Apply date range filter - use datetime objects for datetime fields
            sessions_query = sessions_query.filter(
                Q(scheduled_to__range=[start_date, end_date]) |
                Q(completed_at__range=[start_date, end_date])
            )

            # Apply status filter if provided
            if session_statuses and session_statuses[0]:
                sessions_query = sessions_query.filter(status__in=session_statuses)

            # Process each session into a format suitable for FullCalendar
            for session in sessions_query:
                procedure = session.assigned_procedure

                # Determine start and end times
                if session.scheduled_to:
                    session_start = session.scheduled_to
                    # Default session duration is 30 minutes if not specified in medical service
                    duration_minutes = procedure.medical_service.duration_minutes or 30
                    session_end = session_start + timedelta(minutes=duration_minutes)
                elif session.completed_at:
                    session_start = session.completed_at
                    duration_minutes = procedure.medical_service.duration_minutes or 30
                    session_end = session_start + timedelta(minutes=duration_minutes)
                else:
                    # Skip sessions without a scheduled or completed time
                    continue

                # Format session for calendar
                session_event = {
                    'id': session.id,
                    'title': f"{procedure.illness_history.patient.full_name} - {procedure.medical_service.name} #{session.session_number}",
                    'start': session_start.isoformat(),
                    'end': session_end.isoformat(),
                    'status': session.status,
                    'service_name': procedure.medical_service.name,
                    'patient_name': procedure.illness_history.patient.full_name,
                    'session_number': session.session_number,
                    'therapist_name': session.therapist.full_name if session.therapist else None,
                    'scheduled_to': session.scheduled_to.strftime('%d.%m.%Y %H:%M') if session.scheduled_to else None,
                    'completed_at': session.completed_at.strftime('%d.%m.%Y %H:%M') if session.completed_at else None,
                    'notes': session.notes,
                    'procedure_id': procedure.id
                }

                sessions.append(session_event)
        return JsonResponse({
            'procedures': procedures,
            'sessions': sessions
        })

    except Exception as e:
        # Return error info for debugging
        import traceback
        return JsonResponse({
            'error': str(e),
            'traceback': traceback.format_exc()
        }, status=500)
