from django.urls import path
from django.urls.conf import include

from .views import dashboard
from .urls import medications_url, warehouses_url, companies_url, reports_url, patient_expenses_urls, prescribed_medications_url, transfers_url, income_urls, account_transfers_url

app_name = 'warehouse'

urlpatterns = [
    # Dashboard
    path('', dashboard.warehouse_dashboard, name='warehouse_dashboard'),

    # Income/Receipts Management
    path('income/', include(income_urls)),
    path('medications/', include(medications_url)),
    path('warehouses/', include(warehouses_url)),
    path('companies/', include(companies_url)),

    # Reports
    path('reports/', include(reports_url)),

    # Patients expenses
    path('patients/', include(patient_expenses_urls)),
    path('prescribtions/', include(prescribed_medications_url)),

    # Account Transfers
    path('account-transfers/', include(account_transfers_url)),
]
