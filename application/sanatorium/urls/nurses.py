from django.urls import path, include

from application.sanatorium.views.nurses_viewset.illness_history import assigned_patients_list, all_patients_list


app_name = 'sanatorium.nurses'

urlpatterns = [
    path('main_screen/', assigned_patients_list, name='nurses_main_screen'),
    path('patients-list/', all_patients_list, name='nurse_patients_list'),

    path('appointments/', include('application.sanatorium.urls.nurse_urls.appointments')),
    path('histories/', include('application.sanatorium.urls.nurse_urls.illness_histories')),
    path('patients/', include('application.sanatorium.urls.nurse_urls.patients')),
    path('prescription/', include('application.sanatorium.urls.nurse_urls.prescriptions')),
    path('documents/', include('application.sanatorium.urls.nurse_urls.documents')),

]


