# core/decorators.py
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import redirect
from django.http import HttpResponseForbidden
from django.contrib import messages


def role_required(role_name):
    """
    Decorator to check if a user has a specific role.
    Usage: @role_required('admin')
    """

    def decorator(view_func):
        def wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.error(request, 'Please login to access this page.')
                return redirect('login')

            if request.user.has_role(role_name) or request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            else:
                messages.error(request, 'You do not have permission to access this page.')
                return HttpResponseForbidden('Access Denied: Insufficient permissions.')

        return wrapped_view

    return decorator

