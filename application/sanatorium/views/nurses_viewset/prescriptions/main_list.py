# views.py
from datetime import datetime

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from HayatMedicalCRM.auth.decorators import nurse_required
from django.utils import timezone

# Import all appointment models
from core.models import (
    ConsultingWithCardiologistModel,
    ConsultingWithNeurologistModel,
    EkgAppointmentModel,
    AppointmentWithOnDutyDoctorModel,
    RepeatedAppointmentWithDoctorModel,
    AppointmentWithOnDutyDoctorOnArrivalModel,
    InitialAppointmentWithDoctorModel,
    FinalAppointmentWithDoctorModel,
    Account,
    IllnessHistory, MedicalServiceModel, ProcedureServiceModel, LabResult, AssignedLabs,
    LabResearchModel, LabResearchCategoryModel, PrescribedMedication
)


# Helper functions for main_prescription_list view
def get_available_doctors():
    """Get all doctors that can be assigned to appointments"""
    return Account.objects.filter(is_active=True).exclude(is_admin=True)


def get_appointments_by_type(history, model_class, model_name, display_name):
    """
    Fetch appointments of a specific model type for a patient

    Args:
        history: The patient's illness history
        model_class: The appointment model class
        model_name: String identifier for the model type
        display_name: Human-readable name for this appointment type

    Returns:
        List of appointment dictionaries with standardized format
    """
    appointments = []
    for app in model_class.objects.filter(illness_history=history):
        appointments.append({
            'id': app.id,
            'model_name': model_name,
            'created_at': app.created_at,
            'doctor': app.doctor,
            'status': app.state,
            'scheduled_date': getattr(app, 'scheduled_date', None),
            'get_model_display': display_name
        })
    return appointments


def get_all_appointments(history):
    """
    Combine appointments from all model types into a single sorted list

    Args:
        history: The patient's illness history

    Returns:
        List of all appointment dictionaries sorted by creation date
    """
    appointments = []

    # Add appointments from each model type
    appointments.extend(get_appointments_by_type(
        history, ConsultingWithCardiologistModel, 'cardiologist', 'Консультация кардиолога'))

    appointments.extend(get_appointments_by_type(
        history, ConsultingWithNeurologistModel, 'neurologist', 'Консультация невролога'))

    appointments.extend(get_appointments_by_type(
        history, EkgAppointmentModel, 'ekg', 'ЭКГ'))

    appointments.extend(get_appointments_by_type(
        history, AppointmentWithOnDutyDoctorModel, 'onduty', 'Приём у дежурного врача'))

    appointments.extend(get_appointments_by_type(
        history, RepeatedAppointmentWithDoctorModel, 'repeated', 'Повторный приём'))

    # Sort appointments by creation date (newest first)
    appointments.sort(key=lambda x: x['created_at'], reverse=True)

    return appointments


# def get_lab_tests_for_patient(history):
#     """Get all lab tests ordered for a patient"""
#     # Implement based on your lab test model
#     return LabTest.objects.filter(illness_history=history).order_by('-created_at')
#
# def get_procedures_for_patient(history):
#     """Get all treatment procedures prescribed for a patient"""
#     # Implement based on your procedure model
#     return Procedure.objects.filter(illness_history=history).order_by('-created_at')
#
# def get_medications_for_patient(history):
#     """Get all medications prescribed for a patient"""
#     # Implement based on your medication model
#     return Medication.objects.filter(illness_history=history).order_by('-created_at')
#
#
# @nurse_required
# def main_prescription_list(request, history_id):
#     """View for the main prescription list page"""
#     history = get_object_or_404(IllnessHistory, id=history_id)
#
#     # Get all available doctors
#     doctors = get_available_doctors()
#
#     # Get all appointments for this patient
#     appointments = get_all_appointments(history)
#
#     # Get lab tests ordered for this patient
#     lab_tests = get_lab_tests_for_patient(history)
#
#     # Get treatment procedures prescribed for this patient
#     procedures = get_procedures_for_patient(history)
#
#     # Get medications prescribed for this patient
#     medications = get_medications_for_patient(history)
#
#     context = {
#         'history': history,
#         'appointments': appointments,
#         'doctors': doctors,
#         'lab_tests': lab_tests,
#         'procedures': procedures,
#         'medications': medications,
#         'patient': history.patient
#     }
#
#     return render(request, 'sanatorium/nurses/prescriptions/main_prescription_list.html', context)


