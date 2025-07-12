from django.urls import path

from application.logus.views.patients import (
    PatientListView, PatientDetailView, PatientUpdateView,
    get_districts, patient_quick_create, patient_create_view
)

urlpatterns = [
    # Patient management URLs
    path('', PatientListView.as_view(), name='patient_list'),
    path('create/', patient_create_view, name='patient_create'),
    path('<int:pk>/', PatientDetailView.as_view(), name='patient_detail'),
    path('<int:pk>/update/', PatientUpdateView.as_view(), name='patient_update'),

    path('get-districts/', get_districts, name='get_districts'),
    path('quick-create/', patient_quick_create, name='patient_quick_create'),
]