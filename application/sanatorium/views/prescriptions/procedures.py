from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.http import JsonResponse

from application.sanatorium.forms.procedures import ProcedureForm, ProcedureSessionForm
from core.models import (
    ProcedureServiceModel,
    IllnessHistory,
    IndividualProcedureSessionModel,
    Service, ServiceTypeModel
)


@login_required
def procedure_detail(request, procedure_id):
    """View for showing procedure details"""
    procedure = get_object_or_404(ProcedureServiceModel, id=procedure_id)
    history = procedure.illness_history

    # Get all sessions for this procedure
    sessions = procedure.individual_sessions.all().order_by('session_number')

    context = {
        'procedure': procedure,
        'history': history,
        'sessions': sessions,
        'active_page': {'proc_main_list_page': 'active'}
    }

    return render(request, 'sanatorium/doctors/prescriptions/procedure_detail.html', context)


@login_required
def procedure_create(request, history_id):
    """View for creating a new procedure"""
    history = get_object_or_404(IllnessHistory, id=history_id)
    service_types = ServiceTypeModel.objects.all()


    if request.method == 'POST':
        form = ProcedureForm(request.POST)
        print('here we are')
        if form.is_valid():
            procedure = form.save(commit=False)
            procedure.illness_history = history
            procedure.prescribed_by = request.user
            procedure.save()

            messages.success(request, f'Лечебная процедура "{procedure.medical_service.name}" успешно добавлена.')
            return redirect('main_prescription_list', history_id=history.id)
    else:
        print('not wanted')
        form = ProcedureForm()

    context = {
        'form': form,
        'history': history,
        'service_types': service_types,
        'action': 'Добавить',
        'active_page': {'proc_main_list_page': 'active'}

    }

    return render(request, 'sanatorium/doctors/prescriptions/procedure_form.html', context)


@login_required
def procedure_edit(request, procedure_id):
    """View for editing an existing procedure"""
    procedure = get_object_or_404(ProcedureServiceModel, id=procedure_id)
    history = procedure.illness_history

    if request.method == 'POST':
        form = ProcedureForm(request.POST, instance=procedure)
        if form.is_valid():
            old_quantity = procedure.quantity
            new_procedure = form.save()

            # Handle changes in quantity
            if new_procedure.quantity > old_quantity:
                # Create additional sessions if quantity increased
                create_additional_sessions(new_procedure, old_quantity)
            elif new_procedure.quantity < old_quantity:
                # Remove excess sessions if quantity decreased
                delete_excess_sessions(new_procedure)

            messages.success(request, f'Лечебная процедура "{new_procedure.medical_service.name}" успешно обновлена.')
            return redirect('main_prescription_list', history_id=history.id)
    else:
        form = ProcedureForm(instance=procedure)

    context = {

        'form': form,
        'procedure': procedure,
        'history': history,
        'active_page': {'proc_main_list_page': 'active'},
        'action': 'Редактировать'
    }

    return render(request, 'sanatorium/doctors/prescriptions/procedure_form.html', context)


@login_required
def procedure_delete(request, procedure_id):
    """View for deleting a procedure"""
    procedure = get_object_or_404(ProcedureServiceModel, id=procedure_id)
    history = procedure.illness_history

    if request.method == 'POST':
        procedure_name = procedure.medical_service.name
        procedure.delete()
        messages.success(request, f'Лечебная процедура "{procedure_name}" успешно удалена.')
        return redirect('main_prescription_list', history_id=history.id)

    context = {
        'procedure': procedure,
        'history': history,
        'active_page': {'proc_main_list_page': 'active'}

    }

    return render(request, 'sanatorium/doctors/prescriptions/procedure_confirm_delete.html', context)


