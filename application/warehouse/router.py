from django.urls import path

from .views import dashboard, income, medications, warehouses, company, reports

app_name = 'warehouse'

urlpatterns = [
    # Dashboard
    path('', dashboard.warehouse_dashboard, name='warehouse_dashboard'),

    # Income/Receipts Management
    path('income/', income.income_list, name='income_list'),
    path('income/create/', income.income_create, name='income_create'),
    path('income/<int:pk>/', income.income_detail, name='income_detail'),
    path('income/<int:pk>/update/', income.income_update, name='income_update'),
    path('income/<int:pk>/accept/', income.income_accept, name='income_accept'),
    path('income/<int:pk>/reject/', income.income_reject, name='income_reject'),

    # # Medication Management
    path('medications/', medications.medication_list, name='medication_list'),
    path('medications/create/', medications.medication_create, name='medication_create'),
    path('medications/<int:pk>/', medications.medication_detail, name='medication_detail'),
    path('medications/<int:pk>/update/', medications.medication_update, name='medication_update'),
    path('medications/expiring/', medications.expiring_medications, name='expiring_medications'),
    path('medications/low-stock/', medications.low_stock, name='low_stock'),

    # Warehouse Management
    path('warehouses/', warehouses.warehouse_list, name='warehouse_list'),
    path('warehouses/create/', warehouses.warehouse_create, name='warehouse_create'),
    path('warehouses/<int:pk>/', warehouses.warehouse_detail, name='warehouse_detail'),
    path('warehouses/<int:pk>/update/', warehouses.warehouse_update, name='warehouse_update'),
    path('warehouses/transfer/', warehouses.warehouse_transfer, name='warehouse_transfer'),
    path('warehouses/stats/', warehouses.warehouse_stats, name='warehouse_stats'),
    path('warehouses/batches/', warehouses.get_batches, name='get_batches'),
    path('warehouses/medicaion-info/', warehouses.get_medication_info, name='get_medication_info'),

    # # Company Management
    path('companies/', company.company_list, name='company_list'),
    path('companies/create/', company.company_create, name='company_create'),
    path('companies/<int:pk>/', company.company_detail, name='company_detail'),
    path('companies/<int:pk>/update/', company.company_update, name='company_update'),

    # Reports
    path('reports/stock/', reports.stock_report, name='stock_report'),
    path('reports/expiry/', reports.expiry_report, name='expiry_report'),
    path('reports/income/', reports.income_report, name='income_report'),
]