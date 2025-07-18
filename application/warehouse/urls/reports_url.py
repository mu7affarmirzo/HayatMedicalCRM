from django.urls import path

from application.warehouse.views import reports


urlpatterns = [
    # Reports
    path('reports/stock/', reports.stock_report, name='stock_report'),
    path('reports/expiry/', reports.expiry_report, name='expiry_report'),
    path('reports/income/', reports.income_report, name='income_report'),

]