# @login_required
# @require_POST
# def update_session_status(request, session_id):
#     """AJAX view for updating a procedure session status"""
#     session = get_object_or_404(IndividualProcedureSessionModel, id=session_id)
#
#     status = request.POST.get('status')
#     notes = request.POST.get('notes', '')
#
#     if status not in [choice[0] for choice in IndividualProcedureSessionModel.STATUS_CHOICES]:
#         return JsonResponse({
#             'success': False,
#             'message': 'Некорректный статус'
#         }, status=400)
#
#     session.status = status
#     session.notes = notes
#
#     # If marking as completed, set completed time
#     if status == 'completed':
#         from django.utils import timezone
#         session.completed_at = timezone.now()
#         session.completed_by = request.user
#
#     session.save()
#
#     # Update parent procedure progress
#     update_procedure_progress(session.assigned_procedure)
#
#     return JsonResponse({
#         'success': True,
#         'message': 'Статус сеанса успешно обновлен'
#     })

@login_required
@require_POST
def update_session_status(request, session_id):
    """AJAX view for updating a procedure session status"""
    next_url = request.POST.get('next', '')

    session = get_object_or_404(IndividualProcedureSessionModel, id=session_id)

    status = request.POST.get('status')
    notes = request.POST.get('notes', '')

    if status not in [choice[0] for choice in IndividualProcedureSessionModel.STATUS_CHOICES]:
        return JsonResponse({
            'success': False,
            'message': 'Некорректный статус'
        }, status=400)

    # Save old status to check if it changed
    old_status = session.status

    # Update session data
    session.status = status
    session.notes = notes

    # If marking as completed, set completed time
    completed_at = None
    if status == 'completed' and old_status != 'completed':
        from django.utils import timezone
        now = timezone.now()
        session.completed_at = now
        session.completed_by = request.user
        completed_at = now.strftime('%d.%m.Y %H:%M')

    # If changing from completed to another status, clear completed time
    if old_status == 'completed' and status != 'completed':
        session.completed_at = None
        session.completed_by = None

    session.save()

    # Update parent procedure progress
    procedure = session.assigned_procedure
    update_procedure_progress(procedure)

    if next_url:
        return redirect(next_url)

    url = reverse(
        'prescription_list',
        kwargs={'history_id': procedure.illness_history.pk}  # →  "prescription_urls/1"
    )

    return redirect(f"{url}#procedures")


@login_required
def get_services_by_type(request):
    """AJAX endpoint to get services filtered by type"""
    service_type_id = request.GET.get('service_type_id')

    try:
        service_type = ServiceTypeModel.objects.get(id=service_type_id)
    except ServiceTypeModel.DoesNotExist:
        return []
    services = list(service_type.services.all().values_list('id', 'name'))
    return JsonResponse(services, safe=False)


def load_services(request):
    service_type_id = request.GET.get('service_type_id')
    services = Service.objects.filter(type__id=service_type_id)
    return render(request, 'sanatorium/doctors/prescriptions/services_dropdown_list_options.html', {'services': services})


# Helper functions
def create_procedure_sessions(procedure):
    """Create individual sessions for a procedure based on quantity"""
    for i in range(1, procedure.quantity + 1):
        IndividualProcedureSessionModel.objects.create(
            assigned_procedure=procedure,
            session_number=i,
            status='pending'
        )


def create_additional_sessions(procedure, old_quantity):
    """Create additional sessions when quantity is increased"""
    for i in range(old_quantity + 1, procedure.quantity + 1):
        IndividualProcedureSessionModel.objects.create(
            procedure=procedure,
            session_number=i,
            status='pending'
        )


def delete_excess_sessions(procedure):
    """Delete excess sessions when quantity is decreased"""
    excess_sessions = procedure.individual_sessions.filter(
        session_number__gt=procedure.quantity
    )
    excess_sessions.delete()


def update_procedure_progress(procedure):
    """Update the procedure progress based on completed sessions"""
    completed_count = procedure.individual_sessions.filter(status='completed').count()

    # Update procedure state based on completed sessions
    total_sessions = procedure.quantity

    if completed_count == 0:
        procedure.state = 'pending'
    elif completed_count < total_sessions:
        procedure.state = 'in_progress'
    else:
        procedure.state = 'completed'

    procedure.proceeded_sessions = completed_count
    procedure.save()


