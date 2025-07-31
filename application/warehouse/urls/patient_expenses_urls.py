# warehouse/urls.py (or add to existing warehouse URLs)
from django.urls import path

from application.warehouse.views import patients_expenses_view


urlpatterns = [

    # Medication expenses tracking
    path('medication-expenses/',
         patients_expenses_view.medication_expenses_dashboard,
         name='medication_expenses_dashboard'),

    path('medication-expenses/export/',
         patients_expenses_view.medication_expenses_export,
         name='medication_expenses_export'),
]
