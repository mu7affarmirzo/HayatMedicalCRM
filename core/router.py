from django.urls import path, include


urlpatterns = [
    path('application/', include('core.applications.router')),
    path('administration/', include('core.administration.logus.router')),
]
