from django.urls import path, include

from application.logus.views.rooms import available_room_view, reception_dashboard, create_quick_booking

app_name = 'logus'

urlpatterns = [
    path('booking/', include('application.logus.urls.booking')),
    path('patients/', include('application.logus.urls.patients')),
    path('illness-histories/', include('application.logus.urls.illness_histories')),


    path('availability/', available_room_view, name='check_availability'),
    path('new/dashboard/', reception_dashboard, name='logus_dashboard'),
    path('dashboard/quick-booking/', create_quick_booking, name='create_quick_booking'),

]
