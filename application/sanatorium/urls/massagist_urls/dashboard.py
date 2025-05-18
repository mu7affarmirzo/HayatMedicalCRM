# urls.py
from django.urls import path
from application.sanatorium.views.massagists_viewset.therapist import sessions, dashboard

urlpatterns = [
    path('', dashboard.massagist_dashboard, name='massagist_dashboard'),
    path('api/sessions/<int:session_id>/complete/', sessions.complete_session, name='complete_session'),
    path('api/sessions/<int:session_id>/cancel/', sessions.cancel_session, name='cancel_session'),
    path('api/sessions/<int:session_id>/', sessions.get_session_details, name='get_session_details'),
    path('api/procedures/<int:procedure_id>/', sessions.get_procedure_details, name='get_procedure_details'),
]