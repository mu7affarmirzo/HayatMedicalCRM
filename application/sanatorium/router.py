from django.urls import path, include


urlpatterns = [
    path('patient/', include('application.sanatorium.urls.patients')),
    path('doctor/', include('application.sanatorium.urls.doctors')),
]
