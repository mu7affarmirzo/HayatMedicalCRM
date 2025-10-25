from django.urls import path, include

urlpatterns = [
    path('', include('application.cashbox.urls.billing')),
]