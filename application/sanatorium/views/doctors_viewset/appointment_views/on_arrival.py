from core.models import AppointmentWithOnDutyDoctorOnArrivalModel, IllnessHistory
from application.sanatorium.forms.on_arrival_form import OnDutyDoctorOnArrivalForm

from django.shortcuts import get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin


class AppointmentWithOnDutyDoctorOnArrivalCreateView(LoginRequiredMixin, CreateView):
    model = AppointmentWithOnDutyDoctorOnArrivalModel
    form_class = OnDutyDoctorOnArrivalForm
    template_name = 'sanatorium/doctors/appointments/on_arrival/form.html'

    def get_success_url(self):
        return reverse_lazy('on_arrival_consulting_detail',
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


class AppointmentWithOnDutyDoctorOnArrivalListView(LoginRequiredMixin, ListView):
    model = AppointmentWithOnDutyDoctorOnArrivalModel
    template_name = 'sanatorium/doctors/appointments/on_arrival/list.html'
    context_object_name = 'consultings'

    def get_queryset(self):
        history_id = self.kwargs.get('history_id')
        ojs = AppointmentWithOnDutyDoctorOnArrivalModel.objects.filter(illness_history_id=history_id)
        return ojs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['history'] = get_object_or_404(IllnessHistory, pk=self.kwargs.get('history_id'))
        return context


class AppointmentWithOnDutyDoctorOnArrivalDetailView(LoginRequiredMixin, DetailView):
    model = AppointmentWithOnDutyDoctorOnArrivalModel
    template_name = 'sanatorium/doctors/appointments/on_arrival/detail.html'
    context_object_name = 'appointment'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['illness_history'] = self.object.illness_history
        context['history'] = self.object.illness_history
        return context


class AppointmentWithOnDutyDoctorOnArrivalUpdateView(LoginRequiredMixin, UpdateView):
    model = AppointmentWithOnDutyDoctorOnArrivalModel
    form_class = OnDutyDoctorOnArrivalForm
    template_name = 'sanatorium/doctors/appointments/on_arrival/form.html'

    def get_success_url(self):
        return reverse_lazy('on_arrival_consulting_detail',
                            kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        form.instance.modified_by = self.request.user
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['history'] = self.object.illness_history
        return context
