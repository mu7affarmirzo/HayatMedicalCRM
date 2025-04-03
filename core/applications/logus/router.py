from django.urls import path, include

from core.applications.logus.views.rooms import check_availability

urlpatterns = [
    path('availability/', check_availability, name='check_availability'),
    # path('', include('core.reception.urls.auth')),
    # path('booking/', include('core.reception.urls.registration')),
    # path('adminstration/', include('core.adminstration.urls.adminstration')),
    # path('adminstration/services/', include('core.adminstration.urls.services')),
]
