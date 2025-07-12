from django.urls import path

from application.logus.views import booking
from application.logus.views.booking_list import update_booking_status, booking_list

urlpatterns = [

    # Booking process
    path('start/', booking.booking_start, name='booking_start'),
    path('select-rooms/', booking.booking_select_rooms, name='booking_select_rooms'),
    path('confirm/', booking.booking_confirm, name='booking_confirm'),

    # AJAX endpoints
    path('check-availability/', booking.check_room_availability_ajax, name='check_room_availability'),

    path('add-new-patient/', booking.add_new_patient, name='add-new-patient'),
    path('patient-registration/', booking.patient_registration, name='patient_registration'),
    path('get-districts/', booking.get_districts, name='get_districts'),


    path('list/', booking_list, name='booking_list'),
    path('<int:booking_id>/', booking.booking_detail, name='booking_detail'),
    path('status/<int:booking_id>/', update_booking_status, name='update_booking_status'),
]