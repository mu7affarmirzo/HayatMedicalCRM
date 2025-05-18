from django.http import JsonResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta
from core.models import IndividualProcedureSessionModel, Account


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