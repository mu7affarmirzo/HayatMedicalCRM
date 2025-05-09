from django.urls import path, include

from application.logus.views.rooms import available_room_view

urlpatterns = [
    path('', include('application.logus.urls.booking_list')),
    path('availability/', available_room_view, name='check_availability'),
    path('booking/', include('application.logus.urls.booking')),
    # path('booking/', include('core.reception.urls.registration')),
    # path('adminstration/', include('core.adminstration.urls.adminstration')),
    # path('adminstration/services/', include('core.adminstration.urls.services')),
]
