# Additional views for AJAX actions
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.template.loader import render_to_string
from django.views.decorators.http import require_POST

from core.models import IndividualProcedureSessionModel, ProcedureServiceModel


@login_required
@require_POST
def complete_session(request, session_id):
    """Mark a session as completed"""
    session = get_object_or_404(IndividualProcedureSessionModel, id=session_id)

    # Security check: ensure the nurse is authorized to complete this session
    if session.therapist != request.user and session.assigned_procedure.therapist != request.user:
        return JsonResponse({'status': 'error', 'message': 'Недостаточно прав для выполнения этого действия'},
                            status=403)

    # Update the session
    session.status = 'completed'
    session.therapist = request.user  # Assign the nurse who completed the session
    session.completed_at = timezone.now()
    session.save()

    # Update the procedure's proceeded_sessions count
    procedure = session.assigned_procedure
    procedure.proceeded_sessions = procedure.individual_sessions.filter(status='completed').count()
    procedure.save()

    return JsonResponse({
        'status': 'success',
        'message': 'Сеанс успешно завершен',
        'session': {
            'id': session.id,
            'status': session.status,
            'status_display': session.get_status_display(),
            'completed_at': session.completed_at.strftime('%d.%m.%Y %H:%M') if session.completed_at else None,
        }
    })


@login_required
@require_POST
def cancel_session(request, session_id):
    """Cancel a session"""
    session = get_object_or_404(IndividualProcedureSessionModel, id=session_id)

    # Security check: ensure the nurse is authorized to cancel this session
    if session.therapist != request.user and session.assigned_procedure.therapist != request.user:
        return JsonResponse({'status': 'error', 'message': 'Недостаточно прав для выполнения этого действия'},
                            status=403)

    # Can only cancel pending sessions
    if session.status != 'pending':
        return JsonResponse({'status': 'error', 'message': 'Можно отменить только ожидающие сеансы'}, status=400)

    # Update the session
    session.status = 'canceled'
    session.save()

    return JsonResponse({
        'status': 'success',
        'message': 'Сеанс успешно отменен',
        'session': {
            'id': session.id,
            'status': session.status,
            'status_display': session.get_status_display(),
        }
    })


@login_required
def get_session_details(request, session_id):
    """Get detailed information about a session"""
    session = get_object_or_404(IndividualProcedureSessionModel, id=session_id)

    # Security check: ensure the nurse can view this session
    if session.therapist != request.user and session.assigned_procedure.therapist != request.user:
        return JsonResponse({'status': 'error', 'message': 'Недостаточно прав для просмотра этого сеанса'}, status=403)

    context = {
        'session': session,
        'patient_name': session.assigned_procedure.illness_history.series_number,
        # This should be replaced with actual patient name
        'procedure_name': session.assigned_procedure.medical_service.name,
        'is_completed': session.status == 'completed',
        'is_canceled': session.status == 'canceled',
        'can_complete': session.status == 'pending',
        'can_cancel': session.status == 'pending',
    }

    html = render_to_string('sanatorium/massagists/partials/session_detail.html', context)

    return JsonResponse({
        'status': 'success',
        'html': html,
        'session': {
            'id': session.id,
            'status': session.status,
            'status_display': session.get_status_display(),
            'session_number': session.session_number,
            'completed_at': session.completed_at.strftime('%d.%m.%Y %H:%M') if session.completed_at else None,
            'notes': session.notes,
        }
    })


@login_required
def get_procedure_details(request, procedure_id):
    """Get detailed information about a procedure"""
    procedure = get_object_or_404(ProcedureServiceModel, id=procedure_id)

    # Security check: ensure the nurse can view this procedure
    if procedure.therapist != request.user:
        return JsonResponse({'status': 'error', 'message': 'Недостаточно прав для просмотра этой процедуры'},
                            status=403)

    # Get all sessions for this procedure
    sessions = procedure.individual_sessions.all().order_by('session_number')

    context = {
        'procedure': procedure,
        'patient_name': procedure.illness_history.series_number,  # This should be replaced with actual patient name
        'service_name': procedure.medical_service.name,
        'sessions': sessions,
        'completed_sessions': sessions.filter(status='completed').count(),
        'pending_sessions': sessions.filter(status='pending').count(),
        'canceled_sessions': sessions.filter(status='canceled').count(),
    }

    html = render_to_string('sanatorium/massagists/partials/procedure_detail.html', context)

    return JsonResponse({
        'status': 'success',
        'html': html,
    })