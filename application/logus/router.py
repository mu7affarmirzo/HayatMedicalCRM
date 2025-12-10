from django.urls import path, include

from application.logus.views.rooms import available_room_view, create_quick_booking
from application.logus.views.dashboard import reception_dashboard, current_guests
from application.logus.views.room_availability_v2 import room_availability_matrix_v2_view
from HayatMedicalCRM.auth.decorators import receptionist_required

app_name = 'logus'

urlpatterns = [
    path('dashboard/', receptionist_required(reception_dashboard), name='logus_dashboard'),
    path('current-guests/', receptionist_required(current_guests), name='current_guests'),
    path('availability/', receptionist_required(room_availability_matrix_v2_view), name='check_availability'),  # RM2 - Updated to v2
    path('dashboard/quick-booking/', receptionist_required(create_quick_booking), name='create_quick_booking'),

    path('booking/', include('application.logus.urls.booking')),
    path('patients/', include('application.logus.urls.patients')),
    path('illness-histories/', include('application.logus.urls.illness_histories')),
    path('payments/', include('application.logus.urls.payments')),

    # RM2 - Room Availability V2
    path('rooms/availability-v2/', include('application.logus.urls.room_availability_v2')),

]
