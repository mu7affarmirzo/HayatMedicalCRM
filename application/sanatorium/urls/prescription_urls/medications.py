# urls.py
from django.urls import path

from application.sanatorium.views.prescriptions import medications as views


urlpatterns = [
    # PrescribedMedication URLs
    path('medications/', views.PrescribedMedicationListView.as_view(),
         name='medications_list'),
    path('medications/<int:pk>/', views.PrescribedMedicationDetailView.as_view(),
         name='medications_detail'),
    path('medications/create/<int:illness_history_id>', views.PrescribedMedicationCreateView.as_view(),
         name='prescribed_medication_create'),
    path('medications/<int:pk>/update/', views.PrescribedMedicationUpdateView.as_view(),
         name='medications_update'),
    path('medications/<int:pk>/delete/', views.PrescribedMedicationDeleteView.as_view(),
         name='medications_delete'),

    path('api/search/', views.api_medications_search, name='api_medications_search'),
    path('api/details/', views.api_medication_details, name='api_medication_details'),

    # MedicationAdministration URLs
    path('administrations/', views.MedicationAdministrationListView.as_view(),
         name='medication_administration_list'),
    path('administrations/<int:pk>/', views.MedicationAdministrationDetailView.as_view(),
         name='medication_administration_detail'),
    path('administrations/create/', views.MedicationAdministrationCreateView.as_view(),
         name='medication_administration_create'),
    path('administrations/<int:pk>/update/', views.MedicationAdministrationUpdateView.as_view(),
         name='medication_administration_update'),
    path('administrations/<int:pk>/delete/', views.MedicationAdministrationDeleteView.as_view(),
         name='medication_administration_delete'),
]