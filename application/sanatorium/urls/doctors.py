from django.urls import path, include

from application.sanatorium.views.doctors_viewset.doctors_appointments import doctor_appointments
from application.sanatorium.views.doctors_viewset.illness_history import assigned_patients_list, all_patients_list


urlpatterns = [
    path('main_screen/', assigned_patients_list, name='doctors_main_screen'),
    path('patients-list/', all_patients_list, name='patients_list'),
    path('dashboard/', assigned_patients_list, name='doctor_dashboard'),

    path('assigned-appointments/', doctor_appointments, name='doctor_appointments'),

    path('appointments/', include('application.sanatorium.urls.doctor_urls.appointments')),
    path('histories/', include('application.sanatorium.urls.doctor_urls.illness_histories')),
    path('patients/', include('application.sanatorium.urls.doctor_urls.patients')),
    path('prescription/', include('application.sanatorium.urls.doctor_urls.prescriptions')),
    path('documents/', include('application.sanatorium.urls.doctor_urls.documents')),

]
