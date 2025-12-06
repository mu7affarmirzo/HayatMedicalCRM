from django.urls import path

from application.warehouse.views import expense_views


urlpatterns = [
    # Medication Expense Management
    path('', expense_views.expense_list, name='expense_list'),
    path('create/', expense_views.expense_create, name='expense_create'),
    path('<int:pk>/', expense_views.expense_detail, name='expense_detail'),
    path('export-excel/', expense_views.expense_export_excel, name='expense_export'),
]
