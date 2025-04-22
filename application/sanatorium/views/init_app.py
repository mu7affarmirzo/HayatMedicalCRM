from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404

from application.sanatorium.forms.init_appointment_form import InitialAppointmentForm
from core.models import InitialAppointmentWithDoctorModel, IllnessHistory


class AssignedDoctorRequiredMixin(LoginRequiredMixin):
    """
    Mixin to ensure only the doctor assigned to the illness_history can access the view
    """

    def dispatch(self, request, *args, **kwargs):
        # First check if user is logged in
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        # Get the appointment if it exists
        if 'pk' in kwargs:
            appointment = get_object_or_404(InitialAppointmentWithDoctorModel, pk=kwargs['pk'])

            # Allow access only if current user is the assigned doctor
            if appointment.doctor == request.user:
                return super().dispatch(request, *args, **kwargs)
            else:
                raise PermissionDenied("You are not the assigned doctor for this appointment.")

        # For creation views (no pk), check if user is assigned to illness_history
        if 'illness_history_id' in kwargs:
            illness_history = get_object_or_404(IllnessHistory, pk=kwargs['illness_history_id'])

            # Check if user is assigned to the illness_history
            # This depends on your specific model relations, adjust as needed
            if getattr(illness_history, 'assigned_doctor', None) == request.user:
                return super().dispatch(request, *args, **kwargs)
            else:
                raise PermissionDenied("You are not assigned to this patient's history.")

        return super().dispatch(request, *args, **kwargs)


class AppointmentListView(AssignedDoctorRequiredMixin, ListView):
    model = InitialAppointmentWithDoctorModel
    template_name = 'sanatorium/patients/appointments/init_app/appointment_list.html'
    context_object_name = 'appointments'

    def get_queryset(self):
        # Show only appointments where the logged-in user is the doctor
        return InitialAppointmentWithDoctorModel.objects.filter(
            doctor=self.request.user
        ).select_related('illness_history', 'diagnosis')


class AppointmentDetailView(AssignedDoctorRequiredMixin, DetailView):
    model = InitialAppointmentWithDoctorModel
    template_name = 'sanatorium/patients/appointments/init_app/appointment_detail.html'
    context_object_name = 'appointment'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['fieldsets'] = InitialAppointmentForm.Meta.fieldsets
        return context


class AppointmentCreateView(CreateView):
    model = InitialAppointmentWithDoctorModel
    form_class = InitialAppointmentForm
    template_name = 'sanatorium/patients/appointments/init_app/appointment_form.html'

    def get_initial(self):
        initial = super().get_initial()
        # Pre-populate with illness_history if provided
        if 'illness_history_id' in self.kwargs:
            initial['illness_history'] = self.kwargs['illness_history_id']
        return initial

    def form_valid(self, form):
        # Set the doctor to current user
        form.instance.doctor = self.request.user
        # Set created_by to current user
        form.instance.created_by = self.request.user

        messages.success(self.request, _("Appointment record created successfully."))
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('appointment-detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['action'] = _('Create')
        context['fieldsets'] = self.form_class.Meta.fieldsets
        return context


class AppointmentUpdateView(AssignedDoctorRequiredMixin, UpdateView):
    model = InitialAppointmentWithDoctorModel
    form_class = InitialAppointmentForm
    template_name = 'sanatorium/patients/appointments/init_app/appointment_form.html'

    def form_valid(self, form):
        # Set modified_by to current user
        form.instance.modified_by = self.request.user

        messages.success(self.request, _("Appointment record updated successfully."))
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('appointment-detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['action'] = _('Update')
        context['fieldsets'] = self.form_class.Meta.fieldsets
        return context


class AppointmentDeleteView(AssignedDoctorRequiredMixin, DeleteView):
    model = InitialAppointmentWithDoctorModel
    template_name = 'sanatorium/patients/appointments/init_app/appointment_confirm_delete.html'
    success_url = reverse_lazy('appointment-list')

    def delete(self, request, *args, **kwargs):
        messages.success(request, _("Appointment record deleted successfully."))
        return super().delete(request, *args, **kwargs)