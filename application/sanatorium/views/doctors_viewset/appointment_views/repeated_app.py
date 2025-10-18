from django.shortcuts import get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.urls import reverse_lazy
from HayatMedicalCRM.auth.decorators import DoctorRequiredMixin

from core.models import RepeatedAppointmentWithDoctorModel, IllnessHistory
from application.sanatorium.forms.repeated_app_form import RepeatedAppointmentForm


class RepeatedAppointmentCreateView(DoctorRequiredMixin, CreateView):
    model = RepeatedAppointmentWithDoctorModel
    form_class = RepeatedAppointmentForm
    template_name = 'sanatorium/doctors/appointments/repeated_app/form.html'

    def get_success_url(self):
        return reverse_lazy('repeated_appointment_detail',
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


class RepeatedAppointmentListView(DoctorRequiredMixin, ListView):
    model = RepeatedAppointmentWithDoctorModel
    template_name = 'sanatorium/doctors/appointments/repeated_app/list.html'
    context_object_name = 'appointments'

    def get_queryset(self):
        history_id = self.kwargs.get('history_id')
        return RepeatedAppointmentWithDoctorModel.objects.filter(illness_history_id=history_id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['illness_history'] = get_object_or_404(IllnessHistory, pk=self.kwargs.get('history_id'))
        context['history'] = get_object_or_404(IllnessHistory, pk=self.kwargs.get('history_id'))
        context['history'] = get_object_or_404(IllnessHistory, pk=self.kwargs.get('history_id'))
        return context


class RepeatedAppointmentDetailView(DoctorRequiredMixin, DetailView):
    model = RepeatedAppointmentWithDoctorModel
    template_name = 'sanatorium/doctors/appointments/repeated_app/detail.html'
    context_object_name = 'appointment'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['illness_history'] = self.object.illness_history
        context['history'] = self.object.illness_history
        return context


class RepeatedAppointmentUpdateView(DoctorRequiredMixin, UpdateView):
    model = RepeatedAppointmentWithDoctorModel
    form_class = RepeatedAppointmentForm
    template_name = 'sanatorium/doctors/appointments/repeated_app/form.html'

    def get_success_url(self):
        return reverse_lazy('repeated_appointment_detail',
                            kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        form.instance.modified_by = self.request.user
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['illness_history'] = self.object.illness_history
        context['history'] = self.object.illness_history
        return context

