from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, F, Q
from django.utils import timezone
from datetime import timedelta
from django.core.paginator import Paginator
from core.models import MedicationModel, Warehouse, MedicationsInStockModel, CompanyModel
from ..forms.warehouse_form import WarehouseForm, TransferForm


@login_required
def warehouse_list(request):
    """
    View to display list of all warehouses
    """
    warehouses = Warehouse.objects.all().order_by('-is_main', '-is_emergency', 'name')

    context = {
        'warehouses': warehouses,
        # For notifications
        'expiring_soon_count': MedicationsInStockModel.objects.filter(
            expire_date__lte=timezone.now().date() + timezone.timedelta(days=90),
            expire_date__gt=timezone.now().date()
        ).count(),
        'low_stock_count': MedicationsInStockModel.objects.filter(quantity__lt=10).count(),
    }

    return render(request, 'warehouse/warehouse/warehouse_list.html', context)


@login_required
def warehouse_detail(request, pk):
    """
    View to display details of a specific warehouse and its inventory
    """
    warehouse = get_object_or_404(Warehouse, pk=pk)

    # Get stock information for this warehouse
    stock_items = MedicationsInStockModel.objects.filter(warehouse=warehouse)

    # Group stock by medication
    medication_stock = {}
    for item in stock_items:
        medication_id = item.item.id
        if medication_id not in medication_stock:
            medication_stock[medication_id] = {
                'medication': item.item,
                'total_packs': 0,
                'total_units': 0,
                'batches': []
            }

        medication_stock[medication_id]['total_packs'] += item.quantity
        medication_stock[medication_id]['total_units'] += item.unit_quantity
        medication_stock[medication_id]['batches'].append(item)

    # Calculate some statistics
    total_medications = len(medication_stock)
    total_batches = stock_items.count()
    expiring_soon = stock_items.filter(
        expire_date__lte=timezone.now().date() + timezone.timedelta(days=90),
        expire_date__gt=timezone.now().date()
    ).count()
    low_stock = stock_items.filter(quantity__lt=10).count()

    context = {
        'warehouse': warehouse,
        'medication_stock': medication_stock.values(),
        'total_medications': total_medications,
        'total_batches': total_batches,
        'expiring_soon': expiring_soon,
        'low_stock': low_stock,
        'today': timezone.now().date(),
        # For notifications
        'expiring_soon_count': MedicationsInStockModel.objects.filter(
            expire_date__lte=timezone.now().date() + timezone.timedelta(days=90),
            expire_date__gt=timezone.now().date()
        ).count(),
        'low_stock_count': MedicationsInStockModel.objects.filter(quantity__lt=10).count(),
    }

    return render(request, 'warehouse/warehouse/warehouse_detail.html', context)


@login_required
def warehouse_create(request):
    """
    View to create a new warehouse
    """
    if request.method == 'POST':
        form = WarehouseForm(request.POST)
        if form.is_valid():
            try:
                warehouse = form.save(commit=False)
                warehouse.created_by = request.user
                warehouse.modified_by = request.user
                warehouse.save()

                messages.success(request, f'Склад "{warehouse.name}" успешно создан!')
                return redirect('warehouse:warehouse_detail', pk=warehouse.id)

            except Exception as e:
                messages.error(request, f'Ошибка при создании склада: {str(e)}')
        else:
            messages.error(request, 'Пожалуйста, исправьте ошибки в форме.')
    else:
        form = WarehouseForm()

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

    return render(request, 'warehouse/warehouse/warehouse_form.html', context)


@login_required
def warehouse_update(request, pk):
    """
    View to update an existing warehouse
    """
    warehouse = get_object_or_404(Warehouse, pk=pk)

    if request.method == 'POST':
        form = WarehouseForm(request.POST, instance=warehouse)
        if form.is_valid():
            try:
                warehouse = form.save(commit=False)
                warehouse.modified_by = request.user
                warehouse.save()

                messages.success(request, f'Склад "{warehouse.name}" успешно обновлен!')
                return redirect('warehouse:warehouse_detail', pk=warehouse.id)

            except Exception as e:
                messages.error(request, f'Ошибка при обновлении склада: {str(e)}')
        else:
            messages.error(request, 'Пожалуйста, исправьте ошибки в форме.')
    else:
        form = WarehouseForm(instance=warehouse)

    context = {
        'form': form,
        'warehouse': warehouse,
        'is_update': True,
        # For notifications
        'expiring_soon_count': MedicationsInStockModel.objects.filter(
            expire_date__lte=timezone.now().date() + timezone.timedelta(days=90),
            expire_date__gt=timezone.now().date()
        ).count(),
        'low_stock_count': MedicationsInStockModel.objects.filter(quantity__lt=10).count(),
    }

    return render(request, 'warehouse/warehouse/warehouse_form.html', context)


