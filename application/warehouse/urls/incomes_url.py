from django.urls import path

from application.warehouse.views import income, incomes_test


urlpatterns = [

    # Income/Receipts Management
    path('', income.income_list, name='income_list'),
    path('create/', income.income_create, name='income_create'),
    path('<int:pk>/', income.income_detail, name='income_detail'),
    path('<int:pk>/update/', income.income_update, name='income_update'),
    path('<int:pk>/accept/', income.income_accept, name='income_accept'),
    path('<int:pk>/reject/', income.income_reject, name='income_reject'),


    path('test-create/', incomes_test.create_income, name='create_income'),
    path('search-medication-qr/', incomes_test.search_medication_by_qr, name='search_medication_by_qr'),
    path('medication-info/<int:medication_id>/', incomes_test.get_medication_info, name='get_medication_info'),


]