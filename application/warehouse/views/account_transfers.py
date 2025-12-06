import json
from django.shortcuts import render, redirect, get_object_or_404
from HayatMedicalCRM.auth.decorators import warehouse_manager_required
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from django.http import JsonResponse
from django.core.paginator import Paginator

from core.models import Warehouse, AccountTransferModel, AccountTransferItemsModel, MedicationsInStockModel, MedicationModel, Account

@warehouse_manager_required
def account_transfer_list(request):
    """
    View to display a list of all transfers from warehouses to accounts
    """
    # Get filter parameters
    sender_id = request.GET.get('sender')
    receiver_id = request.GET.get('receiver')
    state = request.GET.get('state')

    # Base queryset
    transfers = AccountTransferModel.objects.all().order_by('-created_at')

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
        'accounts': Account.objects.all(),
        'selected_sender': sender_id,
        'selected_receiver': receiver_id,
        'selected_state': state,
        'states': AccountTransferModel.STATE_CHOICES,
        # For notifications
        'expiring_soon_count': MedicationsInStockModel.objects.filter(
            expire_date__lte=timezone.now().date() + timezone.timedelta(days=90),
            expire_date__gt=timezone.now().date()
        ).count(),
        'low_stock_count': MedicationsInStockModel.objects.filter(quantity__lt=10).count(),
    }

    return render(request, 'warehouse/account_transfers/account_transfer_list.html', context)

@warehouse_manager_required
def account_transfer_detail(request, pk):
    """
    View to display details of a specific account transfer
    """
    transfer = get_object_or_404(AccountTransferModel, pk=pk)
    transfer_items = transfer.transfer_items.all()

    context = {
        'transfer': transfer,
        'transfer_items': transfer_items,
        'states': AccountTransferModel.STATE_CHOICES,
        # For notifications
        'expiring_soon_count': MedicationsInStockModel.objects.filter(
            expire_date__lte=timezone.now().date() + timezone.timedelta(days=90),
            expire_date__gt=timezone.now().date()
        ).count(),
        'low_stock_count': MedicationsInStockModel.objects.filter(quantity__lt=10).count(),
    }

    return render(request, 'warehouse/account_transfers/account_transfer_detail.html', context)

@warehouse_manager_required
def account_transfer_create(request):
    """
    View to create a new transfer from warehouse to account
    """
    if request.method == 'POST':
        sender_id = request.POST.get('sender')
        receiver_id = request.POST.get('receiver')
        notes = request.POST.get('notes')
        treatment_period = request.POST.get('treatment_period')
        expected_return_date = request.POST.get('expected_return_date') or None

        try:
            with transaction.atomic():
                # Create the transfer
                transfer = AccountTransferModel.objects.create(
                    sender_id=sender_id,
                    receiver_id=receiver_id,
                    state='в ожидании',
                    notes=notes,
                    treatment_period=treatment_period,
                    expected_return_date=expected_return_date,
                    created_by=request.user,
                    modified_by=request.user
                )

                messages.success(request, f'Перемещение {transfer.serial} успешно создано. Добавьте товары для перемещения.')
                return redirect('warehouse:account_transfer_add_items', pk=transfer.id)

        except Exception as e:
            messages.error(request, f'Ошибка при создании перемещения: {str(e)}')

    context = {
        'warehouses': Warehouse.objects.all(),
        'accounts': Account.objects.all(),
        # For notifications
        'expiring_soon_count': MedicationsInStockModel.objects.filter(
            expire_date__lte=timezone.now().date() + timezone.timedelta(days=90),
            expire_date__gt=timezone.now().date()
        ).count(),
        'low_stock_count': MedicationsInStockModel.objects.filter(quantity__lt=10).count(),
    }

    return render(request, 'warehouse/account_transfers/account_transfer_form.html', context)

