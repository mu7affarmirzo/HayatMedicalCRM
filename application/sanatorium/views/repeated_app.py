from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from core.models import RepeatedAppointmentWithDoctorModel, IllnessHistory
from .forms import RepeatedAppointmentForm


class RepeatedAppointmentListView(LoginRequiredMixin, ListView):
    model = RepeatedAppointmentWithDoctorModel
    template_name = 'repeated_appointment/list.html'
    context_object_name = 'appointments'

    def get_queryset(self):
        # You might want to filter by some criteria
        return RepeatedAppointmentWithDoctorModel.objects.all().order_by('-created_at')


class RepeatedAppointmentDetailView(LoginRequiredMixin, DetailView):
    model = RepeatedAppointmentWithDoctorModel
    template_name = 'repeated_appointment/detail.html'
    context_object_name = 'appointment'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_page'] = {'consulting_and_med_services_page': 'active'}
        return context


class RepeatedAppointmentCreateView(LoginRequiredMixin, CreateView):
    model = RepeatedAppointmentWithDoctorModel
    template_name = 'repeated_appointment/form.html'
    form_class = RepeatedAppointmentForm

    def get_initial(self):
        initial = super().get_initial()
        # Check if history_id is in URL
        history_id = self.kwargs.get('history_id')
        if history_id:
            initial['illness_history'] = history_id
            initial['doctor'] = self.request.user.id
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Создать повторный приём'
        context['action'] = 'Создать'
        context['active_page'] = {'consulting_and_med_services_page': 'active'}

        # Get illness history for sidebar if available
        history_id = self.kwargs.get('history_id')
        if history_id:
            context['history'] = IllnessHistory.objects.get(id=history_id)

        return context

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.modified_by = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, 'Повторный приём успешно создан!')
        return response

    def get_success_url(self):
        history_id = self.object.illness_history.id
        return reverse('illness_history_detail', kwargs={'pk': history_id})


class RepeatedAppointmentUpdateView(LoginRequiredMixin, UpdateView):
    model = RepeatedAppointmentWithDoctorModel
    template_name = 'repeated_appointment/form.html'
    form_class = RepeatedAppointmentForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Редактировать повторный приём'
        context['action'] = 'Сохранить'
        context['active_page'] = {'consulting_and_med_services_page': 'active'}
        context['history'] = self.object.illness_history
        return context

    def form_valid(self, form):
        form.instance.modified_by = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, 'Повторный приём успешно обновлен!')
        return response

    def get_success_url(self):
        return reverse('repeated_appointment_detail', kwargs={'pk': self.object.pk})


class RepeatedAppointmentDeleteView(LoginRequiredMixin, DeleteView):
    model = RepeatedAppointmentWithDoctorModel
    template_name = 'repeated_appointment/confirm_delete.html'
    context_object_name = 'appointment'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_page'] = {'consulting_and_med_services_page': 'active'}
        context['history'] = self.object.illness_history
        return context

    def get_success_url(self):
        history_id = self.object.illness_history.id
        messages.success(self.request, 'Повторный приём успешно удален!')
        return reverse('illness_history_detail', kwargs={'pk': history_id})