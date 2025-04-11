from django.urls import path, include


urlpatterns = [
    path('logus/', include('administration.logus.router')),
]
