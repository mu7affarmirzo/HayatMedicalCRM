from django.urls import path

from application.logus.views.patients import PatientListView, PatientCreateView, PatientDetailView, PatientUpdateView, \
    get_districts, patient_quick_create, add_new_patient

urlpatterns = [
    # Patient management URLs
    path('', PatientListView.as_view(), name='patient_list'),
    path('create/', PatientCreateView.as_view(), name='patient_create'),
    path('simple/create/', add_new_patient, name='simple_patient_create'),
    path('<int:pk>/', PatientDetailView.as_view(), name='patient_detail'),
    path('<int:pk>/update/', PatientUpdateView.as_view(), name='patient_update'),

    # AJAX URLs
    path('get-districts/', get_districts, name='get_districts'),
    path('quick-create/', patient_quick_create, name='patient_quick_create'),
]