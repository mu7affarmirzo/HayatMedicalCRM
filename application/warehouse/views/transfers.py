import json
from django.shortcuts import render, redirect, get_object_or_404
from HayatMedicalCRM.auth.decorators import warehouse_manager_required
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from django.http import JsonResponse
from django.core.paginator import Paginator

from core.models import Warehouse, TransferModel, TransferItemsModel, MedicationsInStockModel, MedicationModel

@warehouse_manager_required
def transfer_list(request):
    """
    View to display a list of all transfers between warehouses
    """
    # Get filter parameters
    sender_id = request.GET.get('sender')
    receiver_id = request.GET.get('receiver')
    state = request.GET.get('state')

    # Base queryset
    transfers = TransferModel.objects.all().order_by('-created_at')

    # Apply filters
    if sender_id:
        transfers = transfers.filter(sender_id=sender_id)
    if receiver_id:
        transfers = transfers.filter(receiver_id=receiver_id)
    if state:
        transfers = transfers.filter(state=state)

    # Pagination
    paginator = Paginator(transfers, 20)  # Show 20 transfers per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'transfers': page_obj,
        'warehouses': Warehouse.objects.all(),
        'selected_sender': sender_id,
        'selected_receiver': receiver_id,
        'selected_state': state,
        'states': TransferModel.STATE_CHOICES,
        # For notifications
        'expiring_soon_count': MedicationsInStockModel.objects.filter(
            expire_date__lte=timezone.now().date() + timezone.timedelta(days=90),
            expire_date__gt=timezone.now().date()
        ).count(),
        'low_stock_count': MedicationsInStockModel.objects.filter(quantity__lt=10).count(),
    }

    return render(request, 'warehouse/transfers/transfer_list.html', context)

@warehouse_manager_required
def transfer_detail(request, pk):
    """
    View to display details of a specific transfer
    """
    transfer = get_object_or_404(TransferModel, pk=pk)
    transfer_items = transfer.transfer_items.all()

    context = {
        'transfer': transfer,
        'transfer_items': transfer_items,
        'states': TransferModel.STATE_CHOICES,
        # For notifications
        'expiring_soon_count': MedicationsInStockModel.objects.filter(
            expire_date__lte=timezone.now().date() + timezone.timedelta(days=90),
            expire_date__gt=timezone.now().date()
        ).count(),
        'low_stock_count': MedicationsInStockModel.objects.filter(quantity__lt=10).count(),
    }

    return render(request, 'warehouse/transfers/transfer_detail.html', context)

@warehouse_manager_required
def transfer_create(request):
    """
    View to create a new transfer between warehouses
    """
    if request.method == 'POST':
        sender_id = request.POST.get('sender')
        receiver_id = request.POST.get('receiver')
        notes = request.POST.get('notes')

        # Validate sender and receiver
        if sender_id == receiver_id:
            messages.error(request, 'Склад-отправитель и склад-получатель должны быть разными.')
            return redirect('warehouse:transfer_create')

        try:
            with transaction.atomic():
                # Create the transfer
                transfer = TransferModel.objects.create(
                    sender_id=sender_id,
                    receiver_id=receiver_id,
                    state='в ожидании',
                    notes=notes,
                    created_by=request.user,
                    modified_by=request.user
                )

                messages.success(request, f'Перемещение {transfer.serial} успешно создано. Добавьте товары для перемещения.')
                return redirect('warehouse:transfer_add_items', pk=transfer.id)

        except Exception as e:
            messages.error(request, f'Ошибка при создании перемещения: {str(e)}')

    context = {
        'warehouses': Warehouse.objects.all(),
        # For notifications
        'expiring_soon_count': MedicationsInStockModel.objects.filter(
            expire_date__lte=timezone.now().date() + timezone.timedelta(days=90),
            expire_date__gt=timezone.now().date()
        ).count(),
        'low_stock_count': MedicationsInStockModel.objects.filter(quantity__lt=10).count(),
    }

    return render(request, 'warehouse/transfers/transfer_form.html', context)

