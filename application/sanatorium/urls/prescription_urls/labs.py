from django.urls import path, include
from application.sanatorium.views.prescriptions import assigned_labs


urlpatterns = [

    path('assigned/create/', assigned_labs.AssignedLabsCreateView.as_view(), name='assigned_labs_create'),
# In urls.py
#     path('assigned/create/<int:history_id>/', assigned_labs.assign_lab_create, name='assigned_labs_create_for_patient'),

    path('assigned/create/<int:illness_history_id>/', assigned_labs.AssignedLabsCreateView.as_view(),
         name='assigned_labs_create_for_patient'),
    path('assigned/<int:pk>/', assigned_labs.AssignedLabsDetailView.as_view(), name='assigned_labs_detail'),
    path('assigned/<int:pk>/update/', assigned_labs.AssignedLabsUpdateView.as_view(), name='assigned_labs_update'),
    path('assigned/<int:pk>/delete/', assigned_labs.AssignedLabsDeleteView.as_view(), name='assigned_labs_delete'),

    # AJAX paths for dynamic filtering
    path('get-by-category/', assigned_labs.get_labs_by_category, name='get_labs_by_category'),
    path('assigned/<int:pk>/update-state/<str:new_state>/', assigned_labs.update_lab_state, name='update_lab_state'),
]