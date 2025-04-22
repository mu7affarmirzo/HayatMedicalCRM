from django.urls import path, include

from application.sanatorium.views import assigned_patients

urlpatterns = [
    path('dashboard/', assigned_patients.assigned_patients_list, name='doctor_dashboard'),
    path('<int:history_id>/', assigned_patients.patient_detail, name='patient_detail'),
    path('<int:history_id>/edit/', assigned_patients.patient_edit, name='patient_edit'),
    path('<int:history_id>/edit/', assigned_patients.patient_edit, name='patient_edit'),
    path('get-patient-booking/', assigned_patients.get_patient_bookings, name='get_patient_bookings'),

    path('appointments/', include('application.sanatorium.urls.appointments')),
]
