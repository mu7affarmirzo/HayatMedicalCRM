from django.urls import path, include

from core.administration.logus.urls import rooms

urlpatterns = [
    path('rooms/', include(rooms)),
]
