# warehouse/views/medication_expenses.py
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Q, F, DecimalField, Case, When
from django.utils import timezone
from datetime import timedelta, date
from collections import defaultdict
import calendar

from core.models import PrescribedMedication, MedicationSession
from core.models import MedicationsInStockModel  # Adjust import path as needed


@login_required
def medication_expenses_dashboard(request):
    """
    Dashboard view showing expected medication expenses based on prescribed medications
    """
    context = {}

    # Get filter parameters
    period = request.GET.get('period', '30')  # days
    status_filter = request.GET.get('status', 'active')

    try:
        period_days = int(period)
    except ValueError:
        period_days = 30

    # Calculate date ranges
    today = timezone.now().date()
    start_date = today
    end_date = today + timedelta(days=period_days)

    # Base queryset for active prescriptions
    base_prescriptions = PrescribedMedication.objects.select_related(
        'medication__item',
        'illness_history__patient',
        'prescribed_by'
    )

    print(base_prescriptions)

    # Apply status filter
    if status_filter == 'active':
        base_prescriptions = base_prescriptions.filter(
            Q(end_date__isnull=True) | Q(end_date__gte=start_date),  # Q object first
            status='active',                                          # keyword args after
            start_date__lte=end_date
        )
    elif status_filter == 'all':
        base_prescriptions = base_prescriptions.filter(
            Q(end_date__isnull=True) | Q(end_date__gte=start_date),  # Q object first
            status='active',                                          # keyword args after
            start_date__lte=end_date
        )

    # Get expected medication consumption
    medication_expenses = calculate_medication_expenses(
        base_prescriptions, start_date, end_date
    )

    print('----', medication_expenses)

    # Get pending sessions for the period
    pending_sessions = get_pending_sessions(start_date, end_date)

    # Get daily breakdown
    daily_breakdown = get_daily_medication_breakdown(
        base_prescriptions, start_date, end_date
    )

    # Get top medications by cost
    top_medications = get_top_medications_by_cost(medication_expenses)

    # Get patient medication summary
    patient_summary = get_patient_medication_summary(base_prescriptions)

    # Calculate totals
    total_expected_cost = sum(item['total_cost'] for item in medication_expenses.values())
    total_sessions = sum(item['total_sessions'] for item in medication_expenses.values())
    total_patients = len(patient_summary)

    context.update({
        'period_days': period_days,
        'start_date': start_date,
        'end_date': end_date,
        'status_filter': status_filter,
        'medication_expenses': medication_expenses,
        'pending_sessions': pending_sessions,
        'daily_breakdown': daily_breakdown,
        'top_medications': top_medications,
        'patient_summary': patient_summary,
        'total_expected_cost': total_expected_cost,
        'total_sessions': total_sessions,
        'total_patients': total_patients,
        'total_medications': len(medication_expenses),
    })

    return render(request, 'warehouse/patient_expenses/medication_expenses_dashboard.html', context)


def calculate_medication_expenses(prescriptions, start_date, end_date):
    """
    Calculate expected medication expenses for the given period
    """
    medication_expenses = defaultdict(lambda: {
        'medication_name': '',
        'medication_id': None,
        'unit_cost': 0,
        'total_sessions': 0,
        'total_cost': 0,
        'prescriptions': [],
        'current_stock': 0,
        'expected_shortage': 0,
    })

    for prescription in prescriptions:
        # Calculate sessions for this prescription in the period
        sessions_count = calculate_prescription_sessions(
            prescription, start_date, end_date
        )

        if sessions_count > 0:
            medication = prescription.medication
            med_key = medication.id

            # Get unit cost (you might need to adjust this based on your pricing model)
            unit_cost = getattr(medication, 'unit_cost', 0) or getattr(medication, 'price', 0)

            medication_expenses[med_key]['medication_name'] = medication.item.name
            medication_expenses[med_key]['medication_id'] = medication.id
            medication_expenses[med_key]['unit_cost'] = float(unit_cost)
            medication_expenses[med_key]['total_sessions'] += sessions_count
            medication_expenses[med_key]['total_cost'] += float(unit_cost) * sessions_count
            medication_expenses[med_key]['current_stock'] = medication.quantity_in_stock

            # Add prescription details
            medication_expenses[med_key]['prescriptions'].append({
                'patient_name': prescription.illness_history.patient.full_name,
                'dosage': prescription.dosage,
                'frequency': prescription.get_frequency_display(),
                'sessions_count': sessions_count,
                'prescription_id': prescription.id,
            })

    # Calculate expected shortages
    for med_data in medication_expenses.values():
        shortage = max(0, med_data['total_sessions'] - med_data['current_stock'])
        med_data['expected_shortage'] = shortage

    return dict(medication_expenses)


