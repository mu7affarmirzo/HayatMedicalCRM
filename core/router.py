from django.urls import path, include


urlpatterns = [
    path('logus/', include('core.applications.logus.router')),
]
