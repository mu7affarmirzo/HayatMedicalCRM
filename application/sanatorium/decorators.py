from django.utils.decorators import method_decorator
from functools import wraps


def set_active_sidebar(active_section):
    """
    Decorator to set the active sidebar section.
    Works with both function-based and class-based views.

    Usage with function-based view:
    @set_active_sidebar('initial_appointment')
    def initial_appointment_detail(request, history_id):
        ...

    Usage with class-based view:
    @method_decorator(set_active_sidebar('initial_appointment'), name='dispatch')
    class InitialAppointmentView(DetailView):
        ...
    """

    def decorator(view_func_or_class):
        @wraps(view_func_or_class)
        def wrapper_for_function(request, *args, **kwargs):
            response = view_func_or_class(request, *args, **kwargs)

            # Only modify TemplateResponse objects or dictionaries (for render)
            if hasattr(response, 'context'):
                print('has context data')
                # For TemplateResponse objects
                active_page = response.context_data.get('active_page', {})
                for section in ['dashboard', 'initial_appointment', 'consulting_services',
                                'proc_main_list', 'documents', 'diet', 'timetable']:
                    active_page[section] = 'active' if section == active_section else ''
                response.context_data['active_page'] = active_page

            print('------------')

            return response

        # This will be used when applying the decorator directly to a class-based view's method
        def process_view_context(self, context):
            active_page = context.get('active_page', {})
            for section in ['dashboard', 'initial_appointment', 'consulting_services',
                            'proc_main_list', 'documents', 'diet', 'timetable']:
                active_page[section] = 'active' if section == active_section else ''
            context['active_page'] = active_page
            return context

        # Check if this is being applied to a class
        if not callable(view_func_or_class) or hasattr(view_func_or_class, 'as_view'):
            # For class-based views
            original_get_context_data = getattr(view_func_or_class, 'get_context_data', None)

            if original_get_context_data:
                def new_get_context_data(self, *args, **kwargs):
                    context = original_get_context_data(self, *args, **kwargs)
                    return process_view_context(self, context)

                view_func_or_class.get_context_data = new_get_context_data

            return view_func_or_class

        # For function-based views
        return wrapper_for_function

    return decorator