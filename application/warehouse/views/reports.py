from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, F, Q, Count, Value, Case, When, IntegerField, DecimalField
from django.db.models.functions import Coalesce, TruncMonth, TruncYear
from django.utils import timezone
from datetime import datetime, timedelta
import csv
from django.http import HttpResponse

from core.models import MedicationsInStockModel, MedicationModel, Warehouse, IncomeModel, IncomeItemsModel, CompanyModel


@login_required
def stock_report(request):
    """
    Generate a comprehensive report of current stock levels across all warehouses.
    Allows filtering by warehouse, medication name, and low stock items.
    """
    # Get all warehouses for filter dropdown
    warehouses = Warehouse.objects.all()
    selected_warehouse = request.GET.get('warehouse')
    search_query = request.GET.get('search', '')
    low_stock_only = request.GET.get('low_stock') == 'on'
    out_of_stock = request.GET.get('out_of_stock') == 'on'

    # Base query for stock data
    stock_query = MedicationsInStockModel.objects.select_related('item', 'warehouse')

    # Apply filters
    if selected_warehouse:
        stock_query = stock_query.filter(warehouse_id=selected_warehouse)

    if search_query:
        stock_query = stock_query.filter(item__name__icontains=search_query)

    # Group stock data by medication and warehouse
    report_data = []
    warehouses_with_stock = set()
    medications_with_stock = {}

    # Process each stock record
    for stock in stock_query:
        medication = stock.item
        warehouse = stock.warehouse

        # Track which warehouses have stock
        if stock.quantity > 0 or stock.unit_quantity > 0:
            warehouses_with_stock.add(warehouse.id)

        # Calculate total units for this stock item
        total_units = (stock.quantity * medication.in_pack) + stock.unit_quantity

        # For grouping purposes
        med_key = f"{medication.id}-{warehouse.id}"

        if med_key not in medications_with_stock:
            medications_with_stock[med_key] = {
                'medication': medication,
                'warehouse': warehouse,
                'quantity': stock.quantity,
                'unit_quantity': stock.unit_quantity,
                'total_units': total_units,
                'total_value': (stock.quantity * stock.price) + (stock.unit_quantity * stock.unit_price),
                'expires_soon': stock.expire_date and (stock.expire_date - timezone.now().date()).days <= 90,
                'expired': stock.expire_date and stock.expire_date < timezone.now().date(),
                'low_stock': False,  # Will be set after all stock items are processed
            }
        else:
            # Add to existing medication entry for this warehouse
            medications_with_stock[med_key]['quantity'] += stock.quantity
            medications_with_stock[med_key]['unit_quantity'] += stock.unit_quantity
            medications_with_stock[med_key]['total_units'] += total_units
            medications_with_stock[med_key]['total_value'] += (stock.quantity * stock.price) + (
                        stock.unit_quantity * stock.unit_price)

            # Update expiry flag if any batch expires soon
            if stock.expire_date and (stock.expire_date - timezone.now().date()).days <= 90:
                medications_with_stock[med_key]['expires_soon'] = True
            if stock.expire_date and stock.expire_date < timezone.now().date():
                medications_with_stock[med_key]['expired'] = True

    # Determine low stock status
    for med_key, data in medications_with_stock.items():
        # Simple threshold: if total units < 20, it's low stock
        data['low_stock'] = data['total_units'] < 20

    # Apply low stock filter if enabled
    if low_stock_only:
        medications_with_stock = {k: v for k, v in medications_with_stock.items() if v['low_stock']}

    # Apply out of stock filter if enabled
    if out_of_stock:
        medications_with_stock = {k: v for k, v in medications_with_stock.items() if v['total_units'] == 0}

    # Convert to list for template
    report_data = list(medications_with_stock.values())

    # Sort by name, then warehouse
    report_data.sort(key=lambda x: (x['medication'].name, x['warehouse'].name))

    # Calculate summary statistics
    total_items = len(report_data)
    total_value = sum(item['total_value'] for item in report_data)
    low_stock_count = sum(1 for item in report_data if item['low_stock'])
    expiring_soon_count = sum(1 for item in report_data if item['expires_soon'])
    expired_count = sum(1 for item in report_data if item['expired'])

    # Handle export to CSV if requested
    if request.GET.get('export') == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="stock_report_{timezone.now().strftime("%Y%m%d")}.csv"'

        writer = csv.writer(response)
        writer.writerow(['Medication', 'Warehouse', 'Packages', 'Units', 'Total Units', 'Total Value', 'Low Stock',
                         'Expiry Status'])

        for item in report_data:
            expiry_status = 'Normal'
            if item['expired']:
                expiry_status = 'Expired'
            elif item['expires_soon']:
                expiry_status = 'Expiring Soon'

            writer.writerow([
                item['medication'].name,
                item['warehouse'].name,
                item['quantity'],
                item['unit_quantity'],
                item['total_units'],
                item['total_value'],
                'Yes' if item['low_stock'] else 'No',
                expiry_status
            ])

        return response

    context = {
        'report_data': report_data,
        'warehouses': warehouses,
        'selected_warehouse': selected_warehouse,
        'search_query': search_query,
        'low_stock_only': low_stock_only,
        'out_of_stock': out_of_stock,
        'total_items': total_items,
        'total_value': total_value,
        'low_stock_count': low_stock_count,
        'expiring_soon_count': expiring_soon_count,
        'expired_count': expired_count,
        'now': timezone.now(),
    }

    return render(request, 'warehouse/reports/stock_report.html', context)


