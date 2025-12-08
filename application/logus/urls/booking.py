from django.urls import path

from application.logus.views import booking
from application.logus.views.booking_detail import booking_edit_view, booking_detail_add_view, booking_detail_edit_view, \
    booking_detail_delete_view
from application.logus.views.booking_list import update_booking_status, booking_list, booking_detail_view
from application.logus.views.booking_services import booking_detail_view_detail, booking_add_service_view, \
    service_usage_edit_view, service_usage_delete_view

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
    path('<int:booking_id>/', booking.booking_detail, name='booking_detail_old'),
    path('detail/<int:booking_id>/', booking_detail_view, name='booking_detail'),
    path('status/<int:booking_id>/', update_booking_status, name='update_booking_status'),

    # Booking views
    path('<int:booking_id>/edit/', booking_edit_view, name='booking_edit'),
    path('<int:booking_id>/add-guest/', booking_detail_add_view, name='booking_detail_add'),

    path('booking-details/<int:detail_id>/', booking_detail_view_detail, name='booking_detail_view'),
    path('booking-details/<int:detail_id>/edit/', booking_detail_edit_view, name='booking_detail_edit'),
    path('booking-details/<int:detail_id>/delete/', booking_detail_delete_view, name='booking_detail_delete'),

    # Service views
    path('booking-details/<int:detail_id>/add-service/', booking_add_service_view, name='booking_add_service'),
    path('services/<int:service_id>/edit/', service_usage_edit_view, name='service_usage_edit'),
    path('services/<int:service_id>/delete/', service_usage_delete_view, name='service_usage_delete'),

    # Tariff change and service session tracking (TASK-013, TASK-015)
    path('booking-details/<int:detail_id>/change-tariff/', booking.tariff_change_view, name='tariff_change'),
    path('service-tracking/<int:tracking_id>/record-session/', booking.record_service_session, name='record_service_session'),
]