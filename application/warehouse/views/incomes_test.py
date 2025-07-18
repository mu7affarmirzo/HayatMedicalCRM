import json
import uuid
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.db import transaction
from django.core.exceptions import ValidationError
from datetime import datetime


# Import your models here
from core.models import IncomeModel, IncomeItemsModel, CompanyModel, Warehouse, MedicationModel


@login_required
def create_income(request):
    """
    Create new income registry with multiple items
    """
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Get form data
                delivery_company_id = request.POST.get('delivery_company')
                receiver_id = request.POST.get('receiver')
                bill_amount = request.POST.get('bill_amount') or 0
                state = request.POST.get('state', 'принято')

                # Create income record
                income = IncomeModel.objects.create(
                    serial=str(uuid.uuid4()),
                    delivery_company_id=delivery_company_id if delivery_company_id else None,
                    receiver_id=receiver_id,
                    bill_amount=int(bill_amount),
                    state=state,
                    created_by=request.user
                )

                # Get items data from form
                items_data = json.loads(request.POST.get('items_data', '[]'))

                if not items_data:
                    raise ValidationError("Необходимо добавить хотя бы один товар")

                # Create income items
                for item_data in items_data:
                    IncomeItemsModel.objects.create(
                        income=income,
                        item_id=item_data['item_id'],
                        price=int(item_data.get('price', 0)),
                        unit_price=int(item_data.get('unit_price', 0)),
                        nds=int(item_data.get('nds', 0)),
                        overall_price=int(item_data.get('overall_price', 0)),
                        quantity=int(item_data['quantity']),
                        unit_quantity=int(item_data.get('unit_quantity', 0)),
                        expire_date=datetime.strptime(item_data['expire_date'], '%Y-%m-%d').date() if item_data.get(
                            'expire_date') else None,
                        created_by=request.user
                    )

                messages.success(request, f'Реестр прихода {income.serial} успешно создан!')
                return redirect('income_detail', income_id=income.id)

        except Exception as e:
            messages.error(request, f'Ошибка при создании реестра: {str(e)}')

    # Get context data for form
    context = {
        'companies': CompanyModel.objects.all(),
        'warehouses': Warehouse.objects.all(),
        'medications': MedicationModel.objects.all(),
        'state_choices': IncomeModel.STATE_CHOICES,
    }

    return render(request, 'warehouse/income/income_create.html', context)


@login_required
@require_POST
@csrf_exempt
def search_medication_by_qr(request):
    """
    Search medication by QR code
    """
    try:
        qr_code = request.POST.get('qr_code')

        if not qr_code:
            return JsonResponse({'error': 'QR код не предоставлен'}, status=400)

        # Try to find medication by QR code
        # Adjust this logic based on how QR codes are stored in your system
        try:
            medication = MedicationModel.objects.get(qr_code=qr_code)
        except MedicationModel.DoesNotExist:
            # If no direct QR field, try to find by barcode or other identifier
            try:
                medication = MedicationModel.objects.get(barcode=qr_code)
            except MedicationModel.DoesNotExist:
                return JsonResponse({'error': 'Товар с таким QR кодом не найден'}, status=404)

        return JsonResponse({
            'id': medication.id,
            'name': medication.name,
            'unit': getattr(medication, 'unit', 'шт'),
            'price': getattr(medication, 'price', 0),
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def get_medication_info(request, medication_id):
    """
    Get medication information by ID
    """
    try:
        medication = MedicationModel.objects.get(id=medication_id)
        return JsonResponse({
            'id': medication.id,
            'name': medication.name,
            'unit': getattr(medication, 'unit', 'шт'),
            'price': getattr(medication, 'price', 0),
        })
    except MedicationModel.DoesNotExist:
        return JsonResponse({'error': 'Товар не найден'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)