@login_required
def warehouse_transfer(request):
    """
    View to transfer medications between warehouses
    """
    if request.method == 'POST':
        form = TransferForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    source_warehouse = form.cleaned_data['source_warehouse']
                    destination_warehouse = form.cleaned_data['destination_warehouse']
                    medication = form.cleaned_data['medication']
                    batch = form.cleaned_data['batch']
                    quantity = form.cleaned_data['quantity']
                    unit_quantity = form.cleaned_data['unit_quantity'] or 0
                    notes = form.cleaned_data['notes']

                    # Get source stock item
                    source_stock = MedicationsInStockModel.objects.get(
                        warehouse=source_warehouse,
                        item=medication,
                        income_seria=batch
                    )

                    # Calculate total units to transfer
                    transfer_total_units = (quantity * medication.in_pack) + unit_quantity
                    source_total_units = (source_stock.quantity * medication.in_pack) + source_stock.unit_quantity

                    if transfer_total_units > source_total_units:
                        messages.error(request, 'Недостаточно запасов для перемещения.')
                        return redirect('warehouse:warehouse_transfer')

                    # Deduct from source
                    remaining_units = source_total_units - transfer_total_units
                    source_stock.quantity = remaining_units // medication.in_pack
                    source_stock.unit_quantity = remaining_units % medication.in_pack
                    source_stock.modified_by = request.user
                    source_stock.save()

                    # Add to destination
                    try:
                        dest_stock = MedicationsInStockModel.objects.get(
                            warehouse=destination_warehouse,
                            item=medication,
                            income_seria=batch,
                            expire_date=source_stock.expire_date
                        )

                        # Update existing stock at destination
                        dest_total_units = (dest_stock.quantity * medication.in_pack) + dest_stock.unit_quantity
                        new_total_units = dest_total_units + transfer_total_units

                        dest_stock.quantity = new_total_units // medication.in_pack
                        dest_stock.unit_quantity = new_total_units % medication.in_pack
                        dest_stock.modified_by = request.user
                        dest_stock.save()

                    except MedicationsInStockModel.DoesNotExist:
                        # Create new stock item at destination
                        MedicationsInStockModel.objects.create(
                            warehouse=destination_warehouse,
                            item=medication,
                            income_seria=batch,
                            expire_date=source_stock.expire_date,
                            quantity=quantity,
                            unit_quantity=unit_quantity,
                            price=source_stock.price,
                            unit_price=source_stock.unit_price,
                            created_by=request.user,
                            modified_by=request.user
                        )

                    # Create a record of this transfer (in a real system, you might want to have a TransferModel)
                    # For now, just show a success message
                    messages.success(
                        request,
                        f'Успешно перемещено {quantity} упаковок и {unit_quantity} единиц {medication.name} '
                        f'из "{source_warehouse.name}" в "{destination_warehouse.name}".'
                    )

                    # If source is now empty, consider deleting the record
                    if source_stock.quantity == 0 and source_stock.unit_quantity == 0:
                        source_stock.delete()

                    return redirect('warehouse:warehouse_list')

            except MedicationsInStockModel.DoesNotExist:
                messages.error(request, 'Выбранная партия лекарства не найдена.')
            except Exception as e:
                messages.error(request, f'Ошибка при перемещении: {str(e)}')
        else:
            # Form has errors
            pass
    else:
        form = TransferForm()

    context = {
        'form': form,
        # For notifications
        'expiring_soon_count': MedicationsInStockModel.objects.filter(
            expire_date__lte=timezone.now().date() + timezone.timedelta(days=90),
            expire_date__gt=timezone.now().date()
        ).count(),
        'low_stock_count': MedicationsInStockModel.objects.filter(quantity__lt=10).count(),
    }

    return render(request, 'warehouse/warehouse/warehouse_transform.html', context)


