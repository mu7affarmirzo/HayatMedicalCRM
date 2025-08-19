# urls.py
from django.urls import path
from django.urls.conf import include

from application.sanatorium.urls.nurse_urls.prescription_urls import medication_sessions_url
from application.sanatorium.views.nurses_viewset.prescriptions import medications as views
from application.sanatorium.views.nurses_viewset.prescriptions.medication_sessions import \
    MedicationSessionUpdateNotesView, MedicationSessionUpdateStatusView

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

    path('', include(medication_sessions_url))
]
