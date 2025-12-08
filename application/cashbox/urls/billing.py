from django.urls import path
from application.cashbox.views import billing, dashboard, payment, reports

app_name = 'cashbox'

urlpatterns = [
    # Dashboard
    path('', dashboard.dashboard, name='dashboard'),
    path('dashboard/', dashboard.dashboard_stats, name='dashboard_stats'),

    # Billing views
    path('billing/', billing.billing_list, name='billing_list'),
    path('billing/<int:booking_id>/', billing.billing_detail, name='billing_detail'),
    path('billing/<int:booking_id>/update-status/', billing.update_billing_status, name='update_billing_status'),

    # Payment processing endpoints
    path('billing/<int:booking_id>/accept-payment/', payment.accept_payment, name='accept_payment'),
    path('payment/<int:transaction_id>/receipt/', payment.payment_receipt, name='payment_receipt'),
    path('payment/<int:transaction_id>/refund/', payment.refund_payment, name='refund_payment'),

    # Payments list and detail
    path('payments/', payment.payments_list, name='payments_list'),
    path('payments/<int:transaction_id>/', payment.payment_detail, name='payment_detail'),

    # Reports
    path('reports/daily/', reports.report_daily, name='report_daily'),
    path('reports/period/', reports.report_period, name='report_period'),
    path('reports/cashier/', reports.report_cashier, name='report_cashier'),
    path('reports/payment-methods/', reports.report_payment_methods, name='report_payment_methods'),
]