from django.urls import path, include


urlpatterns = [
    path('logus/', include('application.logus.router')),
    path('sanatorium/', include('application.sanatorium.router')),
]
