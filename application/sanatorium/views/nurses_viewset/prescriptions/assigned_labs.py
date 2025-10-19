from HayatMedicalCRM.auth.decorators import nurse_required
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.http import JsonResponse
from HayatMedicalCRM.auth.decorators import NurseRequiredMixin
from django.db.models import Q

from application.sanatorium.forms.assigned_labs_form import AssignedLabsForm
from core.models import AssignedLabs, LabResearchModel, LabResearchCategoryModel, IllnessHistory, AssignedLabResult


@nurse_required
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
            return redirect('sanatorium.nurses:illness_history_detail', pk=history.id)
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

    return render(request, 'sanatorium/nurses/prescriptions/labs/assigned_labs_form.html', context)


class AssignedLabsListView(NurseRequiredMixin, ListView):
    model = AssignedLabs
    template_name = 'sanatorium/nurses/appointments/on_duty_app/list.html'
    context_object_name = 'assigned_labs'
    paginate_by = 10

    def get_queryset(self):
        # You might want to filter appointments based on the logged-in user
        # For example, if the logged-in user is a doctor, show only their appointments
        if self.request.user.is_superuser:
            return self.model.objects.all().order_by('-created_at')
        return self.model.objects.filter(doctor=self.request.user).order_by('-created_at')


class AssignedLabsDetailView(NurseRequiredMixin, DetailView):
    model = AssignedLabs
    template_name = 'sanatorium/nurses/prescriptions/labs/assigned_labs_detail.html'
    context_object_name = 'assigned_lab'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add any additional context data here
        context['illness_history'] = self.object.illness_history
        context['history'] = self.object.illness_history
        return context


class AssignedLabsCreateView(NurseRequiredMixin, CreateView):
    model = AssignedLabs
    form_class = AssignedLabsForm
    template_name = 'sanatorium/nurses/prescriptions/labs/assigned_labs_form.html'

    def get_success_url(self):
        return reverse('sanatorium.nurses:main_prescription_list', kwargs={'history_id': self.object.illness_history.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        history_id = self.kwargs.get('illness_history_id')
        context['history'] = get_object_or_404(IllnessHistory, id=history_id)
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


class AssignedLabsUpdateView(NurseRequiredMixin, UpdateView):
    model = AssignedLabs
    form_class = AssignedLabsForm
    template_name = 'sanatorium/nurses/prescriptions/labs/assigned_labs_form.html'
    context_object_name = 'assigned_lab'

    def get_success_url(self):
        return reverse('sanatorium.nurses:prescription_labs', kwargs={'history_id': self.object.illness_history.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['history'] = self.object.illness_history
        context['form_title'] = 'Редактировать прием у дежурного врача'
        return context

    def form_valid(self, form):
        messages.success(self.request, 'Прием у дежурного врача успешно обновлен')
        return super().form_valid(form)


class AssignedLabsDeleteView(NurseRequiredMixin, DeleteView):
    model = AssignedLabs
    context_object_name = 'assigned_lab'
    template_name = 'sanatorium/nurses/prescriptions/labs/assigned_labs_confirm_delete.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['history'] = self.object.illness_history
        context['form_title'] = '-'
        return context

    def get_success_url(self):
        messages.success(self.request, "Lab assignment successfully deleted.")
        if self.object.illness_history:
            return reverse('sanatorium.nurses:main_prescription_list', kwargs={'history_id': self.object.illness_history.pk})
        return reverse('sanatorium.nurses:assigned_labs_list')


@nurse_required
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


@nurse_required
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


# @nurse_required
# @require_POST
# def update_lab_state(request, lab_id, new_state):
#     """
#     Обновление статуса назначенного лабораторного анализа через AJAX запрос.
#
#     Args:
#         request: HTTP запрос
#         lab_id: ID назначенного анализа
#         new_state: Новый статус (recommended, assigned, dispatched, results, cancelled, stopped)
#
#     Returns:
#         JsonResponse с результатом операции
#     """
#     try:
#         # Проверка, что статус является допустимым
#         if new_state not in dict(AssignedLabs.STATE_CHOICES):
#             return JsonResponse({'success': False, 'error': 'Недопустимый статус'}, status=400)
#
#         # Получение назначенного анализа
#         assigned_lab = get_object_or_404(AssignedLabs, id=lab_id)
#
#         # Проверка прав доступа (опционально - настройте согласно вашей логике)
#         # if assigned_lab.illness_history.doctor != request.user:
#         #    return JsonResponse({'success': False, 'error': _('Нет прав доступа')}, status=403)
#
#         # Специальная обработка для перехода в статус 'results'
#         if new_state == 'results' and assigned_lab.state != 'results':
#             # Проверяем наличие результатов
#             if not assigned_lab.lab_results.exists():
#                 return JsonResponse({
#                     'success': False,
#                     'error': 'Невозможно установить статус "Результаты доступны" без добавления результатов'
#                 }, status=400)
#
#         # Обновление статуса
#         old_state = assigned_lab.state
#         assigned_lab.state = new_state
#         assigned_lab.modified_by = request.user
#         assigned_lab.save()
#
#         # Получение отображаемого значения статуса
#         state_display = dict(AssignedLabs.STATE_CHOICES).get(new_state, new_state)
#
#         # Возвращаем успешный ответ
#         return JsonResponse({
#             'success': True,
#             'state': new_state,
#             'state_display': state_display,
#             'old_state': old_state
#         })
#
#     except Exception as e:
#         # Обработка ошибок
#         return JsonResponse({'success': False, 'error': str(e)}, status=500)


@nurse_required
@require_POST
def add_lab_result(request, assigned_lab_id):
    """
    View to handle the submission of lab results from the modal form.
    """
    assigned_lab = get_object_or_404(AssignedLabs, id=assigned_lab_id)

    # Check if the assigned lab is in a state where results can be added
    if assigned_lab.state not in ['dispatched', 'results']:
        messages.error(request, "Lab results can only be added for dispatched labs.")
        return redirect('sanatorium.nurses:assigned_labs_detail', pk=assigned_lab.id)

    try:
        # Extract data from the form
        comments = request.POST.get('comments', '')
        attached_file = request.FILES.get('attached_file', None)

        # Create a new lab result
        lab_result = AssignedLabResult(
            assigned_lab=assigned_lab,
            comments=comments,
            attached_file=attached_file,
            created_by=request.user,
            modified_by=request.user
        )
        lab_result.save()

        # Update the state of the assigned lab
        assigned_lab.state = 'results'
        assigned_lab.save()

        messages.success(request, "Lab result added successfully.")

        # Handle AJAX requests
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'success', 'message': 'Lab result added successfully'})

        return redirect('sanatorium.nurses:assigned_labs_detail', pk=assigned_lab.id)

    except Exception as e:
        messages.error(request, f"Error adding lab result: {str(e)}")

        # Handle AJAX requests
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
        print('Exception occured!')
        return redirect('sanatorium.nurses:assigned_labs_detail', pk=assigned_lab.id)


@nurse_required
def view_lab_results(request, assigned_lab_id):
    """
    View to display all results for a specific assigned lab.
    """
    assigned_lab = get_object_or_404(AssignedLabs, id=assigned_lab_id)
    lab_results = AssignedLabResult.objects.filter(assigned_lab=assigned_lab)

    context = {
        'assigned_lab': assigned_lab,
        'lab_results': lab_results,
    }
    return render(request, 'sanatorium/nurses/prescriptions/labs/view_lab_results.html', context)


