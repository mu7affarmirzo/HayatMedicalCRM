from django.urls import path

from application.warehouse.views import income


urlpatterns = [
    # Income Management
    path('', income.income_list, name='income_list'),
    path('create/', income.income_create, name='create_income'),
    path('<int:pk>/', income.income_detail, name='income_detail'),
    path('<int:pk>/update/', income.income_update, name='income_update'),
    path('<int:pk>/delete/', income.income_delete, name='income_delete'),

    # AJAX endpoints for adding related entities
    path('add-delivery-company/', income.add_delivery_company, name='add_delivery_company'),
    path('add-medication/', income.add_medication, name='add_medication'),
]