@login_required
def expiry_report(request):
    """
    Generate a report focused on medications that are expired or will expire soon.
    Allows filtering by warehouse, expiry timeframe, and export to CSV.
    """
    # Get all warehouses for filter dropdown
    warehouses = Warehouse.objects.all()
    selected_warehouse = request.GET.get('warehouse')

    # Timeframe filtering
    timeframe = request.GET.get('timeframe', '90')  # Default to 90 days
    try:
        days = int(timeframe)
    except ValueError:
        days = 90

    today = timezone.now().date()
    future_date = today + timedelta(days=days)

    # Status filtering
    expiry_status = request.GET.get('status', 'all')  # 'all', 'expired', or 'expiring'

    # Base query for stock
    expiry_query = MedicationsInStockModel.objects.select_related('item', 'warehouse')

    # Apply warehouse filter if selected
    if selected_warehouse:
        expiry_query = expiry_query.filter(warehouse_id=selected_warehouse)

    # Filter by expiry status
    if expiry_status == 'expired':
        expiry_query = expiry_query.filter(expire_date__lt=today)
    elif expiry_status == 'expiring':
        expiry_query = expiry_query.filter(expire_date__gte=today, expire_date__lte=future_date)
    else:  # 'all'
        expiry_query = expiry_query.filter(expire_date__lte=future_date)

    # Filter out zero quantity stocks unless explicitly showing all
    if request.GET.get('show_zero') != 'on':
        expiry_query = expiry_query.filter(Q(quantity__gt=0) | Q(unit_quantity__gt=0))

    # Group by medication and warehouse for better reporting
    report_data = []
    for stock in expiry_query:
        medication = stock.item
        warehouse = stock.warehouse

        # Calculate days until expiry
        days_until_expiry = (stock.expire_date - today).days if stock.expire_date else None

        # Calculate total units and value
        total_units = (stock.quantity * medication.in_pack) + stock.unit_quantity
        total_value = (stock.quantity * stock.price) + (stock.unit_quantity * stock.unit_price)

        # Determine status category
        if days_until_expiry is None:
            status = 'Unknown'
        elif days_until_expiry < 0:
            status = 'Expired'
        elif days_until_expiry <= 30:
            status = 'Critical'
        elif days_until_expiry <= 90:
            status = 'Warning'
        else:
            status = 'OK'

        # Add to report data
        report_data.append({
            'medication': medication,
            'warehouse': warehouse,
            'expire_date': stock.expire_date,
            'days_until_expiry': days_until_expiry,
            'quantity': stock.quantity,
            'unit_quantity': stock.unit_quantity,
            'total_units': total_units,
            'total_value': total_value,
            'status': status,
            'income_seria': stock.income_seria,
        })

    # Sort by days until expiry, then by medication name
    report_data.sort(key=lambda x: (x['days_until_expiry'] if x['days_until_expiry'] is not None else 9999,
                                    x['medication'].name))

    # Calculate summary statistics
    expired_count = sum(1 for item in report_data if item['status'] == 'Expired')
    critical_count = sum(1 for item in report_data if item['status'] == 'Critical')
    warning_count = sum(1 for item in report_data if item['status'] == 'Warning')

    total_expired_value = sum(item['total_value'] for item in report_data if item['status'] == 'Expired')
    total_critical_value = sum(item['total_value'] for item in report_data if item['status'] == 'Critical')
    total_warning_value = sum(item['total_value'] for item in report_data if item['status'] == 'Warning')

    total_value = sum(item['total_value'] for item in report_data)

    # Handle export to CSV if requested
    if request.GET.get('export') == 'csv':
        response = HttpResponse(content_type='text/csv')
        response[
            'Content-Disposition'] = f'attachment; filename="expiry_report_{timezone.now().strftime("%Y%m%d")}.csv"'

        writer = csv.writer(response)
        writer.writerow(['Medication', 'Warehouse', 'Batch/Seria', 'Expiry Date', 'Days Until Expiry',
                         'Packages', 'Units', 'Total Units', 'Total Value', 'Status'])

        for item in report_data:
            writer.writerow([
                item['medication'].name,
                item['warehouse'].name,
                item['income_seria'] or 'N/A',
                item['expire_date'].strftime('%Y-%m-%d') if item['expire_date'] else 'N/A',
                item['days_until_expiry'] if item['days_until_expiry'] is not None else 'N/A',
                item['quantity'],
                item['unit_quantity'],
                item['total_units'],
                item['total_value'],
                item['status']
            ])

        return response

    context = {
        'report_data': report_data,
        'warehouses': warehouses,
        'selected_warehouse': selected_warehouse,
        'timeframe': timeframe,
        'expiry_status': expiry_status,
        'show_zero': request.GET.get('show_zero') == 'on',
        'today': today,
        'future_date': future_date,
        'expired_count': expired_count,
        'critical_count': critical_count,
        'warning_count': warning_count,
        'total_expired_value': total_expired_value,
        'total_critical_value': total_critical_value,
        'total_warning_value': total_warning_value,
        'total_value': total_value,
        'item_count': len(report_data),
    }

    return render(request, 'warehouse/reports/expiry_report.html', context)


