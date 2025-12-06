from django.urls import path

from application.warehouse.views import transfers

urlpatterns = [
    # Transfer Management
    path('', transfers.transfer_list, name='transfer_list'),
    path('create/', transfers.transfer_create, name='transfer_create'),
    path('<int:pk>/', transfers.transfer_detail, name='transfer_detail'),
    path('<int:pk>/add-items/', transfers.transfer_add_items, name='transfer_add_items'),
    path('<int:pk>/update-state/', transfers.transfer_update_state, name='transfer_update_state'),
    path('<int:pk>/update-item/<int:item_pk>/', transfers.update_transfer_item, name='update_transfer_item'),
    path('<int:pk>/remove-item/<int:item_pk>/', transfers.remove_transfer_item, name='remove_transfer_item'),
    path('get-medication-batches/', transfers.get_medication_batches, name='get_medication_batches'),
]