from django.shortcuts import get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, View
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin

from core.models import FinalAppointmentWithDoctorModel, IllnessHistory
from application.sanatorium.forms.final_app_form import FinalAppointmentWithDoctorForm


class FinalAppointmentCreateOrUpdateView(LoginRequiredMixin, View):
    """View that handles either creating a new final appointment or updating an existing one"""

    def get(self, request, *args, **kwargs):
        history_id = kwargs.get('history_id')
        illness_history = get_object_or_404(IllnessHistory, pk=history_id)

        # Check if a final appointment already exists
        try:
            existing_appointment = FinalAppointmentWithDoctorModel.objects.get(illness_history=illness_history)
            # If it exists, redirect to the update view
            return redirect('final_appointment_update', pk=existing_appointment.pk)
        except FinalAppointmentWithDoctorModel.DoesNotExist:
            # If it doesn't exist, show the create view
            create_view = FinalAppointmentCreateView.as_view()
            return create_view(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        history_id = kwargs.get('history_id')
        illness_history = get_object_or_404(IllnessHistory, pk=history_id)

        # Check if a final appointment already exists
        try:
            existing_appointment = FinalAppointmentWithDoctorModel.objects.get(illness_history=illness_history)
            # If it exists, use the update view to handle the POST
            update_view = FinalAppointmentUpdateView.as_view()
            return update_view(request, pk=existing_appointment.pk)
        except FinalAppointmentWithDoctorModel.DoesNotExist:
            # If it doesn't exist, use the create view to handle the POST
            create_view = FinalAppointmentCreateView.as_view()
            return create_view(request, *args, **kwargs)


class FinalAppointmentCreateView(LoginRequiredMixin, CreateView):
    model = FinalAppointmentWithDoctorModel
    form_class = FinalAppointmentWithDoctorForm
    template_name = 'sanatorium/doctors/appointments/final_app/form.html'

    def get_success_url(self):
        return reverse_lazy('final_appointment_detail',
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


class FinalAppointmentUpdateView(LoginRequiredMixin, UpdateView):
    model = FinalAppointmentWithDoctorModel
    form_class = FinalAppointmentWithDoctorForm
    template_name = 'sanatorium/doctors/appointments/final_app/form.html'

    def get_success_url(self):
        return reverse_lazy('final_appointment_detail',
                            kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        form.instance.modified_by = self.request.user
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['illness_history'] = self.object.illness_history
        context['history'] = self.object.illness_history
        return context


class FinalAppointmentListView(LoginRequiredMixin, ListView):
    model = FinalAppointmentWithDoctorModel
    template_name = 'sanatorium/doctors/appointments/final_app/list.html'
    context_object_name = 'appointments'

    def get_queryset(self):
        history_id = self.kwargs.get('history_id')
        return FinalAppointmentWithDoctorModel.objects.filter(illness_history_id=history_id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['illness_history'] = get_object_or_404(IllnessHistory, pk=self.kwargs.get('history_id'))
        context['history'] = get_object_or_404(IllnessHistory, pk=self.kwargs.get('history_id'))
        context['history'] = get_object_or_404(IllnessHistory, pk=self.kwargs.get('history_id'))
        return context


class FinalAppointmentDetailView(LoginRequiredMixin, DetailView):
    model = FinalAppointmentWithDoctorModel
    template_name = 'sanatorium/doctors/appointments/final_app/detail.html'
    context_object_name = 'appointment'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['illness_history'] = self.object.illness_history
        context['history'] = self.object.illness_history
        return context


class FinalAppointmentUpdateView(LoginRequiredMixin, UpdateView):
    model = FinalAppointmentWithDoctorModel
    form_class = FinalAppointmentWithDoctorForm
    template_name = 'sanatorium/doctors/appointments/final_app/form.html'

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