@login_required
def income_report(request):
    """
    Generate a report on incoming deliveries with trend analysis.
    Allows filtering by date range, warehouse, company, and export to CSV.
    """
    # Get all warehouses and companies for filter dropdowns
    warehouses = Warehouse.objects.all()
    companies = CompanyModel.objects.all()

    # Date range filtering
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')

    today = timezone.now().date()

    try:
        if start_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        else:
            # Default to first day of current month
            start_date = today.replace(day=1)

        if end_date_str:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        else:
            # Default to today
            end_date = today
    except ValueError:
        # Handle invalid date format
        start_date = today.replace(day=1)
        end_date = today

    # Additional filters
    selected_warehouse = request.GET.get('warehouse')
    selected_company = request.GET.get('company')
    group_by = request.GET.get('group_by', 'day')  # 'day', 'month', or 'company'

    # Base query for income records
    income_query = IncomeModel.objects.filter(
        created_at__date__gte=start_date,
        created_at__date__lte=end_date
    ).select_related('receiver', 'delivery_company')

    # Apply filters
    if selected_warehouse:
        income_query = income_query.filter(receiver_id=selected_warehouse)

    if selected_company:
        income_query = income_query.filter(delivery_company_id=selected_company)

    # Only include accepted incomes by default unless showing all statuses
    if request.GET.get('show_all_statuses') != 'on':
        income_query = income_query.filter(state='принято')

    # Collect detailed income data
    detailed_data = []
    for income in income_query:
        detailed_data.append({
            'id': income.id,
            'serial': income.serial,
            'date': income.created_at.date(),
            'warehouse': income.receiver,
            'company': income.delivery_company,
            'state': income.state,
            'amount': income.overall_sum,
            'items_count': income.income_items.count(),
        })

    # Sort by date descending
    detailed_data.sort(key=lambda x: x['date'], reverse=True)

    # Group data based on selected grouping
    grouped_data = {}

    if group_by == 'day':
        # Group by day
        for income in detailed_data:
            day = income['date']
            if day not in grouped_data:
                grouped_data[day] = {
                    'label': day.strftime('%Y-%m-%d'),
                    'date': day,
                    'count': 0,
                    'total_amount': 0,
                    'incomes': []
                }

            grouped_data[day]['count'] += 1
            grouped_data[day]['total_amount'] += income['amount']
            grouped_data[day]['incomes'].append(income)

    elif group_by == 'month':
        # Group by month
        for income in detailed_data:
            month = income['date'].replace(day=1)
            if month not in grouped_data:
                grouped_data[month] = {
                    'label': month.strftime('%Y-%m'),
                    'date': month,
                    'count': 0,
                    'total_amount': 0,
                    'incomes': []
                }

            grouped_data[month]['count'] += 1
            grouped_data[month]['total_amount'] += income['amount']
            grouped_data[month]['incomes'].append(income)

    elif group_by == 'company':
        # Group by company
        for income in detailed_data:
            company = income['company']
            if company not in grouped_data:
                company_name = company.name if company else 'Неизвестно'
                grouped_data[company] = {
                    'label': company_name,
                    'company': company,
                    'count': 0,
                    'total_amount': 0,
                    'incomes': []
                }

            grouped_data[company]['count'] += 1
            grouped_data[company]['total_amount'] += income['amount']
            grouped_data[company]['incomes'].append(income)

    # Convert to list and sort
    if group_by in ['day', 'month']:
        report_data = sorted(grouped_data.values(), key=lambda x: x['date'], reverse=True)
    else:  # company
        report_data = sorted(grouped_data.values(), key=lambda x: x['total_amount'], reverse=True)

    # Calculate summary statistics
    total_income_count = len(detailed_data)
    total_income_amount = sum(income['amount'] for income in detailed_data)

    # Get top 5 products by quantity
    top_products = []
    if detailed_data:
        # Collect all income item IDs
        income_ids = [income['id'] for income in detailed_data]

        # Query income items
        income_items = IncomeItemsModel.objects.filter(
            income_id__in=income_ids
        ).select_related('item').values(
            'item__name'
        ).annotate(
            total_quantity=Sum(F('quantity') * F('item__in_pack') + F('unit_quantity')),
            total_value=Sum(F('overall_price'))
        ).order_by('-total_quantity')[:5]

        top_products = list(income_items)

    # Handle export to CSV if requested
    if request.GET.get('export') == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="income_report_{start_date}_to_{end_date}.csv"'

        writer = csv.writer(response)
        writer.writerow(['Date', 'Serial', 'Warehouse', 'Company', 'Status', 'Amount', 'Items Count'])

        for income in detailed_data:
            writer.writerow([
                income['date'],
                income['serial'],
                income['warehouse'].name if income['warehouse'] else 'N/A',
                income['company'].name if income['company'] else 'N/A',
                income['state'],
                income['amount'],
                income['items_count']
            ])

        return response

    context = {
        'report_data': report_data,
        'detailed_data': detailed_data[:100],  # Limit to prevent performance issues
        'show_all_details': len(detailed_data) <= 100,
        'warehouses': warehouses,
        'companies': companies,
        'selected_warehouse': selected_warehouse,
        'selected_company': selected_company,
        'start_date': start_date,
        'end_date': end_date,
        'group_by': group_by,
        'show_all_statuses': request.GET.get('show_all_statuses') == 'on',
        'total_income_count': total_income_count,
        'total_income_amount': total_income_amount,
        'top_products': top_products,
    }

    return render(request, 'warehouse/reports/income_report.html', context)