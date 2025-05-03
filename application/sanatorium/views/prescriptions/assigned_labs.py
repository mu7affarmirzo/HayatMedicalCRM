from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q

from application.sanatorium.forms.assigned_labs_form import AssignedLabsForm
from core.models import AssignedLabs, LabResearchModel, LabResearchCategoryModel, IllnessHistory


@login_required
def assign_lab_create(request, history_id):
    """View for creating a new lab assignment"""
    history = get_object_or_404(IllnessHistory, id=history_id)
    categories = LabResearchCategoryModel.objects.all()

    if request.method == 'POST':
        form = AssignedLabsForm(request.POST)
        if form.is_valid():
            lab_assignment = form.save(commit=False)
            lab_assignment.illness_history = history
            lab_assignment.created_by = request.user
            lab_assignment.save()

            messages.success(request, f'Лабораторный тест "{lab_assignment.lab.name}" успешно назначен.')
            return redirect('illness_history_detail', pk=history.id)
    else:
        # Pre-populate form with the illness history
        form = AssignedLabsForm(initial={'illness_history': history.id})

    context = {
        'form': form,
        'history': history,
        'categories': categories,
        'title': 'Назначить лабораторный тест',
        'selected_category': '',  # Will be updated by JS when user selects a category
        'action': 'Назначить'
    }

    return render(request, 'sanatorium/doctors/prescriptions/labs/assigned_labs_form.html', context)


class AssignedLabsListView(LoginRequiredMixin, ListView):
    model = AssignedLabs
    template_name = 'sanatorium/doctors/appointments/on_duty_app/list.html'
    context_object_name = 'appointments'
    paginate_by = 10

    def get_queryset(self):
        # You might want to filter appointments based on the logged-in user
        # For example, if the logged-in user is a doctor, show only their appointments
        if self.request.user.is_superuser:
            return self.model.objects.all().order_by('-created_at')
        return self.model.objects.filter(doctor=self.request.user).order_by('-created_at')


class AssignedLabsDetailView(LoginRequiredMixin, DetailView):
    model = AssignedLabs
    template_name = 'sanatorium/doctors/appointments/on_duty_app/detail.html'
    context_object_name = 'appointment'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add any additional context data here
        context['illness_history'] = self.object.illness_history
        context['history'] = self.object.illness_history
        return context


class AssignedLabsCreateView(LoginRequiredMixin, CreateView):
    model = AssignedLabs
    form_class = AssignedLabsForm
    template_name = 'sanatorium/doctors/prescriptions/labs/assigned_labs_form.html'

    def get_success_url(self):
        return reverse('main_prescription_list', kwargs={'history_id': self.object.illness_history.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        history_id = self.kwargs.get('illness_history_id')
        context['history'] = get_object_or_404(IllnessHistory, id=history_id)
        context['active_page'] = {'consulting_and_med_services_page': 'active'}
        context['form_title'] = 'Создать новый прием у дежурного врача'
        return context

    def form_valid(self, form):
        # Set the current user as the doctor
        history_id = self.kwargs.get('history_id')
        form.instance.illness_history_id = self.kwargs.get('illness_history_id')
        form.instance.doctor = self.request.user
        form.instance.created_by = self.request.user
        form.instance.modified_by = self.request.user
        messages.success(self.request, 'Прием у дежурного врача успешно создан')
        return super().form_valid(form)


class AssignedLabsUpdateView(LoginRequiredMixin, UpdateView):
    model = AssignedLabs
    form_class = AssignedLabsForm
    template_name = 'sanatorium/doctors/prescriptions/labs/assigned_labs_form.html'
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


class AssignedLabsDeleteView(LoginRequiredMixin, DeleteView):
    model = AssignedLabs
    template_name = 'sanatorium/doctors/prescriptions/labs/assigned_labs_confirm_delete.html'

    def get_success_url(self):
        messages.success(self.request, "Lab assignment successfully deleted.")
        if self.object.illness_history:
            return reverse('illness_history_detail', kwargs={'pk': self.object.illness_history.pk})
        return reverse('assigned_labs_list')


@login_required
def get_labs_by_category(request):
    """AJAX view for getting labs filtered by category"""
    category_id = request.GET.get('category_id')
    search_term = request.GET.get('search_term', '')

    labs_query = LabResearchModel.objects.filter(is_active=True)

    # Apply category filter if provided
    if category_id:
        labs_query = labs_query.filter(category_id=category_id)

    # Apply search filter if provided
    if search_term:
        labs_query = labs_query.filter(name__icontains=search_term)

    # Limit to reasonable number
    labs_query = labs_query[:50]

    # Prepare response data
    labs_data = []
    for lab in labs_query:
        labs_data.append({
            'id': lab.id,
            'name': lab.name,
            'price': str(lab.price),
            'category_name': lab.category.name if lab.category else None,
            'cito': lab.cito,
            'deadline': lab.deadline
        })

    return JsonResponse({'labs': labs_data})


def update_lab_state(request, pk, new_state):
    if request.method == 'POST':
        assigned_lab = get_object_or_404(AssignedLabs, pk=pk)

        # Validate the new state
        valid_states = [state[0] for state in AssignedLabs.STATE_CHOICES]
        if new_state not in valid_states:
            return JsonResponse({'success': False, 'error': 'Invalid state'}, status=400)

        assigned_lab.state = new_state
        assigned_lab.save()

        return JsonResponse({
            'success': True,
            'state': assigned_lab.state,
            'state_display': dict(AssignedLabs.STATE_CHOICES)[assigned_lab.state]
        })

    return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)