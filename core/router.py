from django.urls import path, include


urlpatterns = [
    path('application/', include('application.router')),
    path('administration/', include('administration.logus.router')),
]
