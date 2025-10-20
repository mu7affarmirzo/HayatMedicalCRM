from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.forms import formset_factory, modelformset_factory
from django.db import transaction
from django.utils import timezone
from django.core.paginator import Paginator

from HayatMedicalCRM.auth.decorators import warehouse_manager_required
from core.models import IncomeModel, IncomeItemsModel, MedicationModel, Warehouse, MedicationsInStockModel, CompanyModel
from ..forms.income_forms import IncomeForm, IncomeItemForm, IncomeItemFormSet


@warehouse_manager_required
def income_list(request):
    """
    View to display list of all income receipts with filtering and sorting options
    """
    # Base queryset
    incomes = IncomeModel.objects.all().order_by('-created_at')

    # Filter parameters
    state = request.GET.get('state')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    warehouse_id = request.GET.get('warehouse')
    company_id = request.GET.get('company')

    # Apply filters
    if state:
        incomes = incomes.filter(state=state)

    if date_from:
        incomes = incomes.filter(created_at__gte=date_from)

    if date_to:
        incomes = incomes.filter(created_at__lte=date_to)

    if warehouse_id:
        incomes = incomes.filter(receiver_id=warehouse_id)

    if company_id:
        incomes = incomes.filter(delivery_company_id=company_id)

    # Pagination
    paginator = Paginator(incomes, 10)  # Show 10 incomes per page
    page = request.GET.get('page')
    incomes_page = paginator.get_page(page)

    # Get context data
    warehouses = Warehouse.objects.all()
    companies = CompanyModel.objects.all()

    context = {
        'incomes': incomes_page,
        'warehouses': warehouses,
        'companies': companies,
        'states': [state[0] for state in IncomeModel.STATE_CHOICES],
        # For notifications
        'expiring_soon_count': MedicationsInStockModel.objects.filter(
            expire_date__lte=timezone.now().date() + timezone.timedelta(days=90),
            expire_date__gt=timezone.now().date()
        ).count(),
        'low_stock_count': MedicationsInStockModel.objects.filter(quantity__lt=10).count(),
    }

    return render(request, 'warehouse/income/income_list.html', context)


@warehouse_manager_required
def income_detail(request, pk):
    """
    View to display details of a specific income receipt
    """
    income = get_object_or_404(IncomeModel, pk=pk)
    items = income.income_items.all()

    context = {
        'income': income,
        'items': items,
        # For notifications
        'expiring_soon_count': MedicationsInStockModel.objects.filter(
            expire_date__lte=timezone.now().date() + timezone.timedelta(days=90),
            expire_date__gt=timezone.now().date()
        ).count(),
        'low_stock_count': MedicationsInStockModel.objects.filter(quantity__lt=10).count(),
    }

    return render(request, 'warehouse/income/income_detail.html', context)