# Helper functions for create_appointment view
def parse_appointment_form(request):
    """
    Parse and validate form data from the appointment creation form

    Args:
        request: The HTTP request

    Returns:
        Dict containing parsed form data or None if validation fails
    """
    form_data = {
        'consultation_type': request.POST.get('consultation_type'),
        'doctor_id': request.POST.get('doctor_id'),
        'scheduled_date_str': request.POST.get('scheduled_date'),
        'priority': request.POST.get('priority') == 'urgent',  # Convert to boolean
        'notes': request.POST.get('notes', '')
    }

    # Basic validation
    if not all([form_data['consultation_type'], form_data['doctor_id'], form_data['scheduled_date_str']]):
        return None

    # Parse scheduled date
    try:
        scheduled_date = timezone.datetime.strptime(form_data['scheduled_date_str'], '%d.%m.%Y %H:%M')
        # Make timezone aware
        form_data['scheduled_date'] = timezone.make_aware(scheduled_date)
    except ValueError:
        return None

    return form_data


def get_appointment_model_class(consultation_type):
    """
    Get the correct appointment model class based on consultation type

    Args:
        consultation_type: String identifier for the appointment type

    Returns:
        Appointment model class or None if type is invalid
    """
    model_mapping = {
        'cardiologist': ConsultingWithCardiologistModel,
        'neurologist': ConsultingWithNeurologistModel,
        'ekg': EkgAppointmentModel,
        'onduty': AppointmentWithOnDutyDoctorModel,
        'repeated': RepeatedAppointmentWithDoctorModel
    }

    return model_mapping.get(consultation_type)


def create_appointment_instance(model_class, doctor, history, priority, user):
    """
    Create a new appointment instance of the specified model type

    Args:
        model_class: The appointment model class
        doctor: The doctor assigned to the appointment
        history: The patient's illness history
        priority: Boolean indicating if this is an urgent appointment
        user: The user creating the appointment

    Returns:
        Newly created appointment instance
    """
    return model_class.objects.create(
        doctor=doctor,
        illness_history=history,
        cito=priority,
        created_by=user,
        state='Не завершено'
    )


def schedule_appointment(appointment, scheduled_date):
    """
    Add scheduling information to an appointment

    Args:
        appointment: The appointment instance
        scheduled_date: The date and time when the appointment is scheduled
    """
    # Add scheduled date to the appointment if the model supports it
    if hasattr(appointment, 'scheduled_date'):
        appointment.scheduled_date = scheduled_date
        appointment.save()

    # Here you would also integrate with your scheduling system if needed
    # For example:
    # Schedule.objects.create(
    #     appointment_id=appointment.id,
    #     appointment_type=consultation_type,
    #     doctor=doctor,
    #     patient=history.patient,
    #     scheduled_date=scheduled_date,
    #     notes=notes
    # )


@nurse_required
def create_appointment(request, history_id):
    """View for creating a new appointment"""
    if request.method != 'POST':
        return redirect('main_prescription_list', history_id=history_id)

    history = get_object_or_404(IllnessHistory, id=history_id)

    # Parse and validate form data
    form_data = parse_appointment_form(request)
    if not form_data:
        messages.error(request, 'Неверные данные формы')
        return redirect('main_prescription_list', history_id=history_id)

    # Get doctor
    doctor = get_object_or_404(Account, id=form_data['doctor_id'])

    # Get appropriate model class
    model_class = get_appointment_model_class(form_data['consultation_type'])
    if not model_class:
        messages.error(request, 'Неверный тип консультации')
        return redirect('main_prescription_list', history_id=history_id)

    # Create appointment
    appointment = create_appointment_instance(
        model_class,
        doctor,
        history,
        form_data['priority'],
        request.user
    )

    # Schedule the appointment
    schedule_appointment(appointment, form_data['scheduled_date'])

    messages.success(request, f'Консультация успешно назначена на {form_data["scheduled_date_str"]}')
    return redirect('main_prescription_list', history_id=history_id)


# Helper functions for cancel_appointment view
def get_appointment_instance(model_name, appointment_id):
    """
    Get the correct appointment instance based on model name and ID

    Args:
        model_name: String identifier for the model type
        appointment_id: ID of the appointment

    Returns:
        Appointment instance or None if model name is invalid
    """
    model_mapping = {
        'cardiologist': ConsultingWithCardiologistModel,
        'neurologist': ConsultingWithNeurologistModel,
        'ekg': EkgAppointmentModel,
        'onduty': AppointmentWithOnDutyDoctorModel,
        'repeated': RepeatedAppointmentWithDoctorModel
    }

    model_class = model_mapping.get(model_name)
    if not model_class:
        return None

    return get_object_or_404(model_class, id=appointment_id)


@nurse_required
def cancel_appointment(request, history_id):
    """View for canceling an appointment"""
    if request.method != 'POST':
        return redirect('main_prescription_list', history_id=history_id)

    # Get form data
    appointment_id = request.POST.get('appointment_id')
    model_name = request.POST.get('model_name')
    cancel_reason = request.POST.get('cancel_reason', '')

    # Find the appointment
    appointment = get_appointment_instance(model_name, appointment_id)
    if not appointment:
        messages.error(request, 'Неверный тип консультации')
        return redirect('main_prescription_list', history_id=history_id)

    # Update appointment status
    appointment.state = 'Пациент на прием не явился'
    appointment.modified_by = request.user
    appointment.save()

    # Log cancellation reason if you have a separate model for that
    # CancellationLog.objects.create(
    #     appointment_type=model_name,
    #     appointment_id=appointment_id,
    #     reason=cancel_reason,
    #     user=request.user
    # )

    messages.success(request, 'Консультация отменена')
    return redirect('main_prescription_list', history_id=history_id)


