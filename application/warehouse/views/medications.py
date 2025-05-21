from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.core.paginator import Paginator
from core.models import MedicationModel, Warehouse, MedicationsInStockModel, CompanyModel
from ..forms.medications_form import MedicationForm


@login_required
def medication_list(request):
    """
    View to display list of all medications with filtering and sorting options
    """
    # Base queryset
    medications = MedicationModel.objects.all().order_by('name')

    # Filter parameters
    name = request.GET.get('name')
    company_id = request.GET.get('company')
    unit = request.GET.get('unit')
    is_active = request.GET.get('is_active')

    # Apply filters
    if name:
        medications = medications.filter(name__icontains=name)

    if company_id:
        medications = medications.filter(company_id=company_id)

    if unit:
        medications = medications.filter(unit=unit)

    if is_active is not None:
        is_active_bool = is_active.lower() == 'true'
        medications = medications.filter(is_active=is_active_bool)

    # Pagination
    paginator = Paginator(medications, 10)  # Show 10 medications per page
    page = request.GET.get('page')
    medications_page = paginator.get_page(page)

    # Get context data
    companies = CompanyModel.objects.all()
    unit_choices = MedicationModel.UNIT_CHOICES

    context = {
        'medications': medications_page,
        'companies': companies,
        'unit_choices': unit_choices,
        # For notifications
        'expiring_soon_count': MedicationsInStockModel.objects.filter(
            expire_date__lte=timezone.now().date() + timezone.timedelta(days=90),
            expire_date__gt=timezone.now().date()
        ).count(),
        'low_stock_count': MedicationsInStockModel.objects.filter(quantity__lt=10).count(),
    }

    return render(request, 'warehouse/medications/medication_list.html', context)


@login_required
def medication_detail(request, pk):
    """
    View to display details of a specific medication and its stock information
    """
    medication = get_object_or_404(MedicationModel, pk=pk)

    # Get stock information for this medication
    stock_items = MedicationsInStockModel.objects.filter(item=medication).order_by('expire_date')

    # Calculate total stock quantity
    total_packs = sum(item.quantity for item in stock_items)
    total_units = sum(item.unit_quantity for item in stock_items)

    # Group stock by warehouse
    warehouse_stock = {}
    for item in stock_items:
        warehouse_id = item.warehouse.id
        if warehouse_id not in warehouse_stock:
            warehouse_stock[warehouse_id] = {
                'warehouse': item.warehouse,
                'total_packs': 0,
                'total_units': 0,
                'items': []
            }

        warehouse_stock[warehouse_id]['total_packs'] += item.quantity
        warehouse_stock[warehouse_id]['total_units'] += item.unit_quantity
        warehouse_stock[warehouse_id]['items'].append(item)

    context = {
        'medication': medication,
        'stock_items': stock_items,
        'total_packs': total_packs,
        'total_units': total_units,
        'warehouse_stock': warehouse_stock.values(),
        # For notifications
        'expiring_soon_count': MedicationsInStockModel.objects.filter(
            expire_date__lte=timezone.now().date() + timezone.timedelta(days=90),
            expire_date__gt=timezone.now().date()
        ).count(),
        'low_stock_count': MedicationsInStockModel.objects.filter(quantity__lt=10).count(),
    }

    return render(request, 'warehouse/medications/medication_detail.html', context)


@login_required
def medication_create(request):
    """
    View to create a new medication
    """
    if request.method == 'POST':
        form = MedicationForm(request.POST)
        if form.is_valid():
            try:
                medication = form.save(commit=False)
                medication.created_by = request.user
                medication.modified_by = request.user
                medication.save()

                messages.success(request, f'Лекарство "{medication.name}" успешно создано!')
                return redirect('warehouse:medication_detail', pk=medication.id)

            except Exception as e:
                messages.error(request, f'Ошибка при создании лекарства: {str(e)}')
        else:
            messages.error(request, 'Пожалуйста, исправьте ошибки в форме.')
    else:
        form = MedicationForm()

    context = {
        'form': form,
        'is_update': False,
        # For notifications
        'expiring_soon_count': MedicationsInStockModel.objects.filter(
            expire_date__lte=timezone.now().date() + timezone.timedelta(days=90),
            expire_date__gt=timezone.now().date()
        ).count(),
        'low_stock_count': MedicationsInStockModel.objects.filter(quantity__lt=10).count(),
    }

    return render(request, 'warehouse/medications/medication_form.html', context)


