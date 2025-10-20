from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.db import transaction

from HayatMedicalCRM.auth.decorators import warehouse_manager_required
from core.models.warehouse.income_registry import IncomeModel, IncomeItemsModel
from core.models import MedicationModel, Warehouse, DeliveryCompanyModel

@warehouse_manager_required
def income_list(request):
    """
    View to display list of all income records with filtering and sorting options
    """
    # Base queryset
    incomes = IncomeModel.objects.all().order_by('-created_at')

    # Filter parameters
    serial = request.GET.get('serial')
    company_id = request.GET.get('company')
    warehouse_id = request.GET.get('warehouse')
    state = request.GET.get('state')

    # Apply filters
    if serial:
        incomes = incomes.filter(serial__icontains=serial)

    if company_id:
        incomes = incomes.filter(delivery_company_id=company_id)

    if warehouse_id:
        incomes = incomes.filter(receiver_id=warehouse_id)

    if state:
        incomes = incomes.filter(state=state)

    # Pagination
    paginator = Paginator(incomes, 10)  # Show 10 incomes per page
    page = request.GET.get('page')
    incomes_page = paginator.get_page(page)

    # Get context data
    companies = DeliveryCompanyModel.objects.all()
    warehouses = Warehouse.objects.all()
    state_choices = IncomeModel.STATE_CHOICES

    context = {
        'incomes': incomes_page,
        'companies': companies,
        'warehouses': warehouses,
        'state_choices': state_choices,
    }

    return render(request, 'warehouse/income/income_list.html', context)


@warehouse_manager_required
def income_detail(request, pk):
    """
    View to display details of a specific income record and its items
    """
    income = get_object_or_404(IncomeModel, pk=pk)

    # Get items for this income
    items = IncomeItemsModel.objects.filter(income=income).order_by('item__name')

    context = {
        'income': income,
        'items': items,
        'overall_sum': income.overall_sum,
    }

    return render(request, 'warehouse/income/income_detail.html', context)


@warehouse_manager_required
def income_create(request):
    """
    View to create a new income record with items
    """
    if request.method == 'POST':
        # Get form data
        receiver_id = request.POST.get('receiver')
        delivery_company_id = request.POST.get('delivery_company')
        bill_amount = request.POST.get('bill_amount', 0)
        state = request.POST.get('state', 'принято')

        # Get item data from form
        item_ids = request.POST.getlist('item_id')
        quantities = request.POST.getlist('quantity')
        unit_quantities = request.POST.getlist('unit_quantity')
        prices = request.POST.getlist('price')
        unit_prices = request.POST.getlist('unit_price')
        nds_values = request.POST.getlist('nds')
        expire_dates = request.POST.getlist('expire_date')

        try:
            with transaction.atomic():
                # Create income record
                income = IncomeModel.objects.create(
                    receiver_id=receiver_id,
                    delivery_company_id=delivery_company_id if delivery_company_id else None,
                    bill_amount=bill_amount,
                    state=state,
                    created_by=request.user,
                    modified_by=request.user
                )

                # Create income items
                for i in range(len(item_ids)):
                    if item_ids[i] and quantities[i]:
                        IncomeItemsModel.objects.create(
                            income=income,
                            item_id=item_ids[i],
                            quantity=quantities[i],
                            unit_quantity=unit_quantities[i] if unit_quantities[i] else 0,
                            price=prices[i] if prices[i] else 0,
                            unit_price=unit_prices[i] if unit_prices[i] else 0,
                            nds=nds_values[i] if nds_values[i] else 0,
                            expire_date=expire_dates[i] if expire_dates[i] else None,
                            created_by=request.user,
                            modified_by=request.user
                        )

                messages.success(request, f'Поступление "{income.serial}" успешно создано!')
                return redirect('warehouse:income_detail', pk=income.id)

        except Exception as e:
            messages.error(request, f'Ошибка при создании поступления: {str(e)}')
    
    # Get data for form
    warehouses = Warehouse.objects.all()
    companies = DeliveryCompanyModel.objects.all()
    medications = MedicationModel.objects.filter(is_active=True).order_by('name')
    state_choices = IncomeModel.STATE_CHOICES

    context = {
        'warehouses': warehouses,
        'companies': companies,
        'medications': medications,
        'state_choices': state_choices,
        'is_update': False,
    }

    return render(request, 'warehouse/income/income_form.html', context)


@warehouse_manager_required
def income_update(request, pk):
    """
    View to update an existing income record
    """
    income = get_object_or_404(IncomeModel, pk=pk)
    
    if request.method == 'POST':
        # Get form data
        receiver_id = request.POST.get('receiver')
        delivery_company_id = request.POST.get('delivery_company')
        bill_amount = request.POST.get('bill_amount', 0)
        state = request.POST.get('state', 'принято')

        try:
            with transaction.atomic():
                # Update income record
                income.receiver_id = receiver_id
                income.delivery_company_id = delivery_company_id if delivery_company_id else None
                income.bill_amount = bill_amount
                income.state = state
                income.modified_by = request.user
                income.save()

                messages.success(request, f'Поступление "{income.serial}" успешно обновлено!')
                return redirect('warehouse:income_detail', pk=income.id)

        except Exception as e:
            messages.error(request, f'Ошибка при обновлении поступления: {str(e)}')
    
    # Get data for form
    warehouses = Warehouse.objects.all()
    companies = DeliveryCompanyModel.objects.all()
    state_choices = IncomeModel.STATE_CHOICES

    context = {
        'income': income,
        'warehouses': warehouses,
        'companies': companies,
        'state_choices': state_choices,
        'is_update': True,
    }

    return render(request, 'warehouse/income/income_form.html', context)


@warehouse_manager_required
def income_delete(request, pk):
    """
    View to delete an income record
    """
    income = get_object_or_404(IncomeModel, pk=pk)
    
    if request.method == 'POST':
        try:
            serial = income.serial
            income.delete()
            messages.success(request, f'Поступление "{serial}" успешно удалено!')
            return redirect('warehouse:income_list')
        except Exception as e:
            messages.error(request, f'Ошибка при удалении поступления: {str(e)}')
            return redirect('warehouse:income_detail', pk=income.id)
    
    context = {
        'income': income,
    }
    
    return render(request, 'warehouse/income/income_confirm_delete.html', context)