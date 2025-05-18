from django.urls import path
from application.sanatorium.views.massagists_viewset.dispatcher import dashboard, calendar, reports

urlpatterns = [
    # Main dashboard view
    path('', dashboard.dispatcher_dashboard, name='dispatcher_dashboard'),

    # Procedure detail and edit
    path('procedure/<int:procedure_id>/', dashboard.procedure_detail, name='procedure_detail'),
    path('procedure/<int:procedure_id>/edit/', dashboard.procedure_edit, name='procedure_edit'),

    # Session management
    path('schedule-sessions/', dashboard.schedule_sessions, name='schedule_sessions'),
    path('add-session/', dashboard.add_session, name='add_session'),
    path('complete-session/', dashboard.complete_session, name='complete_session'),
    path('cancel-session/', dashboard.cancel_session, name='cancel_session'),

    # Calendar views
    path('calendar/', calendar.calendar_view, name='calendar_view'),
    path('calendar/events/', calendar.calendar_events, name='calendar_events'),

    path('reports/', reports.reports_view, name='reports_view'),
]