@warehouse_manager_required
def income_create(request):
    """
    View to create a new income receipt with items
    """
    # Create a formset for income items
    IncomeItemFormSet = formset_factory(IncomeItemForm, extra=1)

    if request.method == 'POST':
        income_form = IncomeForm(request.POST)
        item_formset = IncomeItemFormSet(request.POST, prefix='items')

        if income_form.is_valid() and item_formset.is_valid():
            try:
                with transaction.atomic():
                    # Save income
                    income = income_form.save(commit=False)
                    income.created_by = request.user
                    income.modified_by = request.user
                    income.save()

                    # Process item formset
                    for item_form in item_formset:
                        if item_form.cleaned_data and not item_form.cleaned_data.get('DELETE', False):
                            item = item_form.save(commit=False)
                            item.income = income
                            item.created_by = request.user
                            item.modified_by = request.user

                            # Calculate overall price
                            quantity = item.quantity
                            unit_quantity = item.unit_quantity if item.unit_quantity else 0
                            price = item.price if item.price else 0
                            unit_price = item.unit_price if item.unit_price else 0

                            total_units = (quantity * item.item.in_pack) + unit_quantity
                            total_price = (quantity * price) + (unit_quantity * unit_price)

                            item.overall_price = total_price
                            item.save()

                            # If income is accepted, update the stock
                            if income.state == 'принято':
                                # Try to find existing item in stock
                                try:
                                    stock_item = MedicationsInStockModel.objects.get(
                                        item=item.item,
                                        warehouse=income.receiver,
                                        expire_date=item.expire_date,
                                        income_seria=income.serial
                                    )
                                    # Update existing stock
                                    stock_item.quantity += quantity
                                    stock_item.unit_quantity += unit_quantity
                                    stock_item.price = price
                                    stock_item.unit_price = unit_price
                                    stock_item.save()
                                except MedicationsInStockModel.DoesNotExist:
                                    # Create new stock entry
                                    MedicationsInStockModel.objects.create(
                                        item=item.item,
                                        warehouse=income.receiver,
                                        expire_date=item.expire_date,
                                        quantity=quantity,
                                        unit_quantity=unit_quantity,
                                        price=price,
                                        unit_price=unit_price,
                                        income_seria=income.serial,
                                        created_by=request.user,
                                        modified_by=request.user
                                    )

                messages.success(request, f'Поступление №{income.serial} успешно создано!')
                return redirect('warehouse:income_detail', pk=income.id)

            except Exception as e:
                messages.error(request, f'Ошибка при создании поступления: {str(e)}')
        else:
            messages.error(request, 'Пожалуйста, исправьте ошибки в форме.')
    else:
        income_form = IncomeForm()
        item_formset = IncomeItemFormSet(prefix='items')

    # Get context data
    medications = MedicationModel.objects.all()
    warehouses = Warehouse.objects.all()
    companies = CompanyModel.objects.all()

    context = {
        'income_form': income_form,
        'item_formset': item_formset,
        'medications': medications,
        'warehouses': warehouses,
        'companies': companies,
        # For notifications
        'expiring_soon_count': MedicationsInStockModel.objects.filter(
            expire_date__lte=timezone.now().date() + timezone.timedelta(days=90),
            expire_date__gt=timezone.now().date()
        ).count(),
        'low_stock_count': MedicationsInStockModel.objects.filter(quantity__lt=10).count(),
    }

    return render(request, 'warehouse/income/income_form.html', context)


@warehouse_manager_required
def income_update(request, pk):
    """
    View to update an existing income receipt
    """
    income = get_object_or_404(IncomeModel, pk=pk)

    # Only pending incomes can be edited
    if income.state != 'в ожидании':
        messages.error(request, 'Только поступления в статусе "в ожидании" могут быть отредактированы!')
        return redirect('warehouse:income_detail', pk=income.id)

    # Create a formset for income items
    IncomeItemModelFormSet = modelformset_factory(
        IncomeItemsModel,
        form=IncomeItemForm,
        extra=1,
        can_delete=True
    )

    if request.method == 'POST':
        income_form = IncomeForm(request.POST, instance=income)
        item_formset = IncomeItemModelFormSet(
            request.POST,
            queryset=IncomeItemsModel.objects.filter(income=income),
            prefix='items'
        )

        if income_form.is_valid() and item_formset.is_valid():
            try:
                with transaction.atomic():
                    # Save income
                    income = income_form.save(commit=False)
                    income.modified_by = request.user
                    income.save()

                    # Process item formset
                    items = item_formset.save(commit=False)
                    for item in items:
                        if not item.income_id:
                            item.income = income
                        item.created_by = request.user
                        item.modified_by = request.user

                        # Calculate overall price
                        quantity = item.quantity
                        unit_quantity = item.unit_quantity if item.unit_quantity else 0
                        price = item.price if item.price else 0
                        unit_price = item.unit_price if item.unit_price else 0

                        total_price = (quantity * price) + (unit_quantity * unit_price)
                        item.overall_price = total_price

                        item.save()

                    # Handle deleted items
                    for obj in item_formset.deleted_objects:
                        obj.delete()

                messages.success(request, f'Поступление №{income.serial} успешно обновлено!')
                return redirect('warehouse:income_detail', pk=income.id)

            except Exception as e:
                messages.error(request, f'Ошибка при обновлении поступления: {str(e)}')
        else:
            messages.error(request, 'Пожалуйста, исправьте ошибки в форме.')
    else:
        income_form = IncomeForm(instance=income)
        item_formset = IncomeItemModelFormSet(
            queryset=IncomeItemsModel.objects.filter(income=income),
            prefix='items'
        )

    # Get context data
    medications = MedicationModel.objects.all()
    warehouses = Warehouse.objects.all()
    companies = CompanyModel.objects.all()

    context = {
        'income_form': income_form,
        'item_formset': item_formset,
        'medications': medications,
        'warehouses': warehouses,
        'companies': companies,
        'income': income,
        'is_update': True,
        # For notifications
        'expiring_soon_count': MedicationsInStockModel.objects.filter(
            expire_date__lte=timezone.now().date() + timezone.timedelta(days=90),
            expire_date__gt=timezone.now().date()
        ).count(),
        'low_stock_count': MedicationsInStockModel.objects.filter(quantity__lt=10).count(),
    }

    return render(request, 'warehouse/income/income_form.html', context)


