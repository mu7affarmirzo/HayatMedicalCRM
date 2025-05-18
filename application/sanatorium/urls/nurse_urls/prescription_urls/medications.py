# urls.py
from django.urls import path

from application.sanatorium.views.nurses_viewset.prescriptions import medications as views

urlpatterns = [
    # PrescribedMedication URLs
    path('', views.PrescribedMedicationListView.as_view(),
         name='medications_list'),
    path('<int:pk>/', views.PrescribedMedicationDetailView.as_view(),
         name='medications_detail'),
    path('create/<int:illness_history_id>', views.PrescribedMedicationCreateView.as_view(),
         name='prescribed_medication_create'),
    path('<int:pk>/update/', views.PrescribedMedicationUpdateView.as_view(),
         name='medications_update'),
    path('<int:pk>/delete/', views.PrescribedMedicationDeleteView.as_view(),
         name='medications_delete'),

    path('medication-sessions/<int:session_id>/update-status/', views.update_session_status, name='update_session_status'),
    path('medication-sessions/<int:session_id>/administer/', views.administer_medication, name='administer_medication'),

    path('api/search/', views.api_medications_search, name='api_medications_search'),
    path('api/details/', views.api_medication_details, name='api_medication_details'),

    # MedicationSession URLs
    path('administrations/', views.MedicationSessionListView.as_view(),
         name='medication_administration_list'),
    path('administrations/<int:pk>/', views.MedicationSessionDetailView.as_view(),
         name='medication_administration_detail'),
    path('administrations/create/', views.MedicationSessionCreateView.as_view(),
         name='medication_administration_create'),
    path('administrations/<int:pk>/update/', views.MedicationSessionUpdateView.as_view(),
         name='medication_administration_update'),
    path('administrations/<int:pk>/delete/', views.MedicationSessionDeleteView.as_view(),
         name='medication_administration_delete'),
]