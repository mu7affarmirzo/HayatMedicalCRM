from django.urls import path, include

from core.applications.logus.views.rooms import available_room_view

urlpatterns = [
    path('availability/', available_room_view, name='check_availability'),
    # path('', include('core.reception.urls.auth')),
    # path('booking/', include('core.reception.urls.registration')),
    # path('adminstration/', include('core.adminstration.urls.adminstration')),
    # path('adminstration/services/', include('core.adminstration.urls.services')),
]
