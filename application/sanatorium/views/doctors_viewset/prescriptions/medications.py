# views.py
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy, reverse
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import get_object_or_404

from application.sanatorium.forms.medications_form import PrescribedMedicationForm, MedicationAdministrationForm

from core.models import PrescribedMedication, MedicationAdministration, IllnessHistory, MedicationsInStockModel, \
    MedicationModel


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
    template_name = 'sanatorium/doctors/prescriptions/medications/form.html'
    context_object_name = 'medication'

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
            html = render_to_string('sanatorium/doctors/prescriptions/medications/medication_details.html', context)
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