from django.urls import path, include
from application.sanatorium.views.prescriptions import main_prescription_list_view


urlpatterns = [
    path('<int:history_id>', main_prescription_list_view, name='prescription_list'),
]