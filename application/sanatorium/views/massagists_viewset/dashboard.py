# views.py
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.utils import timezone

from core.models import ProcedureServiceModel, IndividualProcedureSessionModel


@login_required
def massagist_dashboard(request):
    """
    Dashboard view for nurses showing assigned procedures and individual sessions
    """
    # Get the current nurse (assuming request.user is the nurse's Account)
    nurse = request.user

    # Get all procedures assigned to this nurse
    assigned_procedures = ProcedureServiceModel.objects.filter(
        therapist=nurse
    ).select_related('illness_history', 'medical_service')

    # Get all individual sessions for this therapist (both from directly assigned sessions
    # and from procedures where they are the assigned therapist)
    today = timezone.now().date()

    # Direct sessions (where nurse is explicitly assigned to the session)
    direct_sessions = IndividualProcedureSessionModel.objects.filter(
        therapist=nurse
    ).select_related('assigned_procedure',
                     'assigned_procedure__illness_history',
                     'assigned_procedure__medical_service')

    # Procedure-based sessions (where nurse is assigned to the procedure)
    procedure_sessions = IndividualProcedureSessionModel.objects.filter(
        assigned_procedure__therapist=nurse,
        therapist__isnull=True  # No specific therapist assigned to the session yet
    ).select_related('assigned_procedure',
                     'assigned_procedure__illness_history',
                     'assigned_procedure__medical_service')

    # Combine both querysets
    all_sessions = direct_sessions | procedure_sessions

    # Get sessions for today
    today_sessions = all_sessions.filter(
        Q(scheduled_to__date=today)).order_by('session_number')

    # Get pending sessions (not completed, not cancelled)
    pending_sessions = all_sessions.filter(status='pending')

    # Stats for the dashboard
    stats = {
        'total_procedures': assigned_procedures.count(),
        'active_procedures': assigned_procedures.filter(state='assigned').count(),
        'completed_sessions': all_sessions.filter(status='completed').count(),
        'pending_sessions': pending_sessions.count(),
        'today_sessions': today_sessions.count(),
    }

    context = {
        'nurse': nurse,
        'assigned_procedures': assigned_procedures,
        'today_sessions': today_sessions,
        'pending_sessions': pending_sessions.order_by('assigned_procedure__start_date', 'session_number'),
        'stats': stats,
    }

    return render(request, 'sanatorium/massagists/massagists_dashboard.html', context)
