# In a file like your_app/context_processors.py
from core.models import IllnessHistory


def illness_history_context(request):
    """Add illness history ID to all template contexts"""
    illness_history_id = None
    active_page = {
        'title_page': '',
        'dashboard': '',
        'initial_appointment': '',
        'consulting_services': '',
        'proc_main_list': '',
        'documents': '',
        'diet': '',
        'timetable': '',
        # Add all possible sidebar sections
    }

    # Example logic to set active page
    path = request.path
    print(path)
    if '/appointments/init-app/' in path:
        active_page['initial_appointment'] = 'active'
    elif '/appointments/' in path and '/appointments/init-app/' not in path:
        active_page['consulting_and_med_services_page'] = 'active'
    elif '/documents/' in path:
        active_page['documents'] = 'active'
    elif '/histories/' in path:
        active_page['title_page'] = 'active'
    elif '/prescription/' in path:
        active_page['proc_main_list_page'] = 'active'

    if 'appointments/cardiologist/' in path:
        active_page['consulting_cardiologist'] = 'active'
    elif '/neurologist/' in path:
        active_page['consulting_neurologist'] = 'active'
    elif '/on-arrival/' in path:
        active_page['consulting_on_arrival'] = 'active'
    elif '/repeated-app/' in path:
        active_page['repeated_appointment'] = 'active'
    elif '/on-duty-app/' in path:
        active_page['on_duty_appointment'] = 'active'
    elif '/ekg-app/' in path:
        active_page['ekg_appointment'] = 'active'
    elif '/final-app/' in path:
        active_page['final_appointment'] = 'active'
    elif '/prescription/procedures/' in path:
        active_page['procedures'] = 'active'
    elif '/prescription/consulting/' in path:
        active_page['consulting'] = 'active'
    elif '/prescription/labs/' in path:
        active_page['labs'] = 'active'
    elif '/prescription/medications/' in path:
        active_page['medications'] = 'active'

    # Try to extract from URL parameters
    if 'history_id' in request.resolver_match.kwargs:
        illness_history_id = request.resolver_match.kwargs['history_id']
    elif 'illness_id' in request.resolver_match.kwargs:
        illness_history_id = request.resolver_match.kwargs['illness_id']

    # You can also try to get it from session if you store it there
    elif 'illness_history_id' in request.session:
        illness_history_id = request.session['illness_history_id']

    return {
        'illness_history_id': illness_history_id,
        # You could also fetch and include related data:
        'active_illness_history': None if illness_history_id is None else IllnessHistory.objects.filter(
            id=illness_history_id).first(),
        'active_page': active_page
    }
