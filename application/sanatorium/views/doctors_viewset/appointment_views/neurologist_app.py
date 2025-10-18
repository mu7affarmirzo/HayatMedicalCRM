from django.shortcuts import get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.urls import reverse_lazy
from HayatMedicalCRM.auth.decorators import DoctorRequiredMixin

from core.models import ConsultingWithNeurologistModel, IllnessHistory
from application.sanatorium.forms.neurologist_app_form import ConsultingWithNeurologistForm


class NeurologistConsultingCreateView(DoctorRequiredMixin, CreateView):
    model = ConsultingWithNeurologistModel
    form_class = ConsultingWithNeurologistForm
    template_name = 'sanatorium/doctors/appointments/neurologist/form.html'

    def get_success_url(self):
        return reverse_lazy('neurologist_consulting_detail',
                            kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        form.instance.illness_history_id = self.kwargs.get('history_id')
        form.instance.doctor = self.request.user
        form.instance.created_by = self.request.user
        form.instance.modified_by = self.request.user
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['illness_history'] = get_object_or_404(IllnessHistory, pk=self.kwargs.get('history_id'))
        context['history'] = get_object_or_404(IllnessHistory, pk=self.kwargs.get('history_id'))
        return context

class NeurologistConsultingListView(DoctorRequiredMixin, ListView):
    model = ConsultingWithNeurologistModel
    template_name = 'sanatorium/doctors/appointments/neurologist/list.html'
    context_object_name = 'consultings'

    def get_queryset(self):
        history_id = self.kwargs.get('history_id')
        return ConsultingWithNeurologistModel.objects.filter(illness_history_id=history_id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['illness_history'] = get_object_or_404(IllnessHistory, pk=self.kwargs.get('history_id'))
        context['history'] = get_object_or_404(IllnessHistory, pk=self.kwargs.get('history_id'))
        context['history'] = get_object_or_404(IllnessHistory, pk=self.kwargs.get('history_id'))
        return context


class NeurologistConsultingDetailView(DoctorRequiredMixin, DetailView):
    model = ConsultingWithNeurologistModel
    template_name = 'sanatorium/doctors/appointments/neurologist/detail.html'
    context_object_name = 'consulting'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['illness_history'] = self.object.illness_history
        context['history'] = self.object.illness_history
        return context


class NeurologistConsultingUpdateView(DoctorRequiredMixin, UpdateView):
    model = ConsultingWithNeurologistModel
    form_class = ConsultingWithNeurologistForm
    template_name = 'sanatorium/doctors/appointments/neurologist/form.html'

    def get_success_url(self):
        return reverse_lazy('neurologist_consulting_detail',
                            kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        form.instance.modified_by = self.request.user
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['illness_history'] = self.object.illness_history
        context['history'] = self.object.illness_history
        return context