@warehouse_manager_required
def transfer_add_items(request, pk):
    """
    View to add items to a transfer
    """
    transfer = get_object_or_404(TransferModel, pk=pk)

    # Only allow adding items if the transfer is in pending state
    if transfer.state != 'в ожидании':
        messages.error(request, 'Нельзя добавлять товары в перемещение, которое не находится в состоянии "в ожидании".')
        return redirect('warehouse:transfer_detail', pk=transfer.id)

    if request.method == 'POST':
        item_id = request.POST.get('item')
        quantity = int(request.POST.get('quantity', 0))
        unit_quantity = int(request.POST.get('unit_quantity', 0))
        income_seria = request.POST.get('batch')

        try:
            # Get the stock item
            stock_item = MedicationsInStockModel.objects.get(
                item_id=item_id,
                warehouse=transfer.sender,
                income_seria=income_seria
            )

            # Calculate total units
            medication = stock_item.item
            requested_total_units = (quantity * medication.in_pack) + unit_quantity
            available_total_units = (stock_item.quantity * medication.in_pack) + stock_item.unit_quantity

            if requested_total_units > available_total_units:
                messages.error(request, f'Недостаточно запасов. Доступно: {stock_item.quantity} упаковок + {stock_item.unit_quantity} единиц.')
                return redirect('warehouse:transfer_add_items', pk=transfer.id)

            # Create the transfer item
            TransferItemsModel.objects.create(
                transfer=transfer,
                item=stock_item,
                quantity=quantity,
                unit_quantity=unit_quantity,
                price=stock_item.price,
                unit_price=stock_item.unit_price,
                expire_date=stock_item.expire_date,
                income_seria=income_seria,
                created_by=request.user,
                modified_by=request.user
            )

            messages.success(request, f'Товар успешно добавлен в перемещение.')

        except MedicationsInStockModel.DoesNotExist:
            messages.error(request, 'Выбранная партия товара не найдена.')
        except Exception as e:
            messages.error(request, f'Ошибка при добавлении товара: {str(e)}')

    # Get available medications in the sender warehouse
    available_medications = MedicationsInStockModel.objects.filter(
        warehouse=transfer.sender,
        quantity__gt=0
    ).values_list('item', flat=True).distinct()

    medications = MedicationModel.objects.filter(id__in=available_medications)

    context = {
        'transfer': transfer,
        'transfer_items': transfer.transfer_items.all(),
        'medications': medications,
        # For notifications
        'expiring_soon_count': MedicationsInStockModel.objects.filter(
            expire_date__lte=timezone.now().date() + timezone.timedelta(days=90),
            expire_date__gt=timezone.now().date()
        ).count(),
        'low_stock_count': MedicationsInStockModel.objects.filter(quantity__lt=10).count(),
    }

    return render(request, 'warehouse/transfers/transfer_add_items.html', context)

@warehouse_manager_required
def transfer_update_state(request, pk):
    """
    View to update the state of a transfer
    """
    transfer = get_object_or_404(TransferModel, pk=pk)

    if request.method == 'POST':
        new_state = request.POST.get('state')

        if new_state in dict(TransferModel.STATE_CHOICES):
            try:
                transfer.state = new_state
                transfer.modified_by = request.user
                transfer.save()

                messages.success(request, f'Статус перемещения изменен на "{new_state}".')

                # If the transfer is accepted, the signal handler will update the stock

            except Exception as e:
                messages.error(request, f'Ошибка при обновлении статуса: {str(e)}')
        else:
            messages.error(request, 'Неверный статус.')

    return redirect('warehouse:transfer_detail', pk=transfer.id)

@warehouse_manager_required
def get_medication_batches(request):
    """
    AJAX endpoint to get batches for a specific medication in a warehouse
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

@warehouse_manager_required
def remove_transfer_item(request, pk, item_pk):
    """
    View to remove an item from a transfer
    """
    transfer = get_object_or_404(TransferModel, pk=pk)
    transfer_item = get_object_or_404(TransferItemsModel, pk=item_pk, transfer=transfer)

    # Only allow removing items if the transfer is in pending state
    if transfer.state != 'в ожидании':
        messages.error(request, 'Нельзя удалять товары из перемещения, которое не находится в состоянии "в ожидании".')
        return redirect('warehouse:transfer_detail', pk=transfer.id)

    try:
        transfer_item.delete()
        messages.success(request, 'Товар успешно удален из перемещения.')
    except Exception as e:
        messages.error(request, f'Ошибка при удалении товара: {str(e)}')

    return redirect('warehouse:transfer_add_items', pk=transfer.id)
