from django.urls import path
from django.urls.conf import include

from .urls import incomes_url, medications_url, warehouses_url, companies_url, reports_url, patient_expenses_urls
from .views import dashboard, income, medications, warehouses, company, reports

app_name = 'warehouse'

urlpatterns = [
    # Dashboard
    path('', dashboard.warehouse_dashboard, name='warehouse_dashboard'),

    # Income/Receipts Management
    path('income/', include(incomes_url)),
    path('medications/', include(medications_url)),
    path('warehouses/', include(warehouses_url)),
    path('companies/', include(companies_url)),

    # Reports
    path('reports/', include(reports_url)),

    # Patients expenses
    path('patients/', include(patient_expenses_urls)),

]
