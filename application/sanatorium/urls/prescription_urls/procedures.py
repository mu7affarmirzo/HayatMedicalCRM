from django.urls import path, include
from application.sanatorium.views.prescriptions.main_list import main_prescription_list_view
from application.sanatorium.views.prescriptions import procedures


urlpatterns = [
    path('<int:history_id>', main_prescription_list_view, name='prescription_list'),

    path('illness-history/<int:history_id>/prescription/', main_prescription_list_view, name='main_prescription_list'),

    # Procedure URLs
    path('<int:procedure_id>/', procedures.procedure_detail, name='procedure_detail'),
    path('create/<int:history_id>/', procedures.procedure_create, name='procedure_create'),
    path('edit/<int:procedure_id>/', procedures.procedure_edit, name='procedure_edit'),
    path('delete/<int:procedure_id>/', procedures.procedure_delete, name='procedure_delete'),
    path('sessions/<int:session_id>/update/', procedures.update_session_status,
         name='update_session_status'),

    path('get-services-by-type/', procedures.get_services_by_type, name='get_services_by_type'),
    path('load_services/', procedures.load_services, name='load_services'),

]