from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import ListView, CreateView, UpdateView, DeleteView

from application.sanatorium.forms.patients import IllnessHistoryForm
from core.models import IllnessHistory, BookingDetail


class DoctorRequiredMixin(UserPassesTestMixin):
    """Mixin to ensure that only therapists can access the view"""

    def test_func(self):
        # return self.request.user.is_therapist
        return self.request.user


@login_required
def assigned_patients_list(request):
    # # Check if user is a doctor
    # if not request.user.is_therapist:
    #     return redirect('home')  # Redirect non-doctors

    # Get all illness histories where the current user is the assigned doctor
    patient_histories = IllnessHistory.objects.filter(doctor=request.user)

    # Get today's appointments
    today = timezone.now().date()
    today_appointments = IllnessHistory.objects.filter(
        doctor=request.user,
        booking__start_date__date=today
    ).count()

    # Get statistics
    stationary_count = patient_histories.filter(type='stationary').count()
    ambulatory_count = patient_histories.filter(type='ambulatory').count()

    context = {
        'patient_histories': patient_histories,
        'today_appointments': today_appointments,
        'stationary_count': stationary_count,
        'ambulatory_count': ambulatory_count,
        'total_patients': patient_histories.count(),
    }

    return render(request, 'sanatorium/doctors/doctors_dashboard.html', context)


class IllnessHistoryListView(LoginRequiredMixin, DoctorRequiredMixin, ListView):
    model = IllnessHistory
    template_name = 'sanatorium/doctors/illness_history_list.html'
    context_object_name = 'histories'

    def get_queryset(self):
        # Only show illness histories assigned to the logged-in doctor
        return IllnessHistory.objects.filter(doctor=self.request.user).order_by('-modified_at')


class IllnessHistoryCreateView(LoginRequiredMixin, DoctorRequiredMixin, CreateView):
    model = IllnessHistory
    form_class = IllnessHistoryForm
    template_name = 'sanatorium/doctors/illness_history_form.html'
    success_url = reverse_lazy('illness_history_list')

    def form_valid(self, form):
        # Set the doctor automatically to the current user
        form.instance.doctor = self.request.user
        messages.success(self.request, 'История болезни успешно создана')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Создание истории болезни'
        return context


@login_required
def illness_history_detail(request, pk):
    # Get the illness history
    history = get_object_or_404(IllnessHistory, pk=pk)

    # Security check - only the assigned doctor or admin can view
    if history.doctor != request.user and not request.user.is_admin:
        return redirect('illness_history_list')

    # Get patient data
    patient = history.patient
    booking = history.booking

    # Get booking details for this patient
    booking_details = BookingDetail.objects.filter(
        booking=booking,
        client=patient
    ).select_related('room', 'room__room_type', 'tariff')

    context = {
        'history': history,
        'patient': patient,
        'booking': booking,
        'booking_details': booking_details,
        'active_page': {
            'medical_records': 'active'
        }
    }

    return render(request, 'sanatorium/doctors/illness_history_detail.html', context)


class IllnessHistoryUpdateView(LoginRequiredMixin, DoctorRequiredMixin, UpdateView):
    model = IllnessHistory
    form_class = IllnessHistoryForm
    template_name = 'sanatorium/doctors/illness_history_form.html'

    def get_queryset(self):
        # Only allow doctors to update their own assigned histories
        return IllnessHistory.objects.filter(doctor=self.request.user)

    def get_success_url(self):
        return reverse_lazy('illness_history_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, 'История болезни успешно обновлена')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Редактирование истории болезни'
        context['patient'] = self.object.patient
        return context


class IllnessHistoryDeleteView(LoginRequiredMixin, DoctorRequiredMixin, DeleteView):
    model = IllnessHistory
    template_name = 'sanatorium/patients/illness_history_confirm_delete.html'
    success_url = reverse_lazy('illness_history_list')

    def get_queryset(self):
        # Only allow doctors to delete their own assigned histories
        return IllnessHistory.objects.filter(doctor=self.request.user)

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'История болезни успешно удалена')
        return super().delete(request, *args, **kwargs)

    # If you prefer to deactivate instead of delete:
    # def delete(self, request, *args, **kwargs):
    #     history = self.get_object()
    #     history.state = 'closed'
    #     history.save()
    #     messages.success(request, 'История болезни закрыта')
    #     return redirect(self.success_url)


class IllnessHistoryCloseView(LoginRequiredMixin, DoctorRequiredMixin, UpdateView):
    """Special view to mark an illness history as closed"""
    model = IllnessHistory
    template_name = 'sanatorium/doctors/illness_history_confirm_close.html'
    fields = []
    success_url = reverse_lazy('illness_history_list')

    def get_queryset(self):
        return IllnessHistory.objects.filter(doctor=self.request.user)

    def form_valid(self, form):
        form.instance.state = 'closed'
        messages.success(self.request, 'История болезни закрыта')
        return super().form_valid(form)
