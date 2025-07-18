from django.urls import path

from application.warehouse.views import income


urlpatterns = [

    # Income/Receipts Management
    path('', income.income_list, name='income_list'),
    path('create/', income.income_create, name='income_create'),
    path('<int:pk>/', income.income_detail, name='income_detail'),
    path('<int:pk>/update/', income.income_update, name='income_update'),
    path('<int:pk>/accept/', income.income_accept, name='income_accept'),
    path('<int:pk>/reject/', income.income_reject, name='income_reject'),

]