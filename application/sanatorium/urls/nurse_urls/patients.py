from django.urls import path

from application.sanatorium.views.nurses_viewset import assigned_patients

urlpatterns = [

    path('<int:history_id>/', assigned_patients.patient_detail, name='patient_detail'),
    path('<int:history_id>/edit/', assigned_patients.patient_edit, name='patient_edit'),
    path('<int:history_id>/edit/', assigned_patients.patient_edit, name='patient_edit'),
    path('get-patient-booking/', assigned_patients.get_patient_bookings, name='get_patient_bookings'),
]
