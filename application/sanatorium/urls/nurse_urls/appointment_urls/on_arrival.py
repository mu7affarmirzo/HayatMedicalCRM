from django.urls import path

from application.sanatorium.views.doctors_viewset.appointment_views.on_arrival import (
    AppointmentWithOnDutyDoctorOnArrivalCreateView,
    AppointmentWithOnDutyDoctorOnArrivalUpdateView,
    AppointmentWithOnDutyDoctorOnArrivalDetailView,
    AppointmentWithOnDutyDoctorOnArrivalListView,
)

urlpatterns = [
    path('illness/<int:history_id>/',
         AppointmentWithOnDutyDoctorOnArrivalListView.as_view(),
         name='on_arrival_consulting_list'),

    path('illness/<int:history_id>/create/',
         AppointmentWithOnDutyDoctorOnArrivalCreateView.as_view(),
         name='on_arrival_consulting_create'),

    path('detail/<int:pk>/',
         AppointmentWithOnDutyDoctorOnArrivalDetailView.as_view(),
         name='on_arrival_consulting_detail'),

    path('update/<int:pk>/',
         AppointmentWithOnDutyDoctorOnArrivalUpdateView.as_view(),
         name='on_arrival_consulting_update'),
]