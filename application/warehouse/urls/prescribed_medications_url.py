# warehouse/urls/medications.py
from django.urls import path
from application.warehouse.views.prescribed_medications import PrescribedMedicationListView, PrescribedMedicationDetailView


urlpatterns = [
    path('prescribed/', PrescribedMedicationListView.as_view(), name='prescribed_list'),
    path('prescribed/<int:pk>/', PrescribedMedicationDetailView.as_view(), name='prescribed_detail'),
]