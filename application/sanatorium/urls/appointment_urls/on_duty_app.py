from django.urls import path

from application.sanatorium.views.appointment_views.on_duty_app import (
    AppointmentWithOnDutyDoctorCreateView,
    AppointmentWithOnDutyDoctorUpdateView,
    AppointmentWithOnDutyDoctorDetailView,
    AppointmentWithOnDutyDoctorListView,
)

urlpatterns = [
    path('illness/<int:history_id>/',
         AppointmentWithOnDutyDoctorListView.as_view(),
         name='on_duty_appointment_list'),

    path('illness/<int:history_id>/create/',
         AppointmentWithOnDutyDoctorCreateView.as_view(),
         name='on_duty_appointment_create'),

    path('detail/<int:pk>/',
         AppointmentWithOnDutyDoctorDetailView.as_view(),
         name='on_duty_appointment_detail'),

    path('update/<int:pk>/',
         AppointmentWithOnDutyDoctorUpdateView.as_view(),
         name='on_duty_appointment_update'),
]