@warehouse_manager_required
def account_transfer_add_items(request, pk):
    """
    View to add items to an account transfer
    """
    transfer = get_object_or_404(AccountTransferModel, pk=pk)

    # Only allow adding items if the transfer is in pending state
    if transfer.state != 'в ожидании':
        messages.error(request, 'Нельзя добавлять товары в перемещение, которое не находится в состоянии "в ожидании".')
        return redirect('warehouse:account_transfer_detail', pk=transfer.id)

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

            # Get medication to access in_pack
            medication = stock_item.item

            # Auto-convert unit_quantity to packs + units if needed
            if unit_quantity > 0 or quantity > 0:
                total_units = (quantity * medication.in_pack) + unit_quantity
                quantity = total_units // medication.in_pack
                unit_quantity = total_units % medication.in_pack

            # Calculate total units
            requested_total_units = (quantity * medication.in_pack) + unit_quantity
            available_total_units = (stock_item.quantity * medication.in_pack) + stock_item.unit_quantity

            # Validation: Check if enough stock available
            if requested_total_units > available_total_units:
                messages.error(request, f'Недостаточно запасов. Доступно: {stock_item.quantity} упаковок + {stock_item.unit_quantity} единиц.')
                return redirect('warehouse:account_transfer_add_items', pk=transfer.id)

            if requested_total_units == 0:
                messages.error(request, 'Количество должно быть больше нуля.')
                return redirect('warehouse:account_transfer_add_items', pk=transfer.id)

            # Store stock item data before modification
            stock_price = stock_item.price
            stock_unit_price = stock_item.unit_price
            stock_expire_date = stock_item.expire_date

            # Deduct stock immediately (transfer is in "в ожидании" state)
            remaining_units = available_total_units - requested_total_units

            if remaining_units > 0:
                # Update stock with remaining units
                stock_item.quantity = remaining_units // medication.in_pack
                stock_item.unit_quantity = remaining_units % medication.in_pack
                stock_item.save()
            else:
                # Delete stock item if no units remain
                stock_item.delete()

            # Create the transfer item
            AccountTransferItemsModel.objects.create(
                transfer=transfer,
                item=stock_item,
                quantity=quantity,
                unit_quantity=unit_quantity,
                price=stock_price,
                unit_price=stock_unit_price,
                expire_date=stock_expire_date,
                income_seria=income_seria,
                created_by=request.user,
                modified_by=request.user
            )

            messages.success(request, f'Товар успешно добавлен в перемещение.')

        except MedicationsInStockModel.DoesNotExist:
            messages.error(request, 'Выбранная партия товара не найдена.')
        except Exception as e:
            messages.error(request, f'Ошибка при добавлении товара: {str(e)}')

    # Get available medications in the sender warehouse (with actual stock)
    from django.db.models import Q
    available_medications = MedicationsInStockModel.objects.filter(
        warehouse=transfer.sender
    ).filter(
        Q(quantity__gt=0) | Q(unit_quantity__gt=0)
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

    return render(request, 'warehouse/account_transfers/account_transfer_add_items.html', context)

@warehouse_manager_required
def account_transfer_update_state(request, pk):
    """
    View to update the state of an account transfer
    """
    transfer = get_object_or_404(AccountTransferModel, pk=pk)

    if request.method == 'POST':
        new_state = request.POST.get('state')

        if new_state in dict(AccountTransferModel.STATE_CHOICES):
            try:
                transfer.state = new_state
                transfer.modified_by = request.user
                transfer.save()

                messages.success(request, f'Статус перемещения изменен на "{new_state}".')

                # If the transfer is accepted or returned, the signal handler will update the stock

            except Exception as e:
                messages.error(request, f'Ошибка при обновлении статуса: {str(e)}')
        else:
            messages.error(request, 'Неверный статус.')

    return redirect('warehouse:account_transfer_detail', pk=transfer.id)

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
                from django.db.models import Q
                batches = MedicationsInStockModel.objects.filter(
                    warehouse_id=warehouse_id,
                    item_id=medication_id
                ).filter(
                    Q(quantity__gt=0) | Q(unit_quantity__gt=0)
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
def update_account_transfer_item(request, pk, item_pk):
    """
    View to update an account transfer item (only allowed when transfer is in 'в ожидании' state)
    """
    transfer = get_object_or_404(AccountTransferModel, pk=pk)
    transfer_item = get_object_or_404(AccountTransferItemsModel, pk=item_pk, transfer=transfer)

    # Only allow updating items if the transfer is in pending state
    if transfer.state != 'в ожидании':
        messages.error(request, 'Нельзя изменять товары в перемещении, которое не находится в состоянии "в ожидании".')
        return redirect('warehouse:account_transfer_detail', pk=transfer.id)

    if request.method == 'POST':
        try:
            quantity = int(request.POST.get('quantity', 0))
            unit_quantity = int(request.POST.get('unit_quantity', 0))

            # Validation: quantity must be greater than 0
            if quantity == 0 and unit_quantity == 0:
                messages.error(request, 'Количество должно быть больше нуля.')
                return redirect('warehouse:account_transfer_add_items', pk=transfer.id)

            # Get medication info
            medication = transfer_item.item.item

            # Auto-convert unit_quantity to packs + units if needed
            if unit_quantity > 0 or quantity > 0:
                total_units = (quantity * medication.in_pack) + unit_quantity
                quantity = total_units // medication.in_pack
                unit_quantity = total_units % medication.in_pack

            # Calculate requested total units
            requested_total_units = (quantity * medication.in_pack) + unit_quantity

            # Calculate current item's units (to restore to stock temporarily)
            old_total_units = (transfer_item.quantity * medication.in_pack) + transfer_item.unit_quantity

            # Get current stock in sender warehouse
            sender_stock = MedicationsInStockModel.objects.filter(
                item=medication,
                warehouse=transfer.sender,
                expire_date=transfer_item.expire_date,
                income_seria=transfer_item.income_seria
            ).first()

            # Calculate available units (including current transfer item's units)
            if sender_stock:
                available_units = (sender_stock.quantity * medication.in_pack) + sender_stock.unit_quantity + old_total_units
            else:
                available_units = old_total_units

            # Validation: Check if enough stock available
            if requested_total_units > available_units:
                available_packs = available_units // medication.in_pack
                available_unit_qty = available_units % medication.in_pack
                messages.error(request, f'Недостаточно запасов. Доступно: {available_packs} упаковок + {available_unit_qty} единиц.')
                return redirect('warehouse:account_transfer_add_items', pk=transfer.id)

            # Calculate the difference
            units_difference = old_total_units - requested_total_units

            # Update stock in sender warehouse
            if sender_stock:
                current_stock_units = (sender_stock.quantity * medication.in_pack) + sender_stock.unit_quantity
                new_stock_units = current_stock_units + units_difference

                if new_stock_units > 0:
                    sender_stock.quantity = new_stock_units // medication.in_pack
                    sender_stock.unit_quantity = new_stock_units % medication.in_pack
                    sender_stock.save()
                else:
                    sender_stock.delete()
            elif units_difference > 0:
                # Create new stock if difference is positive
                MedicationsInStockModel.objects.create(
                    item=medication,
                    income_seria=transfer_item.income_seria,
                    quantity=units_difference // medication.in_pack,
                    unit_quantity=units_difference % medication.in_pack,
                    expire_date=transfer_item.expire_date,
                    warehouse=transfer.sender,
                    price=transfer_item.price,
                    unit_price=transfer_item.unit_price,
                )

            # Update the transfer item
            transfer_item.quantity = quantity
            transfer_item.unit_quantity = unit_quantity
            transfer_item.modified_by = request.user
            transfer_item.save()

            messages.success(request, 'Товар успешно обновлен.')

        except Exception as e:
            messages.error(request, f'Ошибка при обновлении товара: {str(e)}')

    return redirect('warehouse:account_transfer_add_items', pk=transfer.id)


@warehouse_manager_required
def remove_account_transfer_item(request, pk, item_pk):
    """
    View to remove an item from an account transfer
    """
    transfer = get_object_or_404(AccountTransferModel, pk=pk)
    transfer_item = get_object_or_404(AccountTransferItemsModel, pk=item_pk, transfer=transfer)

    # Only allow removing items if the transfer is in pending state
    if transfer.state != 'в ожидании':
        messages.error(request, 'Нельзя удалять товары из перемещения, которое не находится в состоянии "в ожидании".')
        return redirect('warehouse:account_transfer_detail', pk=transfer.id)

    try:
        # Restore stock to sender warehouse before deleting
        medication = transfer_item.item.item
        total_units_transfer = (transfer_item.quantity * medication.in_pack) + transfer_item.unit_quantity

        # Try to find existing stock in sender warehouse
        sender_stock = MedicationsInStockModel.objects.filter(
            item=medication,
            warehouse=transfer.sender,
            expire_date=transfer_item.expire_date,
            income_seria=transfer_item.income_seria
        ).first()

        if sender_stock:
            # Add back to existing stock
            total_units_sender = (sender_stock.quantity * medication.in_pack) + sender_stock.unit_quantity
            new_total_units = total_units_sender + total_units_transfer

            sender_stock.quantity = new_total_units // medication.in_pack
            sender_stock.unit_quantity = new_total_units % medication.in_pack
            sender_stock.save()
        else:
            # Recreate stock entry in sender warehouse
            MedicationsInStockModel.objects.create(
                item=medication,
                income_seria=transfer_item.income_seria,
                quantity=transfer_item.quantity,
                unit_quantity=transfer_item.unit_quantity,
                expire_date=transfer_item.expire_date,
                warehouse=transfer.sender,
                price=transfer_item.price,
                unit_price=transfer_item.unit_price,
            )

        transfer_item.delete()
        messages.success(request, 'Товар успешно удален из перемещения.')
    except Exception as e:
        messages.error(request, f'Ошибка при удалении товара: {str(e)}')

    return redirect('warehouse:account_transfer_add_items', pk=transfer.id)