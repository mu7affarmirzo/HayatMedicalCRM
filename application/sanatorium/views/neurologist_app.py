from django.shortcuts import get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin

from core.models import ConsultingWithNeurologistModel, IllnessHistory
from ..forms.neurologist_app_form import ConsultingWithNeurologistForm

class NeurologistConsultingCreateView(LoginRequiredMixin, CreateView):
    model = ConsultingWithNeurologistModel
    form_class = ConsultingWithNeurologistForm
    template_name = 'sanatorium/doctors/neurologist/form.html'

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

class NeurologistConsultingListView(LoginRequiredMixin, ListView):
    model = ConsultingWithNeurologistModel
    template_name = 'sanatorium/doctors/neurologist/list.html'
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


class NeurologistConsultingDetailView(LoginRequiredMixin, DetailView):
    model = ConsultingWithNeurologistModel
    template_name = 'sanatorium/doctors/neurologist/detail.html'
    context_object_name = 'consulting'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['illness_history'] = self.object.illness_history
        context['history'] = self.object.illness_history
        return context


class NeurologistConsultingUpdateView(LoginRequiredMixin, UpdateView):
    model = ConsultingWithNeurologistModel
    form_class = ConsultingWithNeurologistForm
    template_name = 'sanatorium/doctors/neurologist/form.html'

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