from django.urls import path, include
from application.sanatorium.views.nurses_viewset.prescriptions.main_list import create_appointment, \
    cancel_appointment, view_appointment, main_prescription_list_view

urlpatterns = [
    path('<int:history_id>', main_prescription_list_view, name='prescription_list'),

    path('illness-history/<int:history_id>/prescription/', main_prescription_list_view, name='main_prescription_list'),

    path('procedures/', include('application.sanatorium.urls.nurse_urls.prescription_urls.procedures')),
    path('labs/', include('application.sanatorium.urls.nurse_urls.prescription_urls.labs')),
    path('medications/', include('application.sanatorium.urls.nurse_urls.prescription_urls.medications')),

    path('<int:history_id>/', main_prescription_list_view, name='main_prescription_list'),
    path('<int:history_id>/create-appointment/', create_appointment, name='create_appointment'),
    path('<int:history_id>/cancel-appointment/', cancel_appointment, name='cancel_appointment'),
    # You'll need this view to display appointment details
    path('appointments/<str:model_name>/<int:appointment_id>/', view_appointment, name='view_appointment'),

]