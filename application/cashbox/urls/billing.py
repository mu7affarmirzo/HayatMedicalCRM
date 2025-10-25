from django.urls import path
from application.cashbox.views import billing, dashboard

app_name = 'cashbox'

urlpatterns = [
    # Dashboard
    path('', dashboard.dashboard, name='dashboard'),
    path('dashboard/', dashboard.dashboard_stats, name='dashboard_stats'),
    
    # Billing views
    path('billing/', billing.billing_list, name='billing_list'),
    path('billing/<int:booking_id>/', billing.billing_detail, name='billing_detail'),
    path('billing/<int:booking_id>/update-status/', billing.update_billing_status, name='update_billing_status'),
]