def get_appointment_detail_template(model_name):
    """
    Get the appropriate template for viewing appointment details

    Args:
        model_name: String identifier for the model type

    Returns:
        Template path string
    """
    template_mapping = {
        'cardiologist': 'sanatorium/nurses/appointments/cardiologist_app/detail.html',
        'neurologist': 'sanatorium/nurses/appointments/neurologist/detail.html',
        'ekg': 'sanatorium/nurses/appointments/ekg_app/detail.html',
        'onduty': 'sanatorium/nurses/appointments/on_duty_app/detail.html',
        'repeated': 'sanatorium/nurses/appointments/repeated_app/detail.html'
    }

    return template_mapping.get(model_name, 'sanatorium/nurses/appointments/generic_detail.html')


@nurse_required
def view_appointment(request, model_name, appointment_id):
    """
    View for displaying appointment details

    Args:
        request: The HTTP request
        model_name: String identifier for the model type
        appointment_id: ID of the appointment

    Returns:
        Rendered template with appointment details
    """
    # Get the appointment instance
    appointment = get_appointment_instance(model_name, appointment_id)
    if not appointment:
        messages.error(request, 'Неверный тип консультации')
        return redirect('dashboard')  # Fallback if we can't determine history_id

    # Get patient's illness history
    history = appointment.illness_history

    # Get template for this appointment type
    template = get_appointment_detail_template(model_name)

    # Determine if the appointment is editable (not completed)
    is_editable = appointment.state != 'Приём завершён'

    # Create context with appointment details
    context = {
        'appointment': appointment,
        'history': history,
        'model_name': model_name,
        'is_editable': is_editable,
        'appointment_type_display': {
            'cardiologist': 'Консультация кардиолога',
            'neurologist': 'Консультация невролога',
            'ekg': 'ЭКГ',
            'onduty': 'Приём у дежурного врача',
            'repeated': 'Повторный приём'
        }.get(model_name, 'Консультация')
    }

    return render(request, template, context)


@nurse_required
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
        medications = PrescribedMedication.objects.filter(illness_history=history)
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

    doctors = Account.objects.filter(roles__name="Doctor")

    appointments = []

    # Add Cardiologist appointments
    for app in ConsultingWithCardiologistModel.objects.filter(illness_history=history):
        appointments.append({
            'id': app.id,
            'model_name': 'cardiologist',
            'created_at': app.created_at,
            'doctor': app.doctor,
            'status': app.state,
            'scheduled_date': getattr(app, 'scheduled_date', None),
            'get_model_display': 'Консультация кардиолога'
        })

    # Add Neurologist appointments
    for app in ConsultingWithNeurologistModel.objects.filter(illness_history=history):
        appointments.append({
            'id': app.id,
            'model_name': 'neurologist',
            'created_at': app.created_at,
            'doctor': app.doctor,
            'status': app.state,
            'scheduled_date': getattr(app, 'scheduled_date', None),
            'get_model_display': 'Консультация невролога'
        })

    # Add EKG appointments
    for app in EkgAppointmentModel.objects.filter(illness_history=history):
        appointments.append({
            'id': app.id,
            'model_name': 'ekg',
            'created_at': app.created_at,
            'doctor': app.doctor,
            'status': app.state,
            'scheduled_date': getattr(app, 'scheduled_date', None),
            'get_model_display': 'ЭКГ'
        })

    # Add On-Duty Doctor appointments
    for app in AppointmentWithOnDutyDoctorModel.objects.filter(illness_history=history):
        appointments.append({
            'id': app.id,
            'model_name': 'onduty',
            'created_at': app.created_at,
            'doctor': app.doctor,
            'status': app.state,
            'scheduled_date': getattr(app, 'scheduled_date', None),
            'get_model_display': 'Приём у дежурного врача'
        })

    # Add Repeated appointments
    for app in RepeatedAppointmentWithDoctorModel.objects.filter(illness_history=history):
        appointments.append({
            'id': app.id,
            'model_name': 'repeated',
            'created_at': app.created_at,
            'doctor': app.doctor,
            'status': app.state,
            'scheduled_date': getattr(app, 'scheduled_date', None),
            'get_model_display': 'Повторный приём'
        })

    # Sort appointments by creation date (newest first)
    appointments.sort(key=lambda x: x['created_at'], reverse=True)

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

        'appointments': appointments,
        'doctors': doctors
    }

    return render(request, 'sanatorium/nurses/prescriptions/main_prescription_list.html', context)

