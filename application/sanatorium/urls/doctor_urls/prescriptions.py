from django.urls import path, include
from application.sanatorium.views.doctors_viewset.prescriptions.main_list import (
    create_appointment, cancel_appointment, view_appointment, main_prescription_list_view,
    prescription_consultings_view, prescription_labs_view, prescription_procedures_view, prescription_medications_view
)

urlpatterns = [
    # Main prescription list view (redirects to consultings)
    path('<int:history_id>', main_prescription_list_view, name='prescription_list'),
    path('illness-history/<int:history_id>/prescription/', main_prescription_list_view, name='main_prescription_list'),
    path('<int:history_id>/', main_prescription_list_view, name='main_prescription_list'),

    # Separate views for each section
    path('<int:history_id>/consultings/', prescription_consultings_view, name='prescription_consultings'),
    path('<int:history_id>/labs/', prescription_labs_view, name='prescription_labs'),
    path('<int:history_id>/procedures/', prescription_procedures_view, name='prescription_procedures'),
    path('<int:history_id>/medications/', prescription_medications_view, name='prescription_medications'),

    # Existing includes for detailed views
    path('procedures/', include('application.sanatorium.urls.doctor_urls.prescription_urls.procedures')),
    path('labs/', include('application.sanatorium.urls.doctor_urls.prescription_urls.labs')),
    path('medications/', include('application.sanatorium.urls.doctor_urls.prescription_urls.medications')),

    # Appointment management
    path('<int:history_id>/create-appointment/', create_appointment, name='create_appointment'),
    path('<int:history_id>/cancel-appointment/', cancel_appointment, name='cancel_appointment'),
    path('appointments/<str:model_name>/<int:appointment_id>/', view_appointment, name='view_appointment'),
]
