from django.shortcuts import get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin

from core.models import EkgAppointmentModel, IllnessHistory
from application.sanatorium.forms.ekg_app_form import EkgAppointmentForm


class EkgAppointmentCreateView(LoginRequiredMixin, CreateView):
    model = EkgAppointmentModel
    form_class = EkgAppointmentForm
    template_name = 'sanatorium/nurses/appointments/ekg_app/form.html'

    def get_success_url(self):
        return reverse_lazy('ekg_appointment_detail',
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


class EkgAppointmentListView(LoginRequiredMixin, ListView):
    model = EkgAppointmentModel
    template_name = 'sanatorium/nurses/appointments/ekg_app/list.html'
    context_object_name = 'appointments'

    def get_queryset(self):
        history_id = self.kwargs.get('history_id')
        return EkgAppointmentModel.objects.filter(illness_history_id=history_id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['illness_history'] = get_object_or_404(IllnessHistory, pk=self.kwargs.get('history_id'))
        context['history'] = get_object_or_404(IllnessHistory, pk=self.kwargs.get('history_id'))
        return context


class EkgAppointmentDetailView(LoginRequiredMixin, DetailView):
    model = EkgAppointmentModel
    template_name = 'sanatorium/nurses/appointments/ekg_app/detail.html'
    context_object_name = 'appointment'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['illness_history'] = self.object.illness_history
        context['history'] = self.object.illness_history
        return context


class EkgAppointmentUpdateView(LoginRequiredMixin, UpdateView):
    model = EkgAppointmentModel
    form_class = EkgAppointmentForm
    template_name = 'sanatorium/nurses/appointments/ekg_app/form.html'

    def get_success_url(self):
        return reverse_lazy('ekg_appointment_detail',
                            kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        form.instance.modified_by = self.request.user
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['illness_history'] = self.object.illness_history
        context['history'] = self.object.illness_history
        return context

