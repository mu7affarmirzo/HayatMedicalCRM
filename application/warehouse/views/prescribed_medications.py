# warehouse/views/medications.py
from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q, Count, Case, When, IntegerField
from django.utils import timezone
from core.models import PrescribedMedication


class PrescribedMedicationListView(LoginRequiredMixin, ListView):
    model = PrescribedMedication
    template_name = 'warehouse/prescribed_medications/prescribed_medication_list.html'
    context_object_name = 'prescribed_medications'
    paginate_by = 20

    def get_queryset(self):
        queryset = PrescribedMedication.objects.select_related(
            'medication__item',
            'illness_history__patient',
            'prescribed_by'
        ).prefetch_related('sessions').annotate(
            total_sessions=Count('sessions'),
            administered_sessions=Count(
                Case(When(sessions__status='administered', then=1),
                     output_field=IntegerField())
            ),
            pending_sessions=Count(
                Case(When(sessions__status='pending', then=1),
                     output_field=IntegerField())
            ),
            missed_sessions=Count(
                Case(When(sessions__status='missed', then=1),
                     output_field=IntegerField())
            )
        ).order_by('-prescribed_at')

        # Search functionality
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(medication__item__name__icontains=search_query) |
                Q(illness_history__patient__f_name__icontains=search_query) |
                Q(illness_history__patient__l_name__icontains=search_query) |
                Q(prescribed_by__f_name__icontains=search_query) |
                Q(prescribed_by__l_name__icontains=search_query)
            )

        # Status filter
        status_filter = self.request.GET.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        context['status_filter'] = self.request.GET.get('status', '')
        context['progress_filter'] = self.request.GET.get('progress', '')
        context['status_choices'] = PrescribedMedication.STATUS_CHOICES

        # Add progress calculations for each prescription
        filtered_prescriptions = []
        progress_filter = self.request.GET.get('progress', '')

        # Statistics counters
        stats = {
            'active_count': 0,
            'excellent_progress': 0,
            'needs_attention': 0,
            'overdue_count': 0
        }

        for prescription in context['prescribed_medications']:
            prescription.progress_data = self.calculate_progress(prescription)

            # Update statistics
            if prescription.status == 'active':
                stats['active_count'] += 1

            if prescription.progress_data['overall_status'] == 'excellent':
                stats['excellent_progress'] += 1
            elif prescription.progress_data['overall_status'] in ['poor', 'fair']:
                stats['needs_attention'] += 1
            elif prescription.progress_data['overall_status'] == 'overdue':
                stats['overdue_count'] += 1

            # Apply progress filter
            if progress_filter:
                if prescription.progress_data['overall_status'] == progress_filter:
                    filtered_prescriptions.append(prescription)
            else:
                filtered_prescriptions.append(prescription)

        # Update the context with filtered prescriptions if progress filter is applied
        if progress_filter:
            context['prescribed_medications'] = filtered_prescriptions
            # Recalculate stats for filtered results
            stats = {
                'active_count': sum(1 for p in filtered_prescriptions if p.status == 'active'),
                'excellent_progress': sum(
                    1 for p in filtered_prescriptions if p.progress_data['overall_status'] == 'excellent'),
                'needs_attention': sum(
                    1 for p in filtered_prescriptions if p.progress_data['overall_status'] in ['poor', 'fair']),
                'overdue_count': sum(
                    1 for p in filtered_prescriptions if p.progress_data['overall_status'] == 'overdue')
            }

        context['statistics'] = stats
        return context

    def calculate_progress(self, prescription):
        """Calculate various progress metrics for a prescription"""
        today = timezone.now().date()

        # Session progress
        total_sessions = prescription.total_sessions
        administered_sessions = prescription.administered_sessions
        session_percentage = (administered_sessions / total_sessions * 100) if total_sessions > 0 else 0

        # Treatment duration progress
        duration_progress = 0
        duration_percentage = 0
        if prescription.start_date and prescription.end_date:
            total_days = (prescription.end_date - prescription.start_date).days
            if total_days > 0:
                if today >= prescription.end_date:
                    completed_days = total_days
                    duration_percentage = 100
                elif today >= prescription.start_date:
                    completed_days = (today - prescription.start_date).days
                    duration_percentage = (completed_days / total_days * 100)
                else:
                    completed_days = 0
                    duration_percentage = 0
                duration_progress = {
                    'completed_days': completed_days,
                    'total_days': total_days,
                    'percentage': duration_percentage
                }

        # Overall progress status
        if prescription.status == 'completed':
            overall_status = 'completed'
        elif prescription.status == 'discontinued':
            overall_status = 'discontinued'
        elif prescription.end_date and today > prescription.end_date:
            overall_status = 'overdue'
        elif session_percentage >= 90:
            overall_status = 'excellent'
        elif session_percentage >= 70:
            overall_status = 'good'
        elif session_percentage >= 50:
            overall_status = 'fair'
        else:
            overall_status = 'poor'

        return {
            'session_percentage': round(session_percentage, 1),
            'duration_progress': duration_progress,
            'duration_percentage': round(duration_percentage, 1),
            'overall_status': overall_status,
            'is_active': prescription.is_active
        }


class PrescribedMedicationDetailView(LoginRequiredMixin, DetailView):
    model = PrescribedMedication
    template_name = 'warehouse/prescribed_medications/prescribed_medication_detail.html'
    context_object_name = 'prescribed_medication'

    def get_queryset(self):
        return PrescribedMedication.objects.select_related(
            'medication__item',
            'illness_history__patient',
            'prescribed_by',
            'last_modified_by'
        ).prefetch_related('sessions')