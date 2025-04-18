from django.urls import path, include


urlpatterns = [
    path('logus/', include('application.logus.router')),
]
