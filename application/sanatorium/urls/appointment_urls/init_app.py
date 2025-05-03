from django.urls import path

from application.sanatorium.views.appointment_views.init_app import initial_appointment_detail, initial_appointment_update

urlpatterns = [
    path('<int:history_id>/', initial_appointment_detail, name='initial_appointment_detail'),
    path('<int:history_id>/update/', initial_appointment_update, name='initial_appointment_update'),
]
