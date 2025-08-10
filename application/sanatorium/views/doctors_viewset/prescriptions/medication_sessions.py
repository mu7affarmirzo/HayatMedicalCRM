from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Count, Case, When, IntegerField
from django.utils import timezone
from django.core.paginator import Paginator
from django.views.decorators.http import require_POST
from datetime import datetime, timedelta
import json

from core.models import PrescribedMedication, MedicationSession, PatientModel


@login_required
def medication_sessions_list(request, med_id):
    """
    List all medication sessions for a specific prescribed medication with filtering and search capabilities
    """
    medication = get_object_or_404(PrescribedMedication, id=med_id)
    sessions = medication.sessions.all()

    # Filtering
    status_filter = request.GET.get('status')
    if status_filter:
        sessions = sessions.filter(status=status_filter)

    date_filter = request.GET.get('date')
    if date_filter:
        try:
            filter_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
            sessions = sessions.filter(session_datetime__date=filter_date)
        except ValueError:
            # Invalid date format, ignore filter
            pass

    # Since we're already filtering by a specific medication,
    # patient filter is not needed (all sessions belong to the same patient)
    # But we can add date range filtering
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')

    if date_from:
        try:
            from_date = datetime.strptime(date_from, '%Y-%m-%d').date()
            sessions = sessions.filter(session_datetime__date__gte=from_date)
        except ValueError:
            pass

    if date_to:
        try:
            to_date = datetime.strptime(date_to, '%Y-%m-%d').date()
            sessions = sessions.filter(session_datetime__date__lte=to_date)
        except ValueError:
            pass

    # Search within session notes only (since all sessions are for the same medication/patient)
    search_query = request.GET.get('search')
    if search_query:
        sessions = sessions.filter(
            Q(notes__icontains=search_query) |
            Q(modified_by__f_name__icontains=search_query) |
            Q(modified_by__l_name__icontains=search_query)
        )

    # Pagination
    paginator = Paginator(sessions, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Get summary statistics for this medication
    total_sessions = medication.sessions.count()
    administered_count = medication.sessions.filter(status='administered').count()
    missed_count = medication.sessions.filter(status='missed').count()
    pending_count = medication.sessions.filter(status='pending').count()

    compliance_rate = (administered_count / total_sessions * 100) if total_sessions > 0 else 0

    context = {
        'history': medication.illness_history,
        'medication': medication,
        'page_obj': page_obj,
        'sessions': page_obj,
        'status_choices': MedicationSession.STATUS_CHOICES,
        'current_filters': {
            'status': status_filter,
            'date': date_filter,
            'date_from': date_from,
            'date_to': date_to,
            'search': search_query,
        },
        'stats': {
            'total_sessions': total_sessions,
            'administered_count': administered_count,
            'missed_count': missed_count,
            'pending_count': pending_count,
            'compliance_rate': round(compliance_rate, 1),
        }
    }

    return render(request, 'sanatorium/doctors/prescriptions/medications/sessions_list.html', context)


@login_required
def today_sessions(request):
    """
    Show today's medication sessions for quick access
    """
    today = timezone.now().date()

    sessions = MedicationSession.objects.filter(
        session_datetime__date=today
    ).select_related(
        'prescribed_medication__medication__item',
        'prescribed_medication__illness_history__patient'
    ).order_by('session_datetime')

    # Group by status for dashboard display
    pending_sessions = sessions.filter(status='pending')
    administered_sessions = sessions.filter(status='administered')
    missed_sessions = sessions.filter(status='missed')

    context = {
        'today': today,
        'pending_sessions': pending_sessions,
        'administered_sessions': administered_sessions,
        'missed_sessions': missed_sessions,
        'total_sessions': sessions.count(),
    }

    return render(request, 'sanatorium/doctors/prescriptions/medications/today_sessions.html', context)


@login_required
@require_POST
def update_session_status(request, session_id):
    """
    Update medication session status via AJAX
    """
    session = get_object_or_404(MedicationSession, id=session_id)

    try:
        data = json.loads(request.body)
        new_status = data.get('status')
        notes = data.get('notes', '')

        if new_status not in dict(MedicationSession.STATUS_CHOICES):
            return JsonResponse({'error': 'Invalid status'}, status=400)

        session.status = new_status
        if notes:
            session.notes = notes

        # Set audit fields based on status
        if new_status == 'administered':
            session.modified_by = request.user
            session.modified_at = timezone.now()

        session.save()

        return JsonResponse({
            'success': True,
            'message': f'Session status updated to {session.get_status_display()}',
            'new_status': new_status,
            'status_display': session.get_status_display()
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
def session_detail(request, session_id):
    """
    Show detailed view of a medication session
    """
    session = get_object_or_404(
        MedicationSession.objects.select_related(
            'prescribed_medication__medication__item',
            'prescribed_medication__illness_history__patient',
            'prescribed_medication__prescribed_by'
        ),
        id=session_id
    )

    context = {
        'session': session,
        'status_choices': MedicationSession.STATUS_CHOICES,
        'history': session.prescribed_medication.illness_history
    }

    return render(request, 'sanatorium/doctors/prescriptions/medications/session_detail.html', context)


@login_required
def patient_medications(request, patient_id):
    """
    Show all medications for a specific patient
    """
    patient = get_object_or_404(PatientModel, id=patient_id)

    # Get prescribed medications
    prescribed_medications = PrescribedMedication.objects.filter(
        illness_history__patient=patient
    ).select_related(
        'medication__item',
        'prescribed_by'
    ).order_by('-prescribed_at')

    # Get recent sessions
    recent_sessions = MedicationSession.objects.filter(
        prescribed_medication__illness_history__patient=patient
    ).select_related(
        'prescribed_medication__medication__item'
    ).order_by('-session_datetime')[:10]

    context = {
        'patient': patient,
        'prescribed_medications': prescribed_medications,
        'recent_sessions': recent_sessions,
    }

    return render(request, 'sanatorium/doctors/prescriptions/medications/patient_medications.html', context)


@login_required
def medication_statistics(request):
    """
    Display statistics about medication administration
    """
    # Date range filtering
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')

    if not date_from:
        date_from = (timezone.now() - timedelta(days=30)).date()
    else:
        date_from = datetime.strptime(date_from, '%Y-%m-%d').date()

    if not date_to:
        date_to = timezone.now().date()
    else:
        date_to = datetime.strptime(date_to, '%Y-%m-%d').date()

    # Base queryset
    sessions = MedicationSession.objects.filter(
        session_datetime__date__range=[date_from, date_to]
    )

    # Overall statistics
    total_sessions = sessions.count()

    status_stats = sessions.aggregate(
        administered=Count(
            Case(When(status='administered', then=1),
                 output_field=IntegerField())
        ),
        pending=Count(
            Case(When(status='pending', then=1),
                 output_field=IntegerField())
        ),
        missed=Count(
            Case(When(status='missed', then=1),
                 output_field=IntegerField())
        ),
        refused=Count(
            Case(When(status='refused', then=1),
                 output_field=IntegerField())
        ),
        canceled=Count(
            Case(When(status='canceled', then=1),
                 output_field=IntegerField())
        )
    )

    # Calculate compliance rate
    completed_sessions = status_stats['administered']
    compliance_rate = (completed_sessions / total_sessions * 100) if total_sessions > 0 else 0

    # Medication usage statistics
    medication_stats = sessions.values(
        'prescribed_medication__medication__item__name'
    ).annotate(
        total_sessions=Count('id'),
        administered=Count(
            Case(When(status='administered', then=1),
                 output_field=IntegerField())
        ),
        missed=Count(
            Case(When(status='missed', then=1),
                 output_field=IntegerField())
        )
    ).order_by('-total_sessions')[:10]

    # Daily statistics for chart
    daily_stats = []
    current_date = date_from
    while current_date <= date_to:
        day_sessions = sessions.filter(session_datetime__date=current_date)
        daily_stats.append({
            'date': current_date.strftime('%Y-%m-%d'),
            'date_display': current_date.strftime('%d.%m'),
            'total': day_sessions.count(),
            'administered': day_sessions.filter(status='administered').count(),
            'missed': day_sessions.filter(status='missed').count(),
        })
        current_date += timedelta(days=1)

    # Patient compliance
    patient_compliance = sessions.values(
        'prescribed_medication__illness_history__patient__f_name',
        'prescribed_medication__illness_history__patient__l_name',
        'prescribed_medication__illness_history__patient__id'
    ).annotate(
        total_sessions=Count('id'),
        administered=Count(
            Case(When(status='administered', then=1),
                 output_field=IntegerField())
        )
    ).filter(total_sessions__gt=0).order_by('-total_sessions')

    # Add compliance rate to each patient
    for patient in patient_compliance:
        patient['compliance_rate'] = (
                patient['administered'] / patient['total_sessions'] * 100
        ) if patient['total_sessions'] > 0 else 0

    context = {
        'date_from': date_from,
        'date_to': date_to,
        'total_sessions': total_sessions,
        'status_stats': status_stats,
        'compliance_rate': round(compliance_rate, 1),
        'medication_stats': medication_stats,
        'daily_stats': daily_stats,
        'patient_compliance': patient_compliance,
    }

    return render(request, 'sanatorium/doctors/prescriptions/medications/statistics.html', context)


@login_required
def create_medication_session(request, prescribed_medication_id):
    """
    Create a new medication session for a prescribed medication
    """
    prescribed_medication = get_object_or_404(PrescribedMedication, id=prescribed_medication_id)

    if request.method == 'POST':
        session_datetime = request.POST.get('session_datetime')
        notes = request.POST.get('notes', '')

        try:
            session_datetime = timezone.datetime.strptime(
                session_datetime, '%Y-%m-%dT%H:%M'
            )
            session_datetime = timezone.make_aware(session_datetime)

            MedicationSession.objects.create(
                prescribed_medication=prescribed_medication,
                session_datetime=session_datetime,
                notes=notes,
                created_by=request.user
            )

            messages.success(request, 'Medication session created successfully')
            return redirect('patient_medications', patient_id=prescribed_medication.illness_history.patient.id)

        except ValueError:
            messages.error(request, 'Invalid date/time format')

    context = {
        'prescribed_medication': prescribed_medication,
    }

    return render(request, 'sanatorium/doctors/prescriptions/medications/create_session.html', context)