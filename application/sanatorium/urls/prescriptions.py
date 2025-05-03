from django.urls import path, include
from application.sanatorium.views.prescriptions.main_list import main_prescription_list_view


urlpatterns = [
    path('<int:history_id>', main_prescription_list_view, name='prescription_list'),

    path('illness-history/<int:history_id>/prescription/', main_prescription_list_view, name='main_prescription_list'),

    path('procedures/', include('application.sanatorium.urls.prescription_urls.procedures')),
    path('labs/', include('application.sanatorium.urls.prescription_urls.labs')),
    path('medications/', include('application.sanatorium.urls.prescription_urls.medications')),
]