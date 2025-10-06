from django.urls import path

from application.logus.views.payments import payments_dashboard

urlpatterns = [
    path('', payments_dashboard, name='payments_dashboard'),
]
