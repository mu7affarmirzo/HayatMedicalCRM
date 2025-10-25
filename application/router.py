from django.urls import path, include


urlpatterns = [
    path('logus/', include('application.logus.router')),
    path('sanatorium/', include('application.sanatorium.router')),
    path('warehouse/', include('application.warehouse.router')),
    path('cashbox/', include('application.cashbox.router')),
]
