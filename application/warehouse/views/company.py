from datetime import timedelta

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Count, Sum, Q
from django.utils import timezone

from core.models import CompanyModel, MedicationModel, IncomeModel, MedicationsInStockModel
from ..forms.company_form import CompanyForm  # You'll need to create this form


@login_required
def company_list(request):
    """
    Display a list of all companies with search and filtering capabilities.
    """
    # Get all companies
    companies = CompanyModel.objects.all().order_by('name')

    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        companies = companies.filter(name__icontains=search_query)

    # Add statistics to each company
    for company in companies:
        # Count medications from this company
        company.medication_count = MedicationModel.objects.filter(company=company).count()

        # Count income records with this company
        company.income_count = IncomeModel.objects.filter(delivery_company=company).count()

        # Calculate total in-stock value from this company
        stocks = MedicationsInStockModel.objects.filter(item__company=company)
        company.stock_value = 0

        for stock in stocks:
            company.stock_value += (stock.quantity * stock.price) + (stock.unit_quantity * stock.unit_price)

    # Pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(companies, 10)  # Show 10 companies per page

    try:
        companies = paginator.page(page)
    except PageNotAnInteger:
        companies = paginator.page(1)
    except EmptyPage:
        companies = paginator.page(paginator.num_pages)

    context = {
        'companies': companies,
        'search_query': search_query,
        'total_companies': CompanyModel.objects.count(),
    }

    return render(request, 'warehouse/company/company_list.html', context)


@login_required
def company_detail(request, pk):
    """
    View company details including associated medications and income records.
    """
    company = get_object_or_404(CompanyModel, pk=pk)

    # Get medications from this company
    medications = MedicationModel.objects.filter(company=company).order_by('name')

    # Get income records with this company
    incomes = IncomeModel.objects.filter(delivery_company=company).order_by('-created_at')

    # Stock information
    stocks = MedicationsInStockModel.objects.filter(item__company=company)
    total_stock_value = 0

    for stock in stocks:
        total_stock_value += (stock.quantity * stock.price) + (stock.unit_quantity * stock.unit_price)

    # Calculate recent activity (last 30 days)
    thirty_days_ago = timezone.now() - timedelta(days=30)
    recent_incomes = incomes.filter(created_at__gte=thirty_days_ago)
    recent_income_value = sum(income.overall_sum for income in recent_incomes)

    context = {
        'company': company,
        'medications': medications,
        'medication_count': medications.count(),
        'incomes': incomes[:10],  # Show only 10 most recent income records
        'income_count': incomes.count(),
        'total_stock_value': total_stock_value,
        'recent_income_value': recent_income_value,
        'recent_income_count': recent_incomes.count(),
    }

    return render(request, 'warehouse/company/company_detail.html', context)


@login_required
def company_create(request):
    """
    Create a new company.
    """
    if request.method == 'POST':
        form = CompanyForm(request.POST)
        if form.is_valid():
            company = form.save(commit=False)
            company.created_by = request.user
            company.modified_by = request.user
            company.save()

            messages.success(request, f'Компания "{company.name}" успешно создана.')
            return redirect('warehouse:company_detail', pk=company.pk)
    else:
        form = CompanyForm()

    context = {
        'form': form,
        'title': 'Создать новую компанию',
        'submit_text': 'Создать',
    }

    return render(request, 'warehouse/company/company_form.html', context)


@login_required
def company_update(request, pk):
    """
    Update an existing company.
    """
    company = get_object_or_404(CompanyModel, pk=pk)

    if request.method == 'POST':
        form = CompanyForm(request.POST, instance=company)
        if form.is_valid():
            # Update the modified_by field
            company = form.save(commit=False)
            company.modified_by = request.user
            company.save()

            messages.success(request, f'Компания "{company.name}" успешно обновлена.')
            return redirect('warehouse:company_detail', pk=company.pk)
    else:
        form = CompanyForm(instance=company)

    context = {
        'form': form,
        'company': company,
        'title': f'Редактировать компанию: {company.name}',
        'submit_text': 'Сохранить изменения',
    }

    return render(request, 'warehouse/company/company_form.html', context)