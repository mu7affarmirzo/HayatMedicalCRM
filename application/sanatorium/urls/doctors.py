from django.urls import path, include
from application.sanatorium.views.illness_history import assigned_patients_list, all_patients_list


urlpatterns = [
    path('main_screen/', assigned_patients_list, name='doctors_main_screen'),
    path('patients-list/', all_patients_list, name='patients_list'),
    path('dashboard/', assigned_patients_list, name='doctor_dashboard'),

    path('appointments/', include('application.sanatorium.urls.appointments')),
    path('histories/', include('application.sanatorium.urls.illness_histories')),
    path('patients/', include('application.sanatorium.urls.patients')),
    path('prescription/', include('application.sanatorium.urls.prescriptions')),

]