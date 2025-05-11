from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.core.paginator import Paginator
from django.utils import timezone

# Import all appointment models
from core.models import (
    ConsultingWithCardiologistModel,
    FinalAppointmentWithDoctorModel,
    AppointmentWithOnDutyDoctorModel,
    InitialAppointmentWithDoctorModel,
    RepeatedAppointmentWithDoctorModel,
    EkgAppointmentModel,
    AppointmentWithOnDutyDoctorOnArrivalModel,
    ConsultingWithNeurologistModel
)


@login_required
def doctor_appointments(request):
    """View for doctors to see all their appointments."""
    # Get filter parameters
    appointment_type = request.GET.get('type', 'all')
    state = request.GET.get('state', 'all')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')

    # Convert date strings to datetime objects if provided
    if date_from:
        date_from = timezone.datetime.strptime(date_from, '%Y-%m-%d').date()
    if date_to:
        date_to = timezone.datetime.strptime(date_to, '%Y-%m-%d').date()

    # Map of appointment types to their models and display names
    appointment_types = {
        'cardiologist': {
            'model': ConsultingWithCardiologistModel,
            'display': 'Консультация кардиолога'
        },
        'final': {
            'model': FinalAppointmentWithDoctorModel,
            'display': 'Заключительный приём'
        },
        'on_duty': {
            'model': AppointmentWithOnDutyDoctorModel,
            'display': 'Приём у дежурного врача'
        },
        'initial': {
            'model': InitialAppointmentWithDoctorModel,
            'display': 'Первичный приём'
        },
        'repeated': {
            'model': RepeatedAppointmentWithDoctorModel,
            'display': 'Повторный приём'
        },
        'ekg': {
            'model': EkgAppointmentModel,
            'display': 'ЭКГ обследование'
        },
        'on_arrival': {
            'model': AppointmentWithOnDutyDoctorOnArrivalModel,
            'display': 'Приём по прибытии'
        },
        'neurologist': {
            'model': ConsultingWithNeurologistModel,
            'display': 'Консультация невролога'
        }
    }

    # List to store all appointments
    all_appointments = []

    # Function to filter queryset based on common criteria
    def apply_filters(queryset):
        filtered_qs = queryset.filter(doctor=request.user)
        if state != 'all':
            filtered_qs = filtered_qs.filter(state=state)
        if date_from:
            filtered_qs = filtered_qs.filter(created_at__gte=date_from)
        if date_to:
            filtered_qs = filtered_qs.filter(created_at__lte=date_to)
        return filtered_qs.select_related('illness_history')

    # Get appointments based on selected type
    types_to_query = [appointment_type] if appointment_type != 'all' else appointment_types.keys()

    for app_type in types_to_query:
        if app_type in appointment_types:
            app_info = appointment_types[app_type]
            queryset = apply_filters(app_info['model'].objects.all())

            for app in queryset:
                # Get patient info from illness_history
                patient_name = "Нет данных"
                patient_id = None

                if hasattr(app.illness_history, 'patient'):
                    patient = app.illness_history.patient
                    patient_name = getattr(patient, 'full_name', str(patient))
                    patient_id = patient.id

                all_appointments.append({
                    'id': app.id,
                    'type': app_info['display'],
                    'type_key': app_type,
                    'patient_name': patient_name,
                    'patient_id': patient_id,
                    'date': app.created_at,
                    'state': app.state,
                    'url': f'/doctor/appointments/{app_type}/{app.id}/',
                    'cito': getattr(app, 'cito', False)
                })

    # Sort by date (most recent first)
    all_appointments.sort(key=lambda x: x['date'], reverse=True)

    # Paginate results
    paginator = Paginator(all_appointments, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Prepare context for template
    context = {
        'appointments': page_obj,
        'appointment_types': [('all', 'Все приёмы')] +
                             [(k, v['display']) for k, v in appointment_types.items()],
        'states': [
            ('all', 'Все статусы'),
            ('Приём завершён', 'Завершён'),
            ('Пациент на прием не явился', 'Неявка'),
            ('Не завершено', 'Не завершено'),
        ],
        'selected_type': appointment_type,
        'selected_state': state,
        'date_from': date_from.strftime('%Y-%m-%d') if date_from else '',
        'date_to': date_to.strftime('%Y-%m-%d') if date_to else '',
    }

    return render(request, 'sanatorium/doctors/doctors_appointments.html', context)
