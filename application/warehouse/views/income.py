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
    View to create a new income record with items.
    Supports bidirectional price calculation: users can provide either price or unit_price,
    and the system will automatically calculate the missing value.
    """
    if request.method == 'POST':
        # Get form data
        receiver_id = request.POST.get('receiver')
        delivery_company_id = request.POST.get('delivery_company')
        bill_amount = int(request.POST.get('bill_amount', 0)) if request.POST.get('bill_amount') else 0
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
                # Process item data with bidirectional price calculation
                total_bill_amount = 0
                processed_items = []

                for i in range(len(item_ids)):
                    if not item_ids[i] or not quantities[i]:
                        continue  # Skip empty rows

                    # Get medication item
                    item = MedicationModel.objects.get(id=item_ids[i])

                    # Parse quantities
                    quantity = int(quantities[i]) if quantities[i] else 0
                    unit_quantity = int(unit_quantities[i]) if unit_quantities[i] else 0

                    # Parse prices (treat 0, None, and empty string as "not provided")
                    price = int(prices[i]) if prices[i] and int(prices[i]) > 0 else 0
                    unit_price = int(unit_prices[i]) if unit_prices[i] and int(unit_prices[i]) > 0 else 0

                    # Parse other fields
                    nds = int(nds_values[i]) if nds_values[i] else 0
                    expire_date = expire_dates[i] if expire_dates[i] else None

                    # Step 1: Calculate total units
                    # total_units = (full packs × units per pack) + loose units
                    total_units = (quantity * item.in_pack) + unit_quantity

                    # Validation: Skip items with zero total units
                    if total_units == 0:
                        messages.warning(
                            request,
                            f'Предупреждение: {item.name} имеет нулевое количество и был пропущен.'
                        )
                        continue

                    # Step 2: Bidirectional Price Calculation

                    # Case 1: Both price and unit_price are provided (> 0)
                    if price > 0 and unit_price > 0:
                        # Use provided values as-is (trust user input)
                        pass

                    # Case 2: Only unit_price is provided (Forward Calculation)
                    elif unit_price > 0 and price == 0:
                        # Calculate: price = unit_price × total_units
                        price = unit_price * total_units

                    # Case 3: Only price is provided (Reverse Calculation)
                    elif price > 0 and unit_price == 0:
                        # Calculate: unit_price = price ÷ total_units (integer division)
                        unit_price = price // total_units

                    # Case 4: Neither price nor unit_price provided
                    else:
                        messages.error(
                            request,
                            f'Ошибка: Для {item.name} необходимо указать цену или цену за единицу.'
                        )
                        continue

                    # Step 3: Calculate contribution to bill_amount
                    # Always use unit_price × total_units for consistency
                    item_total = unit_price * total_units
                    total_bill_amount += item_total

                    # Store processed item data
                    processed_items.append({
                        'item_id': item_ids[i],
                        'item_name': item.name,  # For debugging/logging
                        'quantity': quantity,
                        'unit_quantity': unit_quantity,
                        'price': price,
                        'unit_price': unit_price,
                        'nds': nds,
                        'expire_date': expire_date,
                        'total_units': total_units,  # Store for reference
                        'item_total': item_total  # Store for debugging
                    })

                # Validation: Ensure at least one item was processed
                if not processed_items:
                    messages.error(request, 'Ошибка: Необходимо добавить хотя бы один товар с корректными данными.')
                    raise ValueError('No valid items to process')

                # Step 4: Determine final bill_amount
                # Use manual bill_amount if provided (> 0), otherwise use calculated total
                if bill_amount <= 0:
                    bill_amount = total_bill_amount

                # Step 5: Create income record
                income = IncomeModel.objects.create(
                    receiver_id=receiver_id,
                    delivery_company_id=delivery_company_id if delivery_company_id else None,
                    bill_amount=bill_amount,
                    state=state,
                    created_by=request.user,
                    modified_by=request.user
                )

                # Step 6: Create income items
                for item_data in processed_items:
                    IncomeItemsModel.objects.create(
                        income=income,
                        item_id=item_data['item_id'],
                        quantity=item_data['quantity'],
                        unit_quantity=item_data['unit_quantity'],
                        price=item_data['price'],
                        unit_price=item_data['unit_price'],
                        nds=item_data['nds'],
                        expire_date=item_data['expire_date'],
                        created_by=request.user,
                        modified_by=request.user
                    )

                # Success message
                messages.success(request, f'Поступление "{income.serial}" успешно создано!')
                return redirect('warehouse:income_detail', pk=income.id)

        except MedicationModel.DoesNotExist:
            messages.error(request, 'Ошибка: Один или несколько товаров не найдены в системе.')
        except ValueError as e:
            messages.error(request, f'Ошибка валидации: {str(e)}')
        except Exception as e:
            messages.error(request, f'Ошибка при создании поступления: {str(e)}')

    # GET request - prepare form data
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
        bill_amount = int(request.POST.get('bill_amount', 0)) if request.POST.get('bill_amount') else 0
        state = request.POST.get('state', 'принято')
        serial = request.POST.get('serial')

        try:
            with transaction.atomic():
                # Store the old serial for updating related records
                old_serial = income.serial

                # Update income record
                income.receiver_id = receiver_id
                income.delivery_company_id = delivery_company_id if delivery_company_id else None
                income.bill_amount = bill_amount
                income.state = state
                if serial:
                    income.serial = serial
                income.modified_by = request.user
                income.save()

                # If serial was changed, update related MedicationsInStockModel records
                if serial and old_serial != income.serial:
                    from core.models import MedicationsInStockModel
                    MedicationsInStockModel.objects.filter(income_seria=old_serial).update(income_seria=income.serial)

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
