from django.urls import path
from application.sanatorium.views.doctors_viewset.prescriptions import assigned_labs


urlpatterns = [

    path('assigned/create/<int:illness_history_id>/', assigned_labs.AssignedLabsCreateView.as_view(),
         name='assigned_labs_create_for_patient'),
    path('assigned/<int:pk>/', assigned_labs.AssignedLabsDetailView.as_view(), name='assigned_labs_detail'),
    path('assigned/<int:pk>/update/', assigned_labs.AssignedLabsUpdateView.as_view(), name='assigned_labs_update'),
    path('assigned/<int:pk>/delete/', assigned_labs.AssignedLabsDeleteView.as_view(), name='assigned_labs_delete'),

    path('assigned/<int:pk>/update-state/<str:new_state>/', assigned_labs.update_lab_state, name='update_lab_state'),

    # AJAX paths for dynamic filtering
    path('get-by-category/', assigned_labs.get_labs_by_category, name='get_labs_by_category'),

    path('add-lab-result/<int:assigned_lab_id>/', assigned_labs.add_lab_result, name='add_lab_result'),
    path('view-lab-results/<int:assigned_lab_id>/', assigned_labs.view_lab_results, name='view_lab_results'),

]