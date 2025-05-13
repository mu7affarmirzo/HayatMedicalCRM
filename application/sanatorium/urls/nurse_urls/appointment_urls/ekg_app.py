from django.urls import path

from application.sanatorium.views.nurses_viewset.appointment_views.ekg_app import (
    EkgAppointmentCreateView,
    EkgAppointmentUpdateView,
    EkgAppointmentDetailView,
    EkgAppointmentListView,
)

urlpatterns = [
    path('illness/<int:history_id>/',
         EkgAppointmentListView.as_view(),
         name='ekg_appointment_list'),

    path('illness/<int:history_id>/create/',
         EkgAppointmentCreateView.as_view(),
         name='ekg_appointment_create'),

    path('detail/<int:pk>/',
         EkgAppointmentDetailView.as_view(),
         name='ekg_appointment_detail'),

    path('update/<int:pk>/',
         EkgAppointmentUpdateView.as_view(),
         name='ekg_appointment_update'),
]
