from django.urls import path

from application.sanatorium.views.nurses_viewset.account_transfers import (
    account_transfer_list,
    account_transfer_detail,
    account_transfer_update_state,
    account_transfer_return,
    account_transfer_usage
)


urlpatterns = [
    path('', account_transfer_list, name='list'),
    path('<int:pk>/', account_transfer_detail, name='detail'),
    path('<int:pk>/update-state/', account_transfer_update_state, name='update_state'),
    path('<int:pk>/return/', account_transfer_return, name='return'),
    path('<int:pk>/usage/', account_transfer_usage, name='usage'),
]