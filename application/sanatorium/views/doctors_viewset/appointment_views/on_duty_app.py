from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy, reverse
from HayatMedicalCRM.auth.decorators import DoctorRequiredMixin

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect

from application.sanatorium.forms.on_duty_app_form import AppointmentWithOnDutyDoctorForm
from core.models import IllnessHistory
from core.models import AppointmentWithOnDutyDoctorModel


class AppointmentWithOnDutyDoctorListView(DoctorRequiredMixin, ListView):
    model = AppointmentWithOnDutyDoctorModel
    template_name = 'sanatorium/doctors/appointments/on_duty_app/list.html'
    context_object_name = 'appointments'
    paginate_by = 10

    def get_queryset(self):
        # You might want to filter appointments based on the logged-in user
        # For example, if the logged-in user is a doctor, show only their appointments
        if self.request.user.is_superuser:
            return self.model.objects.all().order_by('-created_at')
        return self.model.objects.filter(doctor=self.request.user).order_by('-created_at')


class AppointmentWithOnDutyDoctorDetailView(DoctorRequiredMixin, DetailView):
    model = AppointmentWithOnDutyDoctorModel
    template_name = 'sanatorium/doctors/appointments/on_duty_app/detail.html'
    context_object_name = 'appointment'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add any additional context data here
        context['illness_history'] = self.object.illness_history
        context['history'] = self.object.illness_history
        return context


class AppointmentWithOnDutyDoctorCreateView(DoctorRequiredMixin, CreateView):
    model = AppointmentWithOnDutyDoctorModel
    form_class = AppointmentWithOnDutyDoctorForm
    template_name = 'sanatorium/doctors/appointments/on_duty_app/form.html'

    def get_success_url(self):
        return reverse('on_duty_appointment_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        history_id = self.kwargs.get('history_id')
        context['history'] = get_object_or_404(IllnessHistory, id=history_id)
        context['active_page'] = {'consulting_and_med_services_page': 'active'}
        context['form_title'] = 'Создать новый прием у дежурного врача'
        return context

    def form_valid(self, form):
        # Set the current user as the doctor
        history_id = self.kwargs.get('history_id')
        form.instance.illness_history_id = self.kwargs.get('history_id')
        form.instance.doctor = self.request.user
        form.instance.created_by = self.request.user
        form.instance.modified_by = self.request.user
        messages.success(self.request, 'Прием у дежурного врача успешно создан')
        return super().form_valid(form)


class AppointmentWithOnDutyDoctorUpdateView(DoctorRequiredMixin, UpdateView):
    model = AppointmentWithOnDutyDoctorModel
    form_class = AppointmentWithOnDutyDoctorForm
    template_name = 'sanatorium/doctors/appointments/on_duty_app/form.html'
    context_object_name = 'appointment'

    def get_success_url(self):
        return reverse('appointment_with_on_duty_doctor_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['history'] = self.object.illness_history
        context['active_page'] = {'consulting_and_med_services_page': 'active'}
        context['form_title'] = 'Редактировать прием у дежурного врача'
        return context

    def form_valid(self, form):
        messages.success(self.request, 'Прием у дежурного врача успешно обновлен')
        return super().form_valid(form)
