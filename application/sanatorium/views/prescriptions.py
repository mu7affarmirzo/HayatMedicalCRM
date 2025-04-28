# views.py
from datetime import datetime

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from core.models import IllnessHistory, MedicalServiceModel, ProcedureServiceModel


# @login_required
# def main_prescription_list_view(request, history_id):
#     """
#     View for the main prescription list (Основной лист назначений)
#     Shows consultations, procedures, and medications
#     """
#     # Get the illness history
#     history = get_object_or_404(IllnessHistory, id=history_id)
#     print(history)
#
#     # Get all medical services (consultations & examinations)
#     consultations = MedicalServiceModel.objects.filter(
#         illness_history=history
#     ).select_related('medical_service', 'consulted_doctor')
#
#     # Get all procedures
#     procedures = ProcedureServiceModel.objects.filter(
#         illness_history=history
#     ).select_related('medical_service', 'therapist')
#
#     # Get all medications (assuming a MedicationModel exists)
#     try:
#         # medications = MedicationModel.objects.filter(illness_history=history)
#         medications = []
#     except:
#         # If the model doesn't exist, provide an empty list
#         medications = []
#
#     # Set active page for sidebar
#     active_page = {
#         'proc_main_list_page': 'active',
#     }
#
#     context = {
#         'history': history,
#         'consultations': consultations,
#         'procedures': procedures,
#         'medications': medications,
#         'consultation_count': consultations.count(),
#         'procedure_count': procedures.count(),
#         'medication_count': len(medications) if medications else 0,
#         'active_page': active_page,
#     }
#
#     return render(request, 'sanatorium/doctors/prescriptions/main_prescription_list.html', context)


@login_required
def main_prescription_list_view(request, history_id):
    """
    View for the main prescription list (Основной лист назначений)
    Shows consultations, procedures, and medications
    """
    # Get the illness history
    history = get_object_or_404(IllnessHistory, id=history_id)

    # Get all medical services (consultations & examinations)
    consultations = MedicalServiceModel.objects.filter(
        illness_history=history
    ).select_related('medical_service', 'consulted_doctor')

    # Get all procedures
    procedures = ProcedureServiceModel.objects.filter(
        illness_history=history
    ).select_related('medical_service', 'therapist').prefetch_related('individual_sessions')

    # Get all medications (assuming a MedicationModel exists)
    try:
        # medications = MedicationModel.objects.filter(illness_history=history)
        medications = []
    except:
        # If the model doesn't exist, provide an empty list
        medications = []

    # Calculate consultation statistics
    consultation_count = consultations.count()
    completed_consultations = consultations.filter(state='dispatched').count()
    completed_consultations_percent = 0
    if consultation_count > 0:
        completed_consultations_percent = (completed_consultations / consultation_count) * 100

    # Calculate procedure statistics
    procedure_count = procedures.count()
    total_sessions = 0
    total_completed_sessions = 0

    for procedure in procedures:
        total_sessions += procedure.quantity
        total_completed_sessions += procedure.proceeded_sessions

    total_procedures_percent = 0
    if total_sessions > 0:
        total_procedures_percent = (total_completed_sessions / total_sessions) * 100

    # Calculate medication statistics
    medication_count = len(medications)
    active_medications = 0

    for med in medications:
        if med.state == 'assigned':
            active_medications += 1

            # Calculate progress percentage for each medication
            if hasattr(med, 'start_date') and hasattr(med, 'end_date'):
                today = datetime.now().date()
                total_days = (med.end_date - med.start_date).days
                days_elapsed = (today - med.start_date).days

                if total_days > 0:
                    med.progress_percent = min(100, max(0, (days_elapsed / total_days) * 100))
                else:
                    med.progress_percent = 0

                med.total_days = total_days
                med.days_elapsed = days_elapsed

    active_medications_percent = 0
    if medication_count > 0:
        active_medications_percent = (active_medications / medication_count) * 100

    # Set active page for sidebar
    active_page = {
        'proc_main_list_page': 'active',
    }

    context = {
        'history': history,
        'consultations': consultations,
        'procedures': procedures,
        'medications': medications,
        'consultation_count': consultation_count,
        'procedure_count': procedure_count,
        'medication_count': medication_count,
        'completed_consultations': completed_consultations,
        'completed_consultations_percent': completed_consultations_percent,
        'total_sessions': total_sessions,
        'total_completed_sessions': total_completed_sessions,
        'total_procedures_percent': total_procedures_percent,
        'active_medications': active_medications,
        'active_medications_percent': active_medications_percent,
        'active_page': active_page,
    }

    return render(request, 'sanatorium/doctors/prescriptions/main_prescription_list.html', context)