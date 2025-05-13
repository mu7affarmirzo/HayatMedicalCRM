from django.urls import path, include

from application.sanatorium.views.nurses_viewset.nurses_appointments import nurse_appointments
from application.sanatorium.views.nurses_viewset.illness_history import assigned_patients_list, all_patients_list


urlpatterns = [
    path('main_screen/', assigned_patients_list, name='nurses_main_screen'),
    path('patients-list/', all_patients_list, name='patients_list'),
    path('dashboard/', assigned_patients_list, name='nurse_dashboard'),

    path('assigned-appointments/', nurse_appointments, name='nurse_appointments'),

    path('appointments/', include('application.sanatorium.urls.nurse_urls.appointments')),
    path('histories/', include('application.sanatorium.urls.nurse_urls.illness_histories')),
    path('patients/', include('application.sanatorium.urls.nurse_urls.patients')),
    path('prescription/', include('application.sanatorium.urls.nurse_urls.prescriptions')),
    path('documents/', include('application.sanatorium.urls.nurse_urls.documents')),

]


