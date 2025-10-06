from django.urls import path, include

from application.logus.views.rooms import available_room_view, create_quick_booking
from application.logus.views.dashboard import reception_dashboard

app_name = 'logus'

urlpatterns = [
    path('dashboard/', reception_dashboard, name='logus_dashboard'),

    path('booking/', include('application.logus.urls.booking')),
    path('patients/', include('application.logus.urls.patients')),
    path('illness-histories/', include('application.logus.urls.illness_histories')),
    path('payments/', include('application.logus.urls.payments')),


    path('availability/', available_room_view, name='check_availability'),
    path('dashboard/quick-booking/', create_quick_booking, name='create_quick_booking'),

]
