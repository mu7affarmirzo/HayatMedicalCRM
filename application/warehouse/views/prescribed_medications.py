# warehouse/views/medications.py
from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
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
        context['status_choices'] = PrescribedMedication.STATUS_CHOICES
        return context


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