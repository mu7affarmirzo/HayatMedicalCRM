# urls.py
from django.urls import path

from application.sanatorium.views.doctors_viewset.prescriptions import medications as views
from application.sanatorium.views.doctors_viewset.prescriptions import medication_sessions as sessions

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

    # Sessions
    path('sessions/<int:med_id>', sessions.medication_sessions_list, name='medication_sessions_list'),
    path('sessions/today/', sessions.today_sessions, name='today_sessions'),
    path('sessions/<int:session_id>/', sessions.session_detail, name='session_detail'),
    path('sessions/<int:session_id>/update/', sessions.update_session_status, name='update_session_status'),

    # Patient medications
    path('patients/<int:patient_id>/', sessions.patient_medications, name='patient_medications'),

    # Statistics
    path('statistics/', sessions.medication_statistics, name='medication_statistics'),

    # Create session
    path('prescribed/<int:prescribed_medication_id>/create-session/',
         sessions.create_medication_session, name='create_medication_session'),
]