@login_required
def medication_update(request, pk):
    """
    View to update an existing medication
    """
    medication = get_object_or_404(MedicationModel, pk=pk)

    if request.method == 'POST':
        form = MedicationForm(request.POST, instance=medication)
        if form.is_valid():
            try:
                medication = form.save(commit=False)
                medication.modified_by = request.user
                medication.save()

                messages.success(request, f'Лекарство "{medication.name}" успешно обновлено!')
                return redirect('warehouse:medication_detail', pk=medication.id)

            except Exception as e:
                messages.error(request, f'Ошибка при обновлении лекарства: {str(e)}')
        else:
            messages.error(request, 'Пожалуйста, исправьте ошибки в форме.')
    else:
        form = MedicationForm(instance=medication)

    context = {
        'form': form,
        'medication': medication,
        'is_update': True,
        # For notifications
        'expiring_soon_count': MedicationsInStockModel.objects.filter(
            expire_date__lte=timezone.now().date() + timezone.timedelta(days=90),
            expire_date__gt=timezone.now().date()
        ).count(),
        'low_stock_count': MedicationsInStockModel.objects.filter(quantity__lt=10).count(),
    }

    return render(request, 'warehouse/medications/medication_form.html', context)


@login_required
def expiring_medications(request):
    """
    View to display medications that will expire soon
    """
    # Default to 90 days for expiring soon
    days = int(request.GET.get('days', 90))

    # Filter parameters
    warehouse_id = request.GET.get('warehouse')

    # Calculate the target date
    target_date = timezone.now().date() + timezone.timedelta(days=days)

    # Get all medications that will expire within the specified days
    stock_items = MedicationsInStockModel.objects.filter(
        expire_date__lte=target_date,
        expire_date__gt=timezone.now().date()
    ).order_by('expire_date')

    # Apply warehouse filter if specified
    if warehouse_id:
        stock_items = stock_items.filter(warehouse_id=warehouse_id)

    # Categorize by expiry urgency
    expiring_critical = stock_items.filter(expire_date__lte=timezone.now().date() + timezone.timedelta(days=30))
    expiring_warning = stock_items.filter(
        expire_date__gt=timezone.now().date() + timezone.timedelta(days=30),
        expire_date__lte=timezone.now().date() + timezone.timedelta(days=60)
    )
    expiring_notice = stock_items.filter(
        expire_date__gt=timezone.now().date() + timezone.timedelta(days=60),
        expire_date__lte=target_date
    )

    # Get context data
    warehouses = Warehouse.objects.all()

    context = {
        'stock_items': stock_items,
        'warehouses': warehouses,
        'selected_warehouse': warehouse_id,
        'days': days,
        'expiring_critical': expiring_critical,
        'expiring_warning': expiring_warning,
        'expiring_notice': expiring_notice,
        'target_date': target_date,
        # For notifications
        'expiring_soon_count': stock_items.count(),
        'low_stock_count': MedicationsInStockModel.objects.filter(quantity__lt=10).count(),
    }

    return render(request, 'warehouse/medications/expiring_medications.html', context)


@login_required
def low_stock(request):
    """
    View to display medications with low stock levels
    """
    # Default threshold for low stock
    threshold = int(request.GET.get('threshold', 10))

    # Filter parameters
    warehouse_id = request.GET.get('warehouse')

    # Get all medications with stock below threshold
    stock_items = MedicationsInStockModel.objects.filter(quantity__lt=threshold).order_by('quantity')

    # Apply warehouse filter if specified
    if warehouse_id:
        stock_items = stock_items.filter(warehouse_id=warehouse_id)

    # Categorize by stock level urgency
    critical_stock = stock_items.filter(quantity__lt=5)
    low_stock = stock_items.filter(quantity__gte=5, quantity__lt=threshold)

    # Get context data
    warehouses = Warehouse.objects.all()

    context = {
        'stock_items': stock_items,
        'warehouses': warehouses,
        'selected_warehouse': warehouse_id,
        'threshold': threshold,
        'critical_stock': critical_stock,
        'low_stock': low_stock,
        # For notifications
        'expiring_soon_count': MedicationsInStockModel.objects.filter(
            expire_date__lte=timezone.now().date() + timezone.timedelta(days=90),
            expire_date__gt=timezone.now().date()
        ).count(),
        'low_stock_count': stock_items.count(),
    }

    return render(request, 'warehouse/medications/low_stock.html', context)