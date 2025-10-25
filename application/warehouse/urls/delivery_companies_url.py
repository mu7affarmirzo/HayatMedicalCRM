from django.urls import path

from application.warehouse.views import delivery_company


urlpatterns = [
    path('', delivery_company.delivery_company_list, name='delivery_company_list'),
    path('create/', delivery_company.delivery_company_create, name='delivery_company_create'),
    path('<int:pk>/', delivery_company.delivery_company_detail, name='delivery_company_detail'),
    path('<int:pk>/update/', delivery_company.delivery_company_update, name='delivery_company_update'),
    path('<int:pk>/delete/', delivery_company.delivery_company_delete, name='delivery_company_delete'),
]
