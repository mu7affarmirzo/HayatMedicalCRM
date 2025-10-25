from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from HayatMedicalCRM.auth.decorators import warehouse_manager_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Count, Sum, Q
from django.utils import timezone
from datetime import timedelta

from core.models import DeliveryCompanyModel, MedicationsInStockModel
from ..forms.delivery_company_form import DeliveryCompanyForm  # You'll need to create this form


@warehouse_manager_required
def delivery_company_list(request):
    """
    Display a list of all delivery companies with search and filtering capabilities.
    """
    # Get all delivery companies
    delivery_companies = DeliveryCompanyModel.objects.all().order_by('name')

    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        delivery_companies = delivery_companies.filter(
            Q(name__icontains=search_query) |
            Q(contact_person__icontains=search_query) |
            Q(phone_number__icontains=search_query) |
            Q(email__icontains=search_query)
        )

    # Add statistics to each company
    for company in delivery_companies:
        # Count medications delivered by this company
        company.medication_count = MedicationsInStockModel.objects.filter(delivery_company=company).count()

        # Calculate total value of medications delivered by this company
        stocks = MedicationsInStockModel.objects.filter(delivery_company=company)
        company.stock_value = 0

        for stock in stocks:
            company.stock_value += (stock.quantity * stock.price) + (stock.unit_quantity * stock.unit_price)

    # Pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(delivery_companies, 10)  # Show 10 companies per page

    try:
        delivery_companies = paginator.page(page)
    except PageNotAnInteger:
        delivery_companies = paginator.page(1)
    except EmptyPage:
        delivery_companies = paginator.page(paginator.num_pages)

    context = {
        'delivery_companies': delivery_companies,
        'search_query': search_query,
        'total_companies': DeliveryCompanyModel.objects.count(),
    }

    return render(request, 'warehouse/delivery_company/delivery_company_list.html', context)


@warehouse_manager_required
def delivery_company_detail(request, pk):
    """
    View delivery company details including associated medications.
    """
    delivery_company = get_object_or_404(DeliveryCompanyModel, pk=pk)

    # Get medications delivered by this company
    medications = MedicationsInStockModel.objects.filter(delivery_company=delivery_company).order_by('-delivery_date')

    # Calculate total value of medications delivered by this company
    total_stock_value = 0
    for stock in medications:
        total_stock_value += (stock.quantity * stock.price) + (stock.unit_quantity * stock.unit_price)

    # Calculate recent activity (last 30 days)
    thirty_days_ago = timezone.now() - timedelta(days=30)
    recent_medications = medications.filter(created_at__gte=thirty_days_ago)
    recent_value = 0
    for stock in recent_medications:
        recent_value += (stock.quantity * stock.price) + (stock.unit_quantity * stock.unit_price)

    context = {
        'delivery_company': delivery_company,
        'medications': medications[:20],  # Show only 20 most recent medications
        'medication_count': medications.count(),
        'total_stock_value': total_stock_value,
        'recent_value': recent_value,
        'recent_count': recent_medications.count(),
        'contract_active': delivery_company.contract_status,
    }

    return render(request, 'warehouse/delivery_company/delivery_company_detail.html', context)


@warehouse_manager_required
def delivery_company_create(request):
    """
    Create a new delivery company.
    """
    if request.method == 'POST':
        form = DeliveryCompanyForm(request.POST)
        if form.is_valid():
            delivery_company = form.save(commit=False)
            delivery_company.created_by = request.user
            delivery_company.modified_by = request.user
            delivery_company.save()

            messages.success(request, f'Компания доставки "{delivery_company.name}" успешно создана.')
            return redirect('warehouse:delivery_company_detail', pk=delivery_company.pk)
    else:
        form = DeliveryCompanyForm()

    context = {
        'form': form,
        'title': 'Создать новую компанию доставки',
        'submit_text': 'Создать',
    }

    return render(request, 'warehouse/delivery_company/delivery_company_form.html', context)


@warehouse_manager_required
def delivery_company_update(request, pk):
    """
    Update an existing delivery company.
    """
    delivery_company = get_object_or_404(DeliveryCompanyModel, pk=pk)

    if request.method == 'POST':
        form = DeliveryCompanyForm(request.POST, instance=delivery_company)
        if form.is_valid():
            # Update the modified_by field
            delivery_company = form.save(commit=False)
            delivery_company.modified_by = request.user
            delivery_company.save()

            messages.success(request, f'Компания доставки "{delivery_company.name}" успешно обновлена.')
            return redirect('warehouse:delivery_company_detail', pk=delivery_company.pk)
    else:
        form = DeliveryCompanyForm(instance=delivery_company)

    context = {
        'form': form,
        'delivery_company': delivery_company,
        'title': f'Редактировать компанию доставки: {delivery_company.name}',
        'submit_text': 'Сохранить изменения',
    }

    return render(request, 'warehouse/delivery_company/delivery_company_form.html', context)


@warehouse_manager_required
def delivery_company_delete(request, pk):
    """
    Delete a delivery company.
    """
    delivery_company = get_object_or_404(DeliveryCompanyModel, pk=pk)

    if request.method == 'POST':
        name = delivery_company.name
        delivery_company.delete()
        messages.success(request, f'Компания доставки "{name}" успешно удалена.')
        return redirect('warehouse:delivery_company_list')

    context = {
        'delivery_company': delivery_company,
    }

    return render(request, 'warehouse/delivery_company/delivery_company_confirm_delete.html', context)