# AJAX endpoint to get batches for a specific warehouse and medication
@login_required
def get_batches(request):
    """
    AJAX view to get batches for a specific warehouse and medication
    """
    if request.method == 'GET':
        warehouse_id = request.GET.get('warehouse_id')
        medication_id = request.GET.get('medication_id')

        if warehouse_id and medication_id:
            try:
                batches = MedicationsInStockModel.objects.filter(
                    warehouse_id=warehouse_id,
                    item_id=medication_id,
                    quantity__gt=0
                ).values('income_seria', 'expire_date', 'quantity', 'unit_quantity')

                batch_data = []
                for batch in batches:
                    expire_date = batch['expire_date'].strftime('%d.%m.%Y') if batch['expire_date'] else 'Не указано'
                    label = f"{batch['income_seria']} - Срок годности: {expire_date} - Остаток: {batch['quantity']} уп. + {batch['unit_quantity']} ед."
                    batch_data.append({
                        'id': batch['income_seria'],
                        'text': label,
                        'quantity': batch['quantity'],
                        'unit_quantity': batch['unit_quantity']
                    })

                return JsonResponse({'results': batch_data})
            except Exception as e:
                return JsonResponse({'error': str(e)}, status=400)

        return JsonResponse({'results': []})

    return JsonResponse({'error': 'Invalid request method'}, status=400)


