from django.urls import path, include

urlpatterns = [
    path('init-app/', include('application.sanatorium.urls.appointment_urls.init_app')),
    path('cardiologist/', include('application.sanatorium.urls.appointment_urls.cardiologist')),
    path('neurologist/', include('application.sanatorium.urls.appointment_urls.neurologist')),
    path('on-arrival/', include('application.sanatorium.urls.appointment_urls.on_arrival')),
    path('repeated-app/', include('application.sanatorium.urls.appointment_urls.repeated_app')),
    path('on-duty-app/', include('application.sanatorium.urls.appointment_urls.on_duty_app')),
    path('ekg-app/', include('application.sanatorium.urls.appointment_urls.ekg_app')),
    path('final-app/', include('application.sanatorium.urls.appointment_urls.final_app')),
]