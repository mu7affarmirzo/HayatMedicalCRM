# views.py
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse, HttpResponseBadRequest
from django.template.loader import render_to_string
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy, reverse
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import get_object_or_404, redirect

from application.sanatorium.forms.medications_form import PrescribedMedicationForm, MedicationSessionForm

from core.models import PrescribedMedication, MedicationSession, IllnessHistory, MedicationsInStockModel, \
    MedicationModel


# PrescribedMedication Views
class PrescribedMedicationListView(LoginRequiredMixin, ListView):
    model = PrescribedMedication
    template_name = 'sanatorium/nurses/prescriptions/medications/list.html'
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
    template_name = 'sanatorium/nurses/prescriptions/medications/detail.html'
    context_object_name = 'medication'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add administrations to context
        context['sessions'] = self.object.sessions.all().order_by('-created_at')
        context['illness_history'] = self.object.illness_history
        context['history'] = self.object.illness_history
        return context


class PrescribedMedicationCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = PrescribedMedication
    form_class = PrescribedMedicationForm
    template_name = 'sanatorium/nurses/prescriptions/medications/form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user

        # Get illness_history from URL parameter
        illness_history_id = self.kwargs.get('illness_history_id')
        if illness_history_id:
            kwargs['illness_history'] = get_object_or_404(IllnessHistory, pk=illness_history_id)

        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        # Pre-populate illness_history if provided in URL
        illness_history_id = self.request.GET.get('illness_history')
        if illness_history_id:
            initial['illness_history'] = illness_history_id
        return initial

    def form_valid(self, form):
        medication_id = self.request.POST.get('medication')
        if medication_id:
            form.instance.medication_id = medication_id
        else:
            # Handle the case where medication is not provided
            return self.form_invalid(form)

        # Set the prescribed_by field to the current user
        form.instance.illness_history = get_object_or_404(IllnessHistory, pk=self.kwargs.get('illness_history_id'))
        form.instance.prescribed_by = self.request.user
        form.instance.doctor = self.request.user
        form.instance.created_by = self.request.user
        form.instance.modified_by = self.request.user

        # Check if user is the assigned doctor
        if form.instance.illness_history.doctor == self.request.user:
            form.instance.state = 'assigned'  # or whatever state indicates direct assignment
        else:
            form.instance.state = 'recommended'

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
    template_name = 'sanatorium/nurses/prescriptions/medications/form.html'
    context_object_name = 'medication'

    def form_valid(self, form):
        # Set the last_modified_by field to the current user
        form.instance.last_modified_by = self.request.user
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['history'] = get_object_or_404(IllnessHistory, pk=self.kwargs.get('illness_history_id'))
        return context

    def get_success_url(self):
        return reverse_lazy('prescribed_medication_detail', kwargs={'pk': self.object.id})


class PrescribedMedicationDeleteView(LoginRequiredMixin, SuccessMessageMixin, DeleteView):
    model = PrescribedMedication
    template_name = 'sanatorium/nurses/prescriptions/medications/confirm_delete.html'
    context_object_name = 'medication'

    def get_success_url(self):
        # Redirect to illness history detail if available
        if self.object.illness_history:
            return reverse_lazy('illness_history_detail', kwargs={'pk': self.object.illness_history.id})
        return reverse_lazy('prescribed_medication_list')


# MedicationSession Views
class MedicationSessionListView(LoginRequiredMixin, ListView):
    model = MedicationSession
    template_name = 'sanatorium/nurses/prescriptions/medications/list.html'
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


class MedicationSessionDetailView(LoginRequiredMixin, DetailView):
    model = MedicationSession
    template_name = 'sanatorium/nurses/prescriptions/medications/detail.html'
    context_object_name = 'administration'


class MedicationSessionCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = MedicationSession
    form_class = MedicationSessionForm
    template_name = 'sanatorium/nurses/prescriptions/medications/form.html'

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


class MedicationSessionUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = MedicationSession
    form_class = MedicationSessionForm
    template_name = 'sanatorium/nurses/prescriptions/medications/form.html'
    context_object_name = 'administration'

    def form_valid(self, form):
        # Set the modified_by field to the current user
        form.instance.modified_by = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('medication_administration_detail', kwargs={'pk': self.object.id})


class MedicationSessionDeleteView(LoginRequiredMixin, SuccessMessageMixin, DeleteView):
    model = MedicationSession
    template_name = 'sanatorium/nurses/prescriptions/medications/confirm_delete.html'
    context_object_name = 'administration'

    def get_success_url(self):
        return reverse_lazy('prescribed_medication_detail',
                            kwargs={'pk': self.object.prescribed_medication.id})