@warehouse_manager_required
def income_accept(request, pk):
    """
    View to accept a pending income receipt and update stock
    """
    income = get_object_or_404(IncomeModel, pk=pk)

    if income.state != 'в ожидании':
        messages.error(request, 'Только поступления в статусе "в ожидании" могут быть приняты!')
        return redirect('warehouse:income_detail', pk=income.id)

    try:
        with transaction.atomic():
            # Update income state
            income.state = 'принято'
            income.modified_by = request.user
            income.save()

            # Add items to stock
            for item in income.income_items.all():
                # Try to find existing item in stock
                try:
                    stock_item = MedicationsInStockModel.objects.get(
                        item=item.item,
                        warehouse=income.receiver,
                        expire_date=item.expire_date,
                        income_seria=income.serial
                    )
                    # Update existing stock
                    stock_item.quantity = item.quantity
                    stock_item.unit_quantity = item.unit_quantity or 0
                    stock_item.price = item.price or 0
                    stock_item.unit_price = item.unit_price or 0
                    stock_item.save()
                except MedicationsInStockModel.DoesNotExist:
                    # Create new stock entry
                    MedicationsInStockModel.objects.create(
                        item=item.item,
                        warehouse=income.receiver,
                        expire_date=item.expire_date,
                        quantity=item.quantity,
                        unit_quantity=item.unit_quantity or 0,
                        price=item.price or 0,
                        unit_price=item.unit_price or 0,
                        income_seria=income.serial,
                        created_by=request.user,
                        modified_by=request.user
                    )

        messages.success(request, f'Поступление №{income.serial} успешно принято!')
    except Exception as e:
        messages.error(request, f'Ошибка при принятии поступления: {str(e)}')

    return redirect('warehouse:income_detail', pk=income.id)


@warehouse_manager_required
def income_reject(request, pk):
    """
    View to reject a pending income receipt
    """
    income = get_object_or_404(IncomeModel, pk=pk)

    if income.state != 'в ожидании':
        messages.error(request, 'Только поступления в статусе "в ожидании" могут быть отклонены!')
        return redirect('warehouse:income_detail', pk=income.id)

    try:
        # Update income state
        income.state = 'отказано'
        income.modified_by = request.user
        income.save()

        messages.success(request, f'Поступление №{income.serial} отклонено.')
    except Exception as e:
        messages.error(request, f'Ошибка при отклонении поступления: {str(e)}')

    return redirect('warehouse:income_detail', pk=income.id)