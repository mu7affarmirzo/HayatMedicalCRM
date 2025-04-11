from django.urls import path, include

from administration.logus.urls import rooms

urlpatterns = [
    path('rooms/', include(rooms)),
]
