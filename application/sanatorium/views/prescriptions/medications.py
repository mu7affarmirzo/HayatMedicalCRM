# views.py
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy, reverse
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import get_object_or_404

from ...forms.medications_form import PrescribedMedicationForm, MedicationAdministrationForm

from core.models import PrescribedMedication, MedicationAdministration, IllnessHistory


# PrescribedMedication Views
class PrescribedMedicationListView(LoginRequiredMixin, ListView):
    model = PrescribedMedication
    template_name = 'sanatorium/doctors/prescriptions/medications/list.html'
    context_object_name = 'medications'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filter by illness_history if provided
        illness_history_id = self.request.GET.get('illness_history')
        if illness_history_id:
            queryset = queryset.filter(illness_history_id=illness_history_id)

        # Filter by status if provided
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Add illness_history to context if filtering by it
        illness_history_id = self.request.GET.get('illness_history')
        if illness_history_id:
            context['illness_history'] = get_object_or_404(IllnessHistory, id=illness_history_id)

        # Add status choices for filtering
        context['status_choices'] = PrescribedMedication.STATUS_CHOICES

        return context


class PrescribedMedicationDetailView(LoginRequiredMixin, DetailView):
    model = PrescribedMedication
    template_name = 'sanatorium/doctors/prescriptions/medications/detail.html'
    context_object_name = 'medication'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add administrations to context
        context['administrations'] = self.object.administrations.all().order_by('-administered_at')
        return context


class PrescribedMedicationCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = PrescribedMedication
    form_class = PrescribedMedicationForm
    template_name = 'sanatorium/doctors/prescriptions/medications/form.html'
    success_message = "Назначение успешно создано"

    def get_initial(self):
        initial = super().get_initial()
        # Pre-populate illness_history if provided in URL
        illness_history_id = self.request.GET.get('illness_history')
        if illness_history_id:
            initial['illness_history'] = illness_history_id
        return initial

    def form_valid(self, form):
        # Set the prescribed_by field to the current user
        form.instance.illness_history = get_object_or_404(IllnessHistory, pk=self.kwargs.get('illness_history_id'))
        form.instance.prescribed_by = self.request.user
        form.instance.doctor = self.request.user
        form.instance.created_by = self.request.user
        form.instance.modified_by = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('main_prescription_list', kwargs={'history_id': self.object.illness_history.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['illness_history'] = get_object_or_404(IllnessHistory, pk=self.kwargs.get('illness_history_id'))
        context['history'] = get_object_or_404(IllnessHistory, pk=self.kwargs.get('illness_history_id'))
        return context


class PrescribedMedicationUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = PrescribedMedication
    form_class = PrescribedMedicationForm
    template_name = 'sanatorium/doctors/prescriptions/medications/form.html'
    context_object_name = 'medication'
    success_message = "Назначение успешно обновлено"

    def form_valid(self, form):
        # Set the last_modified_by field to the current user
        form.instance.last_modified_by = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('prescribed_medication_detail', kwargs={'pk': self.object.id})


class PrescribedMedicationDeleteView(LoginRequiredMixin, SuccessMessageMixin, DeleteView):
    model = PrescribedMedication
    template_name = 'sanatorium/doctors/prescriptions/medications/confirm_delete.html'
    context_object_name = 'medication'
    success_message = "Назначение успешно удалено"

    def get_success_url(self):
        # Redirect to illness history detail if available
        if self.object.illness_history:
            return reverse_lazy('illness_history_detail', kwargs={'pk': self.object.illness_history.id})
        return reverse_lazy('prescribed_medication_list')


# MedicationAdministration Views
class MedicationAdministrationListView(LoginRequiredMixin, ListView):
    model = MedicationAdministration
    template_name = 'sanatorium/doctors/prescriptions/medications/list.html'
    context_object_name = 'administrations'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filter by prescribed_medication if provided
        prescribed_medication_id = self.request.GET.get('prescribed_medication')
        if prescribed_medication_id:
            queryset = queryset.filter(prescribed_medication_id=prescribed_medication_id)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Add prescribed_medication to context if filtering by it
        prescribed_medication_id = self.request.GET.get('prescribed_medication')
        if prescribed_medication_id:
            context['prescribed_medication'] = get_object_or_404(
                PrescribedMedication,
                id=prescribed_medication_id
            )

        return context


class MedicationAdministrationDetailView(LoginRequiredMixin, DetailView):
    model = MedicationAdministration
    template_name = 'sanatorium/doctors/prescriptions/medications/detail.html'
    context_object_name = 'administration'


class MedicationAdministrationCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = MedicationAdministration
    form_class = MedicationAdministrationForm
    template_name = 'sanatorium/doctors/prescriptions/medications/form.html'
    success_message = "Применение лекарства успешно зарегистрировано"

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Remove prescribed_medication field as it will be set from URL
        if 'prescribed_medication_id' in self.kwargs:
            if 'prescribed_medication' in form.fields:
                del form.fields['prescribed_medication']
        return form

    def form_valid(self, form):
        # Set the prescribed_medication if provided in URL
        if 'prescribed_medication_id' in self.kwargs:
            form.instance.prescribed_medication = get_object_or_404(
                PrescribedMedication, pk=self.kwargs['prescribed_medication_id']
            )

        # Set default fields
        form.instance.created_by = self.request.user
        form.instance.modified_by = self.request.user

        # If administered_by not specified, use current user
        if not form.instance.administered_by:
            form.instance.administered_by = self.request.user

        return super().form_valid(form)

    def get_success_url(self):
        if hasattr(self.object, 'prescribed_medication') and self.object.prescribed_medication:
            return reverse('prescribed_medication_detail',
                           kwargs={'pk': self.object.prescribed_medication.id})
        return reverse('medication_administration_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if 'prescribed_medication_id' in self.kwargs:
            prescribed_medication = get_object_or_404(
                PrescribedMedication, pk=self.kwargs['prescribed_medication_id']
            )
            context['prescribed_medication'] = prescribed_medication
            context['illness_history'] = prescribed_medication.illness_history
        return context


class MedicationAdministrationUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = MedicationAdministration
    form_class = MedicationAdministrationForm
    template_name = 'sanatorium/doctors/prescriptions/medications/form.html'
    context_object_name = 'administration'
    success_message = "Применение лекарства успешно обновлено"

    def form_valid(self, form):
        # Set the modified_by field to the current user
        form.instance.modified_by = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('medication_administration_detail', kwargs={'pk': self.object.id})


class MedicationAdministrationDeleteView(LoginRequiredMixin, SuccessMessageMixin, DeleteView):
    model = MedicationAdministration
    template_name = 'sanatorium/doctors/prescriptions/medications/confirm_delete.html'
    context_object_name = 'administration'
    success_message = "Применение лекарства успешно удалено"

    def get_success_url(self):
        return reverse_lazy('prescribed_medication_detail',
                            kwargs={'pk': self.object.prescribed_medication.id})