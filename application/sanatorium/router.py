from django.urls import path, include



urlpatterns = [
    path('doctor/', include('application.sanatorium.urls.doctors')),
    path('nurse/', include('application.sanatorium.urls.nurses'), name='nurses'),
    path('massagist/', include('application.sanatorium.urls.massagists'), name='massagists'),
]
