from django.urls import path
from application.sanatorium.views.doctors_viewset.diet import (
    diet_list_view,
    diet_create_view,
    diet_update_view,
    diet_delete_view,
    diet_detail_view
)

urlpatterns = [
    path('<int:history_id>/', diet_list_view, name='diet_list'),
    path('<int:history_id>/create/', diet_create_view, name='diet_create'),
    path('<int:history_id>/update/<int:diet_id>/', diet_update_view, name='diet_update'),
    path('<int:history_id>/delete/<int:diet_id>/', diet_delete_view, name='diet_delete'),
    path('<int:history_id>/detail/<int:diet_id>/', diet_detail_view, name='diet_detail'),
]