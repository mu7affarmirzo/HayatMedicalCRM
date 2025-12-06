from django.urls import path

from application.warehouse.views import income


urlpatterns = [
    # Income Management
    path('', income.income_list, name='income_list'),
    path('create/', income.income_create, name='create_income'),
    path('<int:pk>/', income.income_detail, name='income_detail'),
    path('<int:pk>/update/', income.income_update, name='income_update'),
    path('<int:pk>/delete/', income.income_delete, name='income_delete'),

    # Income Item Management
    path('<int:pk>/update-item/<int:item_pk>/', income.update_income_item, name='update_income_item'),
    path('<int:pk>/remove-item/<int:item_pk>/', income.remove_income_item, name='remove_income_item'),

    # AJAX endpoints for adding related entities
    path('add-delivery-company/', income.add_delivery_company, name='add_delivery_company'),
    path('add-medication/', income.add_medication, name='add_medication'),
]