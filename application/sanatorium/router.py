from django.urls import path, include

from application.sanatorium.views import assigned_patients


urlpatterns = [
    path('dashboard/', assigned_patients.assigned_patients_list, name='doctor_dashboard'),
    path('patient/<int:history_id>/', assigned_patients.patient_detail, name='patient_detail'),
    path('patient/<int:history_id>/edit/', assigned_patients.patient_edit, name='patient_edit'),
]
