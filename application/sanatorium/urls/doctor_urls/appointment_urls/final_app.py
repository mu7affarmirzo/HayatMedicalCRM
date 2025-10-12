from django.urls import path
from application.sanatorium.views.doctors_viewset.appointment_views.final_app import (
    FinalAppointmentListView,
    FinalAppointmentDetailView,
    FinalAppointmentUpdateView, FinalAppointmentCreateOrUpdateView,
    FinalAppointmentDownloadView,
)

urlpatterns = [
    path('illness/<int:history_id>/',
         FinalAppointmentListView.as_view(),
         name='final_appointment_list'),

    path('illness/<int:history_id>/create/',
         FinalAppointmentCreateOrUpdateView.as_view(),
         name='final_appointment_create'),

    path('detail/<int:pk>/',
         FinalAppointmentDetailView.as_view(),
         name='final_appointment_detail'),

    path('update/<int:pk>/',
         FinalAppointmentUpdateView.as_view(),
         name='final_appointment_update'),

    path('download/<int:pk>/',
         FinalAppointmentDownloadView.as_view(),
         name='final_appointment_download'),
]
