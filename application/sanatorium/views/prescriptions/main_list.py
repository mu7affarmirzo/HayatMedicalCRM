# views.py
from datetime import datetime

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from core.models import IllnessHistory, MedicalServiceModel, ProcedureServiceModel, LabResult, AssignedLabs, \
    LabResearchModel, LabResearchCategoryModel


# @login_required
# def main_prescription_list_view(request, history_id):
#     # Get the illness history
#     history = get_object_or_404(IllnessHistory, id=history_id)
#
#     # Get all medical services (consultations & examinations)
#     consultations = MedicalServiceModel.objects.filter(
#         illness_history=history
#     ).select_related('medical_service', 'consulted_doctor')
#
#     # Get all procedures
#     procedures = ProcedureServiceModel.objects.filter(
#         illness_history=history
#     ).select_related('medical_service', 'therapist').prefetch_related('individual_sessions')
#
#     # Calculate consultation statistics
#     consultation_count = consultations.count()
#     completed_consultations = consultations.filter(state='dispatched').count()
#     completed_consultations_percent = 0
#     if consultation_count > 0:
#         completed_consultations_percent = (completed_consultations / consultation_count) * 100
#
#     # Get all medications
#     try:
#         medications = []
#     except:
#         medications = []
#
#     # Get lab research
#     try:
#         lab_results = LabResult.objects.filter(
#             illness_history=history
#         ).select_related('research', 'specimen_type', 'ordered_by')
#
#         # Prefetch test results for efficiency
#         lab_results = lab_results.prefetch_related('test_results__test')
#     except:
#         lab_results = []
#
#     # Calculate statistics
#     consultation_count = consultations.count()
#     lab_result_count = len(lab_results)
#     total_count = consultation_count + lab_result_count
#
#     completed_consultations = consultations.filter(state='dispatched').count()
#     completed_lab_tests = sum(1 for lab in lab_results if lab.status in ['final', 'amended'])
#     completed_total = completed_consultations + completed_lab_tests
#
#     completed_total_percent = 0
#     if total_count > 0:
#         completed_total_percent = (completed_total / total_count) * 100
#
#     # Calculate procedure statistics
#     procedure_count = procedures.count()
#     total_sessions = 0
#     total_completed_sessions = 0
#
#     for procedure in procedures:
#         total_sessions += procedure.quantity
#         total_completed_sessions += procedure.proceeded_sessions
#
#     total_procedures_percent = 0
#     if total_sessions > 0:
#         total_procedures_percent = (total_completed_sessions / total_sessions) * 100
#
#     # Calculate medication statistics
#     medication_count = len(medications)
#     active_medications = 0
#
#     active_medications_percent = 0
#     if medication_count > 0:
#         active_medications_percent = (active_medications / medication_count) * 100
#
#     active_page = {
#         'proc_main_list_page': 'active',
#     }
#
#     # Include context data
#     context = {
#         'history': history,
#         'consultations': consultations,
#         'procedures': procedures,
#         'medications': medications,
#         'lab_results': lab_results,
#
#         'consultation_count': consultation_count,
#         'lab_result_count': lab_result_count,
#         'total_consultations_count': total_count,
#         'completed_total': completed_total,
#         'completed_total_percent': completed_total_percent,
#         # Add other context variables...
#
#         'procedure_count': procedure_count,
#         'medication_count': medication_count,
#         'completed_consultations': completed_consultations,
#         'completed_consultations_percent': completed_consultations_percent,
#         'total_sessions': total_sessions,
#         'total_completed_sessions': total_completed_sessions,
#         'total_procedures_percent': total_procedures_percent,
#         'active_medications': active_medications,
#         'active_medications_percent': active_medications_percent,
#         'active_page': active_page,
#     }
#
#     return render(request, 'sanatorium/doctors/prescription_urls/main_prescription_list.html', context)

@login_required
def main_prescription_list_view(request, history_id):
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

    # Calculate consultation statistics
    consultation_count = consultations.count()
    completed_consultations = consultations.filter(state='dispatched').count()
    completed_consultations_percent = 0
    if consultation_count > 0:
        completed_consultations_percent = (completed_consultations / consultation_count) * 100

    # Get all medications
    try:
        medications = []
    except:
        medications = []

    # Get lab tests using the new AssignedLabs model
    assigned_labs = AssignedLabs.objects.filter(
        illness_history=history
    ).select_related('lab', 'created_by', 'modified_by')

    # Get all available labs for the assign modal
    available_labs = LabResearchModel.objects.filter(is_active=True)

    # Group labs by category
    lab_categories = LabResearchCategoryModel.objects.all()

    # Process lab filter parameter if provided
    selected_category = request.GET.get('lab_category', 'all')

    # Apply filtering
    if selected_category != 'all' and selected_category in lab_categories:
        filtered_labs = lab_categories[selected_category]
    else:
        filtered_labs = assigned_labs
        selected_category = 'all'  # Ensure we set to 'all' if category doesn't exist

    # Calculate statistics
    consultation_count = consultations.count()
    lab_count = assigned_labs.count()
    total_count = consultation_count + lab_count

    # Calculate lab test statistics
    completed_lab_tests = assigned_labs.filter(state='results').count()
    cancelled_lab_tests = assigned_labs.filter(state__in=['cancelled', 'stopped']).count()
    pending_lab_tests = lab_count - completed_lab_tests - cancelled_lab_tests

    lab_completion_percent = 0
    if lab_count > 0:
        lab_completion_percent = (completed_lab_tests / lab_count) * 100

    completed_total = completed_consultations + completed_lab_tests
    completed_total_percent = 0
    if total_count > 0:
        completed_total_percent = (completed_total / total_count) * 100

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

    active_medications_percent = 0
    if medication_count > 0:
        active_medications_percent = (active_medications / medication_count) * 100

    active_page = {
        'proc_main_list_page': 'active',
    }

    # Include context data
    context = {
        'history': history,
        'consultations': consultations,
        'procedures': procedures,
        'medications': medications,

        # Lab-related context
        'assigned_labs': assigned_labs,
        'filtered_labs': filtered_labs,
        'lab_categories': lab_categories,
        'selected_category': selected_category,
        'available_labs': available_labs,

        # Statistics
        'consultation_count': consultation_count,
        'lab_count': lab_count,
        'total_consultations_count': total_count,
        'completed_total': completed_total,
        'completed_total_percent': completed_total_percent,

        'completed_lab_tests': completed_lab_tests,
        'cancelled_lab_tests': cancelled_lab_tests,
        'pending_lab_tests': pending_lab_tests,
        'lab_completion_percent': lab_completion_percent,

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