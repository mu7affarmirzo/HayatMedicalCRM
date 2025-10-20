from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from django.utils import timezone
from django.http import JsonResponse
from django.db import transaction

from HayatMedicalCRM.auth.decorators import nurse_required
from core.models import AccountTransferModel, AccountTransferItemsModel

@nurse_required
def account_transfer_list(request):
    """
    View to display a list of all transfers assigned to the current nurse
    """
    # Get filter parameters
    state = request.GET.get('state')

    # Base queryset - only show transfers for the current nurse
    transfers = AccountTransferModel.objects.filter(receiver=request.user).order_by('-created_at')

    # Apply filters
    if state:
        transfers = transfers.filter(state=state)

    # Pagination
    paginator = Paginator(transfers, 20)  # Show 20 transfers per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'transfers': page_obj,
        'selected_state': state,
        'states': AccountTransferModel.STATE_CHOICES,
    }

    return render(request, 'sanatorium/nurses/account_transfers/account_transfer_list.html', context)

@nurse_required
def account_transfer_detail(request, pk):
    """
    View to display details of a specific account transfer
    """
    transfer = get_object_or_404(AccountTransferModel, pk=pk, receiver=request.user)
    transfer_items = transfer.transfer_items.all()

    context = {
        'transfer': transfer,
        'transfer_items': transfer_items,
        'states': AccountTransferModel.STATE_CHOICES,
    }

    return render(request, 'sanatorium/nurses/account_transfers/account_transfer_detail.html', context)

@nurse_required
def account_transfer_update_state(request, pk):
    """
    View to update the state of an account transfer (accept or reject)
    """
    transfer = get_object_or_404(AccountTransferModel, pk=pk, receiver=request.user)

    # Only allow updating if the transfer is in pending state
    if transfer.state != 'в ожидании':
        messages.error(request, 'Нельзя изменить статус перемещения, которое не находится в состоянии "в ожидании".')
        return redirect('sanatorium.nurses:account_transfer_detail', pk=transfer.id)

    if request.method == 'POST':
        new_state = request.POST.get('state')

        # Nurses can only accept or reject transfers
        if new_state in ['принято', 'отказано']:
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

    return redirect('sanatorium.nurses:account_transfer_detail', pk=transfer.id)

@nurse_required
def account_transfer_return(request, pk):
    """
    View to return unused medications to the warehouse
    """
    transfer = get_object_or_404(AccountTransferModel, pk=pk, receiver=request.user)

    # Only allow returning if the transfer is in accepted state
    if transfer.state != 'принято':
        messages.error(request, 'Нельзя вернуть перемещение, которое не находится в состоянии "принято".')
        return redirect('sanatorium.nurses:account_transfer_detail', pk=transfer.id)

    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Update the transfer state
                transfer.state = 'возвращено'
                transfer.modified_by = request.user
                transfer.save()

                # Process each item
                for item_id, data in request.POST.items():
                    if item_id.startswith('returned_quantity_'):
                        item_pk = item_id.replace('returned_quantity_', '')
                        returned_quantity = int(data or 0)
                        
                        unit_item_id = f'returned_unit_quantity_{item_pk}'
                        returned_unit_quantity = int(request.POST.get(unit_item_id, 0) or 0)
                        
                        if returned_quantity > 0 or returned_unit_quantity > 0:
                            item = get_object_or_404(AccountTransferItemsModel, pk=item_pk, transfer=transfer)
                            
                            # Validate return quantities
                            total_units = (item.quantity * item.item.item.in_pack) + item.unit_quantity
                            used_units = (item.used_quantity * item.item.item.in_pack) + item.used_unit_quantity
                            available_units = total_units - used_units
                            
                            return_units = (returned_quantity * item.item.item.in_pack) + returned_unit_quantity
                            
                            if return_units > available_units:
                                raise ValueError(f'Нельзя вернуть больше, чем доступно для {item.item.item.name}')
                            
                            # Update the item
                            item.returned_quantity = returned_quantity
                            item.returned_unit_quantity = returned_unit_quantity
                            item.save()

                messages.success(request, 'Перемещение успешно возвращено в склад.')

            # The signal handler will update the stock

        except ValueError as e:
            messages.error(request, str(e))
        except Exception as e:
            messages.error(request, f'Ошибка при возврате перемещения: {str(e)}')

    return redirect('sanatorium.nurses:account_transfer_detail', pk=transfer.id)

@nurse_required
def account_transfer_usage(request, pk):
    """
    View to record medication usage
    """
    transfer = get_object_or_404(AccountTransferModel, pk=pk, receiver=request.user)

    # Only allow recording usage if the transfer is in accepted state
    if transfer.state != 'принято':
        messages.error(request, 'Нельзя записать использование для перемещения, которое не находится в состоянии "принято".')
        return redirect('sanatorium.nurses:account_transfer_detail', pk=transfer.id)

    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Process each item
                for item_id, data in request.POST.items():
                    if item_id.startswith('used_quantity_'):
                        item_pk = item_id.replace('used_quantity_', '')
                        used_quantity = int(data or 0)
                        
                        unit_item_id = f'used_unit_quantity_{item_pk}'
                        used_unit_quantity = int(request.POST.get(unit_item_id, 0) or 0)
                        
                        if used_quantity > 0 or used_unit_quantity > 0:
                            item = get_object_or_404(AccountTransferItemsModel, pk=item_pk, transfer=transfer)
                            
                            # Validate usage quantities
                            total_units = (item.quantity * item.item.item.in_pack) + item.unit_quantity
                            current_used_units = (item.used_quantity * item.item.item.in_pack) + item.used_unit_quantity
                            current_returned_units = (item.returned_quantity * item.item.item.in_pack) + item.returned_unit_quantity
                            available_units = total_units - current_used_units - current_returned_units
                            
                            new_used_units = (used_quantity * item.item.item.in_pack) + used_unit_quantity
                            
                            if new_used_units > available_units:
                                raise ValueError(f'Нельзя использовать больше, чем доступно для {item.item.item.name}')
                            
                            # Update the item
                            item.used_quantity = item.used_quantity + used_quantity
                            item.used_unit_quantity = item.used_unit_quantity + used_unit_quantity
                            item.save()

                messages.success(request, 'Использование медикаментов успешно записано.')

        except ValueError as e:
            messages.error(request, str(e))
        except Exception as e:
            messages.error(request, f'Ошибка при записи использования: {str(e)}')

    return redirect('sanatorium.nurses:account_transfer_detail', pk=transfer.id)