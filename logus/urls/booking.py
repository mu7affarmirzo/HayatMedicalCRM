from django.urls import path
from logus.views import booking

urlpatterns = [
    # Booking process
    path('booking/start/', booking.booking_start, name='booking_start'),
    path('booking/select-rooms/', booking.booking_select_rooms, name='booking_select_rooms'),
    path('booking/confirm/', booking.booking_confirm, name='booking_confirm'),
    path('booking/<int:booking_id>/', booking.booking_detail, name='booking_detail'),

    # AJAX endpoints
    path('booking/check-availability/', booking.check_room_availability_ajax, name='check_room_availability'),
]