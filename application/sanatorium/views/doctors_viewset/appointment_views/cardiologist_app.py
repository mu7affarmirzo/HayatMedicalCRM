from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404

from core.models import ConsultingWithCardiologistModel, IllnessHistory
from application.sanatorium.decorators import set_active_sidebar
from application.sanatorium.forms.cardiologist_app_form import ConsultingWithCardiologistForm


class CardiologistConsultingListView(LoginRequiredMixin, ListView):
    model = ConsultingWithCardiologistModel
    template_name = 'sanatorium/doctors/appointments/cardiologist/list.html'
    context_object_name = 'consultings'

    def get_queryset(self):
        history_id = self.kwargs.get('history_id')
        return ConsultingWithCardiologistModel.objects.filter(illness_history_id=history_id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['illness_history'] = get_object_or_404(IllnessHistory, pk=self.kwargs.get('history_id'))
        context['history'] = get_object_or_404(IllnessHistory, pk=self.kwargs.get('history_id'))
        context['history'] = get_object_or_404(IllnessHistory, pk=self.kwargs.get('history_id'))
        return context


class CardiologistConsultingDetailView(LoginRequiredMixin, DetailView):
    model = ConsultingWithCardiologistModel
    template_name = 'sanatorium/doctors/appointments/cardiologist/detail.html'
    context_object_name = 'consulting'

    def get_context_data(self, **kwargs):
        print('--------------------')
        context = super().get_context_data(**kwargs)
        context['illness_history'] = self.object.illness_history
        context['history'] = self.object.illness_history
        print(context)
        return context


class CardiologistConsultingCreateView(LoginRequiredMixin, CreateView):
    model = ConsultingWithCardiologistModel
    form_class = ConsultingWithCardiologistForm
    template_name = 'sanatorium/doctors/appointments/cardiologist/form.html'

    def get_success_url(self):
        return reverse_lazy('cardiologist_consulting_detail',
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


class CardiologistConsultingUpdateView(LoginRequiredMixin, UpdateView):
    model = ConsultingWithCardiologistModel
    form_class = ConsultingWithCardiologistForm
    template_name = 'sanatorium/doctors/appointments/cardiologist/form.html'

    def get_success_url(self):
        return reverse_lazy('cardiologist_consulting_detail',
                            kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        form.instance.modified_by = self.request.user
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['illness_history'] = self.object.illness_history
        context['history'] = self.object.illness_history
        return context