from django.urls import path

from application.warehouse.views import account_transfers

urlpatterns = [
    # Account Transfer Management
    path('', account_transfers.account_transfer_list, name='account_transfer_list'),
    path('create/', account_transfers.account_transfer_create, name='account_transfer_create'),
    path('<int:pk>/', account_transfers.account_transfer_detail, name='account_transfer_detail'),
    path('<int:pk>/add-items/', account_transfers.account_transfer_add_items, name='account_transfer_add_items'),
    path('<int:pk>/update-state/', account_transfers.account_transfer_update_state, name='account_transfer_update_state'),
    path('<int:pk>/update-item/<int:item_pk>/', account_transfers.update_account_transfer_item, name='update_account_transfer_item'),
    path('<int:pk>/remove-item/<int:item_pk>/', account_transfers.remove_account_transfer_item, name='remove_account_transfer_item'),
    path('get-medication-batches/', account_transfers.get_medication_batches, name='get_account_medication_batches'),
]