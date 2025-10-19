from django.urls import path

from application.warehouse.views import medications


urlpatterns = [

    # # Medication Management
    path('', medications.medication_list, name='medication_list'),
    path('create/', medications.medication_create, name='medication_create'),
    path('<int:pk>/', medications.medication_detail, name='medication_detail'),
    path('<int:pk>/update/', medications.medication_update, name='medication_update'),
    path('expiring/', medications.expiring_medications, name='expiring_medications'),
    path('expiring/export-excel/', medications.expiring_medications_export_excel, name='expiring_medications_export'),
    path('low-stock/', medications.low_stock, name='low_stock'),

]