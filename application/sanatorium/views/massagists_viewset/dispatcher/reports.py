import json
from datetime import timedelta
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Count, Q, Sum, Case, When, Value, IntegerField, F
from core.models import ProcedureServiceModel, IndividualProcedureSessionModel, Account, Service


@login_required
def reports_view(request):
    """
    Reports view for analyzing procedure and therapist performance
    """
    # Get date range from request or default to current month
    period = request.GET.get('period', 'month')
    today = timezone.now().date()

    # Determine date range based on selected period
    if period == 'week':
        start_date = today - timedelta(days=today.weekday())  # Monday of this week
        end_date = start_date + timedelta(days=6)  # Sunday of this week
        report_period_text = f"Текущая неделя ({start_date.strftime('%d.%m.%Y')} - {end_date.strftime('%d.%m.%Y')})"

    elif period == 'month':
        start_date = today.replace(day=1)  # First day of current month
        # Last day of current month
        if today.month == 12:
            end_date = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            end_date = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
        report_period_text = f"Текущий месяц ({start_date.strftime('%d.%m.%Y')} - {end_date.strftime('%d.%m.%Y')})"

    elif period == 'quarter':
        quarter = (today.month - 1) // 3 + 1
        start_date = today.replace(month=(quarter - 1) * 3 + 1, day=1)
        if quarter == 4:
            end_date = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            end_date = today.replace(month=quarter * 3 + 1, day=1) - timedelta(days=1)
        report_period_text = f"Текущий квартал ({start_date.strftime('%d.%m.%Y')} - {end_date.strftime('%d.%m.%Y')})"

    elif period == 'year':
        start_date = today.replace(month=1, day=1)  # January 1st of current year
        end_date = today.replace(month=12, day=31)  # December 31st of current year
        report_period_text = f"Текущий год ({start_date.strftime('%d.%m.%Y')} - {end_date.strftime('%d.%m.%Y')})"

    elif period == 'custom':
        try:
            start_date = timezone.datetime.strptime(request.GET.get('start_date'), '%d.%m.%Y').date()
            end_date = timezone.datetime.strptime(request.GET.get('end_date'), '%d.%m.%Y').date()
            report_period_text = f"Пользовательский период ({start_date.strftime('%d.%m.%Y')} - {end_date.strftime('%d.%m.%Y')})"
        except (ValueError, TypeError):
            # Default to current month if date parsing fails
            start_date = today.replace(day=1)
            if today.month == 12:
                end_date = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                end_date = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
            report_period_text = f"Текущий месяц ({start_date.strftime('%d.%m.%Y')} - {end_date.strftime('%d.%m.%Y')})"
    else:
        # Default to current month
        start_date = today.replace(day=1)
        if today.month == 12:
            end_date = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            end_date = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
        report_period_text = f"Текущий месяц ({start_date.strftime('%d.%m.%Y')} - {end_date.strftime('%d.%m.%Y')})"

    # Basic statistics
    total_procedures = ProcedureServiceModel.objects.filter(
        start_date__range=[start_date, end_date]
    ).count()

    completed_sessions = IndividualProcedureSessionModel.objects.filter(
        completed_at__date__range=[start_date, end_date],
        status='completed'
    ).count()

    pending_sessions = IndividualProcedureSessionModel.objects.filter(
        scheduled_to__date__range=[start_date, end_date],
        status='pending'
    ).count()

    canceled_sessions = IndividualProcedureSessionModel.objects.filter(
        Q(scheduled_to__date__range=[start_date, end_date]) | Q(completed_at__date__range=[start_date, end_date]),
        status='canceled'
    ).count()

    # Service types statistics
    service_stats = ProcedureServiceModel.objects.filter(
        start_date__range=[start_date, end_date]
    ).values('medical_service__name').annotate(
        count=Count('id')
    ).order_by('-count')[:10]

    service_types_labels = [item['medical_service__name'] for item in service_stats]
    service_types_data = [item['count'] for item in service_stats]

    # Timeline data
    # Determine the appropriate time grouping based on the date range
    days_diff = (end_date - start_date).days

    if days_diff <= 31:
        # Daily grouping for up to a month
        timeline_data = {}
        current_date = start_date
        while current_date <= end_date:
            date_str = current_date.strftime('%d.%m')
            timeline_data[date_str] = {
                'completed': 0,
                'canceled': 0
            }
            current_date += timedelta(days=1)

        # Completed sessions
        completed_timeline = IndividualProcedureSessionModel.objects.filter(
            completed_at__date__range=[start_date, end_date],
            status='completed'
        ).values('completed_at__date').annotate(
            count=Count('id')
        )

        for item in completed_timeline:
            date_str = item['completed_at__date'].strftime('%d.%m')
            if date_str in timeline_data:
                timeline_data[date_str]['completed'] = item['count']

        # Canceled sessions
        canceled_timeline = IndividualProcedureSessionModel.objects.filter(
            Q(scheduled_to__date__range=[start_date, end_date]) | Q(completed_at__date__range=[start_date, end_date]),
            status='canceled'
        ).values('scheduled_to__date').annotate(
            count=Count('id')
        )

        for item in canceled_timeline:
            if item['scheduled_to__date']:
                date_str = item['scheduled_to__date'].strftime('%d.%m')
                if date_str in timeline_data:
                    timeline_data[date_str]['canceled'] = item['count']

        timeline_labels = list(timeline_data.keys())
        completed_timeline_data = [timeline_data[date]['completed'] for date in timeline_labels]
        canceled_timeline_data = [timeline_data[date]['canceled'] for date in timeline_labels]

    else:
        # Weekly grouping for larger ranges
        timeline_data = {}
        current_date = start_date
        week_number = 1

        while current_date <= end_date:
            week_end = min(current_date + timedelta(days=6), end_date)
            week_str = f"Неделя {week_number} ({current_date.strftime('%d.%m')} - {week_end.strftime('%d.%m')})"
            timeline_data[week_str] = {
                'completed': 0,
                'canceled': 0,
                'start': current_date,
                'end': week_end
            }
            current_date = week_end + timedelta(days=1)
            week_number += 1

        # Completed sessions
        for week_str, week_data in timeline_data.items():
            completed_count = IndividualProcedureSessionModel.objects.filter(
                completed_at__date__range=[week_data['start'], week_data['end']],
                status='completed'
            ).count()
            timeline_data[week_str]['completed'] = completed_count

            canceled_count = IndividualProcedureSessionModel.objects.filter(
                Q(scheduled_to__date__range=[week_data['start'], week_data['end']]) |
                Q(completed_at__date__range=[week_data['start'], week_data['end']]),
                status='canceled'
            ).count()
            timeline_data[week_str]['canceled'] = canceled_count

        timeline_labels = list(timeline_data.keys())
        completed_timeline_data = [timeline_data[week]['completed'] for week in timeline_labels]
        canceled_timeline_data = [timeline_data[week]['canceled'] for week in timeline_labels]

    # Therapist statistics
    therapist_stats = []
    therapists = Account.objects.filter(is_therapist=True)

    for therapist in therapists:
        # Get completed and canceled sessions for this therapist
        completed = IndividualProcedureSessionModel.objects.filter(
            therapist=therapist,
            completed_at__date__range=[start_date, end_date],
            status='completed'
        ).count()

        canceled = IndividualProcedureSessionModel.objects.filter(
            therapist=therapist,
            status='canceled'
        ).count()

        # Calculate efficiency (completed sessions / total sessions)
        total = completed + canceled
        efficiency = int((completed / total) * 100) if total > 0 else 0

        # Calculate workload (assuming 8 hour days, 5 days a week)
        max_capacity = (end_date - start_date).days * 8  # 8 hours per day
        workload = int((completed / max_capacity) * 100) if max_capacity > 0 else 0
        workload = min(workload, 100)  # Cap at 100%

        therapist_stats.append({
            'name': therapist.full_name,
            'completed': completed,
            'canceled': canceled,
            'efficiency': efficiency,
            'workload': workload
        })

    # Top services
    top_services = Service.objects.filter(
        procedureservicemodel__start_date__range=[start_date, end_date]
    ).annotate(
        procedure_count=Count('procedureservicemodel'),
        session_count=Sum('procedureservicemodel__quantity')
    ).order_by('-procedure_count')[:10]

    # Procedure status statistics
    status_counts = ProcedureServiceModel.objects.filter(
        start_date__range=[start_date, end_date]
    ).values('state').annotate(
        count=Count('id')
    ).order_by('state')

    status_labels = []
    status_data = []

    # Convert status values to display labels
    status_display = dict(ProcedureServiceModel.STATE_CHOICES)
    for item in status_counts:
        status_labels.append(status_display.get(item['state'], item['state']))
        status_data.append(item['count'])

    context = {
        'period': period,
        'start_date': start_date,
        'end_date': end_date,
        'report_period_text': report_period_text,

        # Basic statistics
        'total_procedures': total_procedures,
        'completed_sessions': completed_sessions,
        'pending_sessions': pending_sessions,
        'canceled_sessions': canceled_sessions,

        # Chart data
        'service_types_labels': json.dumps(service_types_labels),
        'service_types_data': json.dumps(service_types_data),
        'timeline_labels': json.dumps(timeline_labels),
        'completed_timeline_data': json.dumps(completed_timeline_data),
        'canceled_timeline_data': json.dumps(canceled_timeline_data),
        'status_labels': json.dumps(status_labels),
        'status_data': json.dumps(status_data),

        # Table data
        'therapist_stats': therapist_stats,
        'top_services': top_services,
    }

    return render(request, 'sanatorium/massagists/dispatcher/reports.html', context)