def calculate_prescription_sessions(prescription, start_date, end_date):
    """
    Calculate number of sessions for a prescription in the given period
    """
    # Get the effective period for this prescription
    prescription_start = max(prescription.start_date, start_date)
    prescription_end = prescription.end_date if prescription.end_date else end_date
    prescription_end = min(prescription_end, end_date)

    if prescription_start > prescription_end:
        return 0

    days_in_period = (prescription_end - prescription_start).days + 1

    # Calculate sessions per day based on frequency
    frequency_map = {
        'once': 1 / days_in_period if days_in_period > 0 else 0,  # One time total
        'daily': 1,
        'bid': 2,
        'tid': 3,
        'qid': 4,
        'qhs': 1,
        'q4h': 6,
        'q6h': 4,
        'q8h': 3,
        'q12h': 2,
        'weekly': 1 / 7,
        'biweekly': 2 / 7,
        'monthly': 1 / 30,
        'prn': 0.5,  # Estimate for PRN medications
    }

    sessions_per_day = frequency_map.get(prescription.frequency, 1)
    total_sessions = int(sessions_per_day * days_in_period)

    return total_sessions


def get_pending_sessions(start_date, end_date):
    """
    Get pending medication sessions for the period
    """
    return MedicationSession.objects.filter(
        session_datetime__date__range=[start_date, end_date],
        status='pending'
    ).select_related(
        'prescribed_medication__medication__item',
        'prescribed_medication__illness_history__patient'
    ).order_by('session_datetime')


def get_daily_medication_breakdown(prescriptions, start_date, end_date):
    """
    Get daily breakdown of expected medication usage
    """
    daily_data = defaultdict(lambda: {
        'date': None,
        'total_sessions': 0,
        'total_cost': 0,
        'medications': defaultdict(int)
    })

    current_date = start_date
    while current_date <= end_date:
        daily_data[current_date]['date'] = current_date
        current_date += timedelta(days=1)

    # Calculate daily usage for each prescription
    for prescription in prescriptions:
        sessions_per_day = get_daily_sessions_for_prescription(prescription)
        unit_cost = float(getattr(prescription.medication, 'unit_cost', 0) or
                          getattr(prescription.medication, 'price', 0))

        # Distribute sessions across the period
        current_date = start_date
        while current_date <= end_date:
            if is_prescription_active_on_date(prescription, current_date):
                daily_sessions = sessions_per_day
                daily_cost = daily_sessions * unit_cost

                daily_data[current_date]['total_sessions'] += daily_sessions
                daily_data[current_date]['total_cost'] += daily_cost
                daily_data[current_date]['medications'][prescription.medication.item.name] += daily_sessions

            current_date += timedelta(days=1)

    return dict(daily_data)


def get_daily_sessions_for_prescription(prescription):
    """
    Get number of sessions per day for a prescription
    """
    frequency_map = {
        'daily': 1,
        'bid': 2,
        'tid': 3,
        'qid': 4,
        'qhs': 1,
        'q4h': 6,
        'q6h': 4,
        'q8h': 3,
        'q12h': 2,
        'weekly': 1 / 7,
        'biweekly': 2 / 7,
        'monthly': 1 / 30,
        'prn': 0.5,
        'once': 0,  # Handle separately
    }

    return frequency_map.get(prescription.frequency, 1)


def is_prescription_active_on_date(prescription, check_date):
    """
    Check if prescription is active on a specific date
    """
    if check_date < prescription.start_date:
        return False

    if prescription.end_date and check_date > prescription.end_date:
        return False

    return prescription.status == 'active'


def get_top_medications_by_cost(medication_expenses):
    """
    Get top medications by expected cost
    """
    sorted_medications = sorted(
        medication_expenses.items(),
        key=lambda x: x[1]['total_cost'],
        reverse=True
    )

    return sorted_medications[:10]  # Top 10


def get_patient_medication_summary(prescriptions):
    """
    Get summary of medications per patient
    """
    patient_summary = defaultdict(lambda: {
        'patient_name': '',
        'patient_id': None,
        'total_medications': 0,
        'total_expected_cost': 0,
        'medications': []
    })

    for prescription in prescriptions:
        patient = prescription.illness_history.patient
        patient_key = patient.id

        unit_cost = float(getattr(prescription.medication, 'unit_cost', 0) or
                          getattr(prescription.medication, 'price', 0))

        patient_summary[patient_key]['patient_name'] = patient.full_name
        patient_summary[patient_key]['patient_id'] = patient.id
        patient_summary[patient_key]['total_medications'] += 1
        patient_summary[patient_key]['medications'].append({
            'name': prescription.medication.item.name,
            'dosage': prescription.dosage,
            'frequency': prescription.get_frequency_display(),
            'status': prescription.get_status_display(),
        })

    return dict(patient_summary)


@login_required
def medication_expenses_export(request):
    """
    Export medication expenses data to CSV/Excel
    """
    # Implementation for exporting data
    pass