@login_required
def api_medications_search(request):
    """
    AJAX endpoint для поиска медикаментов с фильтрацией и пагинацией.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Метод не поддерживается'}, status=405)

    # Получаем параметры из запроса
    draw = int(request.POST.get('draw', 1))
    start = int(request.POST.get('start', 0))
    length = int(request.POST.get('length', 10))
    search_term = request.POST.get('search_term', '')
    category = request.POST.get('category', '')
    stock_status = request.POST.get('stock_status', '')
    active_ingredient = request.POST.get('active_ingredient', '')
    form = request.POST.get('form', '')
    manufacturer = request.POST.get('manufacturer', '')

    # Базовый запрос с предзагрузкой связанных данных
    query = MedicationsInStockModel.objects.select_related('item', 'warehouse').filter(warehouse__is_main=True)
    # Фильтрация по поисковому запросу
    if search_term:
        # Используем более простой поиск без вложенных полей
        query = query.filter(
            Q(item__name__icontains=search_term)
        )
        # query = query.filter(
        #     Q(item__name__icontains=search_term) |
        #     Q(income_seria__icontains=search_term)
        # )
        print(query)

    # Применяем фильтры
    if category:
        query = query.filter(item__category=category)

    if stock_status:
        if stock_status == 'in-stock':
            query = query.filter(Q(quantity__gt=0) | Q(unit_quantity__gt=0))
        elif stock_status == 'low-stock':
            # Предполагаем, что "заканчивается" означает менее 10 упаковок или есть только единицы
            query = query.filter(
                (Q(quantity__gt=0) & Q(quantity__lte=10)) |
                (Q(quantity=0) & Q(unit_quantity__gt=0))
            )
        elif stock_status == 'out-of-stock':
            query = query.filter(quantity=0, unit_quantity=0)

    if active_ingredient:
        # Вместо вложенного поиска используем простое сравнение ID
        query = query.filter(item__active_ingredient=active_ingredient)

    if form:
        query = query.filter(item__form=form)

    if manufacturer:
        query = query.filter(item__manufacturer=manufacturer)

    # Получаем общее количество записей и отфильтрованных записей
    total_records = MedicationsInStockModel.objects.count()
    total_filtered = query.count()

    # Сортировка и пагинация
    query = query.order_by('expire_date', 'item__name')[start:start + length]

    # Формируем результат
    data = []
    for medication in query:
        # Определяем статус наличия
        if medication.quantity > 10:
            stock_status = 'in-stock'
        elif medication.quantity > 0 or medication.unit_quantity > 0:
            stock_status = 'low-stock'
        else:
            stock_status = 'out-of-stock'

        # Получаем безопасные данные о препарате
        item_name = str(medication.item) if medication.item else "Не указан"

        # Предполагаем, что у item есть атрибуты form, active_ingredient, dosage и manufacturer
        # Но обращаемся к ним безопасно
        try:
            form_display = medication.item.form if hasattr(medication.item, 'form') else "Не указана"
        except:
            form_display = "Не указана"

        try:
            active_ingredient = medication.item.active_ingredient if hasattr(medication.item,
                                                                             'active_ingredient') else "Не указано"
        except:
            active_ingredient = "Не указано"

        try:
            dosage = medication.item.dosage if hasattr(medication.item, 'dosage') else "Не указана"
        except:
            dosage = "Не указана"

        try:
            manufacturer = medication.company if hasattr(medication.item, 'manufacturer') else "Не указан"
        except:
            manufacturer = "Не указан"

        # Форматируем срок годности
        days_left = medication.days_until_expire
        expire_date_str = medication.expire_date.strftime('%d.%m.%Y') if medication.expire_date else "Не указан"
        expiry_indicator = ""
        if days_left < 0:
            expiry_indicator = " <span class='badge badge-danger'>Просрочен</span>"
        elif days_left < 30:
            expiry_indicator = f" <span class='badge badge-warning'>Осталось {days_left} дн.</span>"

        data.append({
            'id': medication.id,
            'name': item_name,
            'form': str(form_display),
            'active_ingredient': str(active_ingredient),
            'dosage': str(dosage),
            'manufacturer': str(manufacturer),
            'stock_status': stock_status,
            'quantity': f"{medication.quantity} уп." + (
                f" {medication.unit_quantity} шт." if medication.unit_quantity > 0 else ""),
            'warehouse': medication.warehouse.name if medication.warehouse else "Не указан",
            'expire_date': expire_date_str + expiry_indicator
        })

    return JsonResponse({
        'draw': draw,
        'recordsTotal': total_records,
        'recordsFiltered': total_filtered,
        'data': data
    })



@login_required
@require_POST
def update_session_status(request, session_id):
    """Update the status of a medication session"""
    session = get_object_or_404(MedicationSession, id=session_id)

    # Only pending sessions can be updated
    if session.status != 'pending':
        return redirect(reverse('nurses:prescribed_medication_detail', args=[session.prescribed_medication.id]))

    # Get form data
    new_status = request.POST.get('status')
    notes = request.POST.get('notes', '')

    # Validate status
    valid_statuses = ['administered', 'missed', 'refused', 'canceled']
    if new_status not in valid_statuses:
        return HttpResponseBadRequest("Недопустимый статус")

    # Update session
    session.status = new_status
    session.notes = notes

    # Additional actions based on status
    if new_status == 'administered':
        # Get administered_at from form or use current time
        administered_at_str = request.POST.get('administered_at')
        if administered_at_str:
            try:
                # Parse datetime string, convert to timezone aware
                administered_at = timezone.datetime.fromisoformat(administered_at_str.replace('Z', '+00:00'))
                if timezone.is_naive(administered_at):
                    administered_at = timezone.make_aware(administered_at)
                session.administered_at = administered_at
            except (ValueError, TypeError):
                # If parsing fails, use current time
                session.administered_at = timezone.now()
        else:
            # If not provided, use current time
            session.administered_at = timezone.now()

        # Set administered_by to current user
        session.administered_by = request.user

    elif new_status == 'missed':
        session.administered_at = timezone.now()
        session.administered_by = request.user

    elif new_status == 'refused':
        session.administered_at = timezone.now()
        session.administered_by = request.user

    # Save changes
    session.save()

    # Redirect back to the medication detail page
    return redirect(reverse('nurses:prescribed_medication_detail', args=[session.prescribed_medication.id]))


@login_required
def api_medication_details(request):
    """
    AJAX endpoint для получения детальной информации о медикаменте.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Метод не поддерживается'}, status=405)

    medication_id = request.POST.get('medication_id')

    try:
        medication = MedicationsInStockModel.objects.select_related('item', 'warehouse').get(id=medication_id)

        # Формируем данные для шаблона
        context = {
            'medication': medication,
            # Добавляем безопасные свойства
            'item_name': str(medication.item) if medication.item else "Не указан",
            'form': str(medication.item.form) if hasattr(medication.item,
                                                         'form') and medication.item.form else "Не указана",
            'active_ingredient': str(medication.item.active_ingredient) if hasattr(medication.item,
                                                                                   'active_ingredient') and medication.item.active_ingredient else "Не указано",
            'dosage': str(medication.item.dosage) if hasattr(medication.item, 'dosage') else "Не указана",
            'manufacturer': str(medication.company) if hasattr(medication.item,
                                                                         'manufacturer') and medication.company else "Не указан",
            'days_left': medication.days_until_expire
        }

        try:
            # Формируем HTML для отображения в модальном окне
            html = render_to_string('sanatorium/nurses/prescriptions/medications/medication_details.html', context)
        except:
            html = None

        # Формируем краткую информацию для отображения в форме
        info = f"{context['form']}, {context['active_ingredient']}, {context['dosage']}"

        return JsonResponse({
            'html': html,
            'name': context['item_name'],
            'info': info
        })
    except MedicationsInStockModel.DoesNotExist:
        return JsonResponse({'error': 'Медикамент не найден'}, status=404)


