"""
URL Configuration for Room Availability Matrix V2 (RM2)

FEATURE: RM2 - Room Availability V2
"""

from django.urls import path
from application.logus.views import room_availability_v2

urlpatterns = [
    # Main matrix view
    path('',
         room_availability_v2.room_availability_matrix_v2_view,
         name='room_availability_v2'),

    # AJAX endpoint for room details
    path('room-details/',
         room_availability_v2.get_room_details_ajax,
         name='room_details_ajax_v2'),

    # AJAX endpoint for guest details
    path('guest-details/',
         room_availability_v2.get_guest_details_ajax,
         name='guest_details_ajax_v2'),

    # Quick booking endpoint
    path('quick-book/',
         room_availability_v2.quick_book_from_matrix,
         name='quick_book_from_matrix'),

    # Export to Excel
    path('export-excel/',
         room_availability_v2.export_matrix_excel,
         name='export_matrix_excel_v2'),
]