@login_required
def get_medication_info(request):
    """
    AJAX endpoint to get basic information about a medication.

    Expected query parameters:
    - medication_id: ID of the medication to get info for

    Returns JSON object with medication details such as:
    - name: Medication name
    - in_pack: Number of units in a standard package
    - unit: Unit of measurement
    - company: Manufacturer company
    - description: Medication description
    - dosage_form: Form of the medication
    - active_ingredients: List of active ingredients
    - contraindications: List of contraindications
    """
    try:
        medication_id = request.GET.get('medication_id')

        if not medication_id:
            return JsonResponse({'error': 'Medication ID is required'}, status=400)

        # Get the medication
        medication = get_object_or_404(MedicationModel, id=medication_id)

        # Check for stock information
        stock_info = {
            'total_quantity': 0,
            'warehouses': []
        }

        # Get stock information across all warehouses
        stock_items = medication.in_stock.all()

        if stock_items.exists():
            # Count total quantity across all warehouses
            total_units = 0
            warehouses_with_stock = set()

            for stock in stock_items:
                # Only include stocks with positive quantity
                if stock.quantity > 0 or stock.unit_quantity > 0:
                    total_units += (stock.quantity * medication.in_pack + stock.unit_quantity)
                    warehouses_with_stock.add(stock.warehouse.id)

                    # Check if this warehouse is already in our list
                    warehouse_exists = False
                    for wh in stock_info['warehouses']:
                        if wh['id'] == stock.warehouse.id:
                            wh['quantity'] += stock.quantity
                            wh['unit_quantity'] += stock.unit_quantity
                            warehouse_exists = True
                            break

                    # If not, add it
                    if not warehouse_exists:
                        stock_info['warehouses'].append({
                            'id': stock.warehouse.id,
                            'name': stock.warehouse.name,
                            'quantity': stock.quantity,
                            'unit_quantity': stock.unit_quantity
                        })

            # Update total quantity
            stock_info['total_quantity'] = total_units
            stock_info['warehouses_count'] = len(warehouses_with_stock)

        # Prepare medication info
        medication_info = {
            'id': medication.id,
            'name': medication.name,
            'in_pack': medication.in_pack,
            'unit': medication.get_unit_display(),  # Display value for the unit choice field
            'unit_code': medication.unit,  # Actual unit code value
            'company': {
                'id': medication.company.id,
                'name': medication.company.name
            },
            'description': medication.description,
            'dosage_form': medication.dosage_form,
            'active_ingredients': medication.active_ingredients,
            'contraindications': medication.contraindications,
            'batch_number': medication.batch_number,
            'manufacture_date': medication.manufacture_date.isoformat() if medication.manufacture_date else None,
            'expiry_date': medication.expiry_date.isoformat() if medication.expiry_date else None,
            'is_active': medication.is_active,
            'validity_status': medication.validity_status,
            'stock': stock_info
        }

        return JsonResponse(medication_info)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def warehouse_stats(request):
    """
    AJAX endpoint to get warehouse statistics.

    Expected query parameters:
    - warehouse_id: (Optional) ID of the warehouse to get stats for.
      If not provided, returns stats for all warehouses.

    Returns JSON object with warehouse statistics
    """
    try:
        warehouse_id = request.GET.get('warehouse_id')

        # Base query for medications in stock with positive quantity
        query = MedicationsInStockModel.objects.filter(
            Q(quantity__gt=0) | Q(unit_quantity__gt=0)
        )

        if warehouse_id:
            try:
                warehouse = Warehouse.objects.get(id=warehouse_id)
                query = query.filter(warehouse=warehouse)
            except Warehouse.DoesNotExist:
                return JsonResponse({'error': 'Warehouse not found'}, status=404)

        # Calculate statistics
        today = timezone.now().date()
        expiring_soon_date = today + timedelta(days=90)

        # Count total distinct medications
        total_medications = query.values('item').distinct().count()

        # Calculate total inventory value
        inventory_value = query.aggregate(
            pack_value=Sum(F('quantity') * F('price')),
            unit_value=Sum(F('unit_quantity') * F('unit_price'))
        )

        # Sum up the pack and unit values
        total_value = (inventory_value['pack_value'] or 0) + (inventory_value['unit_value'] or 0)

        # Count expiring and expired medications
        expiring_count = query.filter(expire_date__lte=expiring_soon_date, expire_date__gt=today).count()
        expired_count = query.filter(expire_date__lt=today).count()

        # Low stock analysis
        stocked_medications = MedicationModel.objects.filter(
            in_stock__in=query
        ).distinct()

        low_stock_count = 0
        critical_stock_count = 0

        for medication in stocked_medications:
            # Get all stock records for this medication
            med_stocks = query.filter(item=medication)

            # Calculate total units
            total_units = sum(
                stock.quantity * medication.in_pack + stock.unit_quantity
                for stock in med_stocks
            )

            # Define thresholds
            low_threshold = 20  # Less than 20 units is low stock
            critical_threshold = 5  # Less than 5 units is critical

            if total_units <= critical_threshold:
                critical_stock_count += 1
            elif total_units <= low_threshold:
                low_stock_count += 1

        # Warehouse breakdown if no specific warehouse was requested
        warehouses_data = []
        if not warehouse_id:
            warehouses = Warehouse.objects.all()
            for wh in warehouses:
                wh_stocks = query.filter(warehouse=wh)

                # Count distinct medications in this warehouse
                wh_count = wh_stocks.values('item').distinct().count()

                # Calculate total inventory value in this warehouse
                wh_inventory = wh_stocks.aggregate(
                    pack_value=Sum(F('quantity') * F('price')),
                    unit_value=Sum(F('unit_quantity') * F('unit_price'))
                )

                wh_value = (wh_inventory['pack_value'] or 0) + (wh_inventory['unit_value'] or 0)

                # Count expiring items in this warehouse
                wh_expiring = wh_stocks.filter(expire_date__lte=expiring_soon_date, expire_date__gt=today).count()
                wh_expired = wh_stocks.filter(expire_date__lt=today).count()

                warehouses_data.append({
                    'id': wh.id,
                    'name': wh.name,
                    'address': wh.address,
                    'is_main': wh.is_main,
                    'is_emergency': wh.is_emergency,
                    'item_count': wh_count,
                    'total_value': wh_value,
                    'expiring_count': wh_expiring,
                    'expired_count': wh_expired
                })

        # Top companies by value
        top_companies = []
        company_stats = {}

        for stock in query:
            company = stock.item.company
            if company.id not in company_stats:
                company_stats[company.id] = {
                    'id': company.id,
                    'name': company.name,
                    'count': 0,
                    'value': 0
                }

            company_stats[company.id]['count'] += 1
            stock_value = (stock.quantity * stock.price + stock.unit_quantity * stock.unit_price)
            company_stats[company.id]['value'] += stock_value

        # Sort companies by value and get top 5
        top_companies = sorted(
            company_stats.values(),
            key=lambda x: x['value'],
            reverse=True
        )[:5]

        # Prepare response
        stats = {
            'total_medications': total_medications,
            'total_value': total_value,
            'expiring_soon': expiring_count,
            'expired': expired_count,
            'low_stock': low_stock_count,
            'critical_stock': critical_stock_count,
            'warehouses': warehouses_data,
            'top_companies': top_companies
        }

        return JsonResponse(stats)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
