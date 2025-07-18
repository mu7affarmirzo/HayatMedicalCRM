from django.urls import path

from application.warehouse.views import company


urlpatterns = [

    path('', company.company_list, name='company_list'),
    path('create/', company.company_create, name='company_create'),
    path('<int:pk>/', company.company_detail, name='company_detail'),
    path('<int:pk>/update/', company.company_update, name='company_update'),

]