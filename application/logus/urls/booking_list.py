from django.urls import path
from application.logus.views import booking_list as views

urlpatterns = [
    # Dashboard and Booking list
    path('dashboard', views.dashboard, name='dashboard'),
    path('list/', views.booking_list, name='booking_list'),
    path('status/<int:booking_id>/', views.update_booking_status, name='update_booking_status'),
]