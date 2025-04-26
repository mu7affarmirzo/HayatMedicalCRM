from django.urls import path, include

urlpatterns = [
    path('init-app/', include('application.sanatorium.urls.init_app')),
    path('cardiologist/', include('application.sanatorium.urls.cardiologist')),
    path('neurologist/', include('application.sanatorium.urls.neurologist')),
    path('on-arrival/', include('application.sanatorium.urls.on_arrival')),
    path('repeated-app/', include('application.sanatorium.urls.repeated_app')),
    path('on-duty-app/', include('application.sanatorium.urls.on_duty_app')),
]