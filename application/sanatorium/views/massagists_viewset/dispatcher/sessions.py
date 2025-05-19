# Additional views for AJAX actions
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.template.loader import render_to_string
from django.views.decorators.http import require_POST

from core.models import IndividualProcedureSessionModel, ProcedureServiceModel, Account

from django.shortcuts import render, redirect
from django.views import View
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin


class DispatcherDashboardView(LoginRequiredMixin, View):
    template_name = 'sanatorium/massagists/dispatcher/sessions_list.html'

    def get(self, request):
        # Get today's date
        today = timezone.now().date()

        # Get all sessions scheduled for today
        today_sessions = IndividualProcedureSessionModel.objects.filter(
            scheduled_to__date=today
        ).select_related(
            'assigned_procedure',
            'assigned_procedure__illness_history',
            'assigned_procedure__illness_history__patient',
            'assigned_procedure__medical_service',
            'therapist'
        ).order_by(
            # Order by patient name first
            'assigned_procedure__illness_history__patient__l_name',
            'assigned_procedure__illness_history__patient__f_name',
            # Then by ID
            'id',
            # Then by medical service
            'assigned_procedure__medical_service__name'
        )

        # Get all available therapists for the form dropdown
        therapists = Account.objects.filter(is_therapist=True, is_active=True).order_by('l_name', 'f_name')

        context = {
            'today_sessions': today_sessions,
            'therapists': therapists,
            'today': today,
        }

        return render(request, self.template_name, context)

    def post(self, request):
        # Process form submission for assigning therapists
        session_id = request.POST.get('session_id')
        therapist_id = request.POST.get('therapist_id')

        if session_id and therapist_id:
            try:
                session = IndividualProcedureSessionModel.objects.get(id=session_id)
                therapist = Account.objects.get(id=therapist_id)

                # Assign the therapist to the session
                session.therapist = therapist
                session.save(update_fields=['therapist', 'modified_at', 'modified_by'])

                messages.success(request,
                                 f"Терапист {therapist.full_name} успешно назначен на сеанс #{session.session_number}")
            except IndividualProcedureSessionModel.DoesNotExist:
                messages.error(request, "Сеанс не найден")
            except Account.DoesNotExist:
                messages.error(request, "Терапист не найден")
        else:
            messages.error(request, "Неверные данные формы")

        return redirect('massagist:dispatcher_sessions_list')


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

    html = render_to_string('sanatorium/massagists/dispatcher/partials/session_detail.html', context)

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

    html = render_to_string('sanatorium/massagists/dispatcher/partials/procedure_detail.html', context)

    return JsonResponse({
        'status': 'success',
        'html': html,
    })