@login_required
@require_POST
def administer_medication(request, session_id):
    """Directly mark a medication session as administered"""
    session = get_object_or_404(MedicationSession, id=session_id)

    # Only pending sessions can be administered
    if session.status != 'pending':
        return redirect(reverse('nurses:prescribed_medication_detail', args=[session.prescribed_medication.id]))

    # Update session
    session.status = 'administered'
    session.administered_at = timezone.now()
    session.administered_by = request.user
    session.notes = request.POST.get('notes', '')
    session.save()

    # Redirect back to the medication detail page
    return redirect(reverse('nurses:prescribed_medication_detail', args=[session.prescribed_medication.id]))


@login_required
@require_POST
def mark_missed(request, session_id):
    """Mark a medication session as missed"""
    session = get_object_or_404(MedicationSession, id=session_id)
    if session.status != 'pending':
        return redirect(reverse('nurses:prescribed_medication_detail', args=[session.prescribed_medication.id]))

    session.status = 'missed'
    session.administered_at = timezone.now()
    session.administered_by = request.user
    session.notes = request.POST.get('notes', '')
    session.save()

    return redirect(reverse('nurses:prescribed_medication_detail', args=[session.prescribed_medication.id]))


@login_required
@require_POST
def mark_refused(request, session_id):
    """Mark a medication session as refused by patient"""
    session = get_object_or_404(MedicationSession, id=session_id)
    if session.status != 'pending':
        return redirect(reverse('nurses:prescribed_medication_detail', args=[session.prescribed_medication.id]))

    session.status = 'refused'
    session.administered_at = timezone.now()
    session.administered_by = request.user
    session.notes = request.POST.get('notes', '')
    session.save()

    return redirect(reverse('nurses:prescribed_medication_detail', args=[session.prescribed_medication.id]))