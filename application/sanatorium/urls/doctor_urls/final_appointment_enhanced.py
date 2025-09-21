from django.urls import path
from application.sanatorium.views.doctors_viewset.final_appointment_enhanced import (
    FinalAppointmentEnhancedCreateOrUpdateView,
    FinalAppointmentEnhancedCreateView,
    FinalAppointmentEnhancedUpdateView,
    FinalAppointmentEnhancedListView,
    FinalAppointmentEnhancedDetailView,
    export_final_appointment_pdf,
    export_final_appointment_word,
    get_patient_vitals_history
)

urlpatterns = [
    # Main views
    path('<int:history_id>/', FinalAppointmentEnhancedListView.as_view(), name='final_appointment_enhanced_list'),
    path('create/<int:history_id>/', FinalAppointmentEnhancedCreateOrUpdateView.as_view(), name='final_appointment_enhanced_create_or_update'),
    path('create-new/<int:history_id>/', FinalAppointmentEnhancedCreateView.as_view(), name='final_appointment_enhanced_create'),
    path('update/<int:pk>/', FinalAppointmentEnhancedUpdateView.as_view(), name='final_appointment_enhanced_update'),
    path('detail/<int:pk>/', FinalAppointmentEnhancedDetailView.as_view(), name='final_appointment_enhanced_detail'),
    
    # Export functionality
    path('export/pdf/<int:pk>/', export_final_appointment_pdf, name='final_appointment_export_pdf'),
    path('export/word/<int:pk>/', export_final_appointment_word, name='final_appointment_export_word'),
    
    # AJAX endpoints
    path('api/vitals-history/<int:history_id>/', get_patient_vitals_history, name='final_appointment_vitals_history'),
]