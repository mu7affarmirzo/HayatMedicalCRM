from django.urls import path

from application.sanatorium.views.nurses_viewset.appointment_views.repeated_app import (
    RepeatedAppointmentCreateView,
    RepeatedAppointmentUpdateView,
    RepeatedAppointmentDetailView,
    RepeatedAppointmentListView,
)

urlpatterns = [
    path('illness/<int:history_id>/',
         RepeatedAppointmentListView.as_view(),
         name='repeated_appointment_list'),

    path('illness/<int:history_id>/create/',
         RepeatedAppointmentCreateView.as_view(),
         name='repeated_appointment_create'),

    path('detail/<int:pk>/',
         RepeatedAppointmentDetailView.as_view(),
         name='repeated_appointment_detail'),

    path('update/<int:pk>/',
         RepeatedAppointmentUpdateView.as_view(),
         name='repeated_appointment_update'),
]
