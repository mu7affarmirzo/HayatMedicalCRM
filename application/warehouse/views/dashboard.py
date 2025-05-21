import json
from datetime import timedelta

from django.shortcuts import render
from django.utils import timezone

from core.models import Warehouse, MedicationModel, IncomeModel, MedicationsInStockModel


def warehouse_dashboard(request):
    # Get filter parameters
    warehouse_id = request.GET.get('warehouse')
    date_range = request.GET.get('date_range')

    # Sample data for the charts
    income_months = ['January', 'February', 'March', 'April', 'May', 'June']
    income_counts = [10, 15, 8, 12, 17, 14]

    warehouse_names = ['Main Warehouse', 'Emergency Warehouse', 'Branch 1', 'Branch 2']
    warehouse_stock_counts = [650, 120, 230, 180]

    context = {
        'warehouses': Warehouse.objects.all(),
        'selected_warehouse': warehouse_id,
        'total_medications': MedicationModel.objects.count(),
        'total_income_this_month': IncomeModel.objects.filter(created_at__month=timezone.now().month).count(),
        'expiring_soon_count': MedicationsInStockModel.objects.filter(
            expire_date__lte=timezone.now().date() + timedelta(days=90), expire_date__gt=timezone.now().date()).count(),
        'expired_count': MedicationsInStockModel.objects.filter(expire_date__lt=timezone.now().date()).count(),
        'recent_incomes': IncomeModel.objects.all().order_by('-created_at')[:10],
        'expiring_medications': MedicationsInStockModel.objects.filter(
            expire_date__lte=timezone.now().date() + timedelta(days=90),
            expire_date__gt=timezone.now().date()).order_by('expire_date')[:5],
        'low_stock_items': MedicationsInStockModel.objects.filter(quantity__lt=10).order_by('quantity', 'expire_date')[
                           :10],
        'today': timezone.now().date().strftime('%Y-%m-%d'),
        'income_months': json.dumps(income_months),
        'income_counts': json.dumps(income_counts),
        'warehouse_names': json.dumps(warehouse_names),
        'warehouse_stock_counts': json.dumps(warehouse_stock_counts),
    }

    return render(request, 'warehouse/dashboard.html', context)