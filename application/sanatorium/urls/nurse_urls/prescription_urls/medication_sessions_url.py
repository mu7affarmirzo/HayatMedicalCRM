from django.urls import path

from application.sanatorium.views.nurses_viewset.prescriptions.medication_sessions import *


# API URLs for medication session updates
urlpatterns = [
    # # Class-based views
    # path('api/medication-sessions/<int:session_id>/update-status/',
    #      MedicationSessionUpdateStatusView.as_view(),
    #      name='api_medication_session_update_status'),
    #
    # path('api/medication-sessions/<int:session_id>/update-notes/',
    #      MedicationSessionUpdateNotesView.as_view(),
    #      name='api_medication_session_update_notes'),

    # Alternative function-based views (comment out if using class-based views above)
    path('api/medication-sessions/<int:session_id>/update-status/',
         update_medication_session_status,
         name='api_medication_session_update_status'),

    path('api/medication-sessions/<int:session_id>/update-notes/',
         update_medication_session_notes,
         name='api_medication_session_update_notes'),
]

# If this is part of a larger app, you might need to include these in your main urls.py:
#
# In your main urls.py:
# from django.urls import path, include
#
# urlpatterns = [
#     # ... other urls
#     path('', include('your_app.urls')),  # Replace 'your_app' with your actual app name
# ]