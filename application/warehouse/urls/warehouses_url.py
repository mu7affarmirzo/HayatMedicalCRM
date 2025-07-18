from django.urls import path

from application.warehouse.views import warehouses


urlpatterns = [

    # Warehouse Management
    path('', warehouses.warehouse_list, name='warehouse_list'),
    path('create/', warehouses.warehouse_create, name='warehouse_create'),
    path('<int:pk>/', warehouses.warehouse_detail, name='warehouse_detail'),
    path('<int:pk>/update/', warehouses.warehouse_update, name='warehouse_update'),
    path('transfer/', warehouses.warehouse_transfer, name='warehouse_transfer'),
    path('stats/', warehouses.warehouse_stats, name='warehouse_stats'),
    path('batches/', warehouses.get_batches, name='get_batches'),
    path('medicaion-info/', warehouses.get_medication_info, name='get_medication_info'),

]