# core/views/auth.py
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.csrf import csrf_protect

from core.decorator import role_required
from core.models.role import Role
from core.forms import LoginForm  # We'll create this next


@csrf_protect
def login_view(request):
    """Login view with role-based redirection"""
    if request.user.is_authenticated:
        return redirect_by_role(request.user)

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            user = authenticate(request, email=email, password=password)

            if user is not None and user.is_active:
                login(request, user)
                next_url = request.GET.get('next')
                if next_url:
                    return redirect(next_url)
                return redirect_by_role(user)
            else:
                messages.error(request, 'Invalid email or password.')
    else:
        form = LoginForm()

    return render(request, 'login.html', {'form': form})


def logout_view(request):
    """Logout view"""
    logout(request)
    return redirect('login')


def redirect_by_role(user):
    """Redirect user based on their primary role"""
    main_role = user.get_main_role()

    if main_role == Role.ADMIN:
        return redirect('admin_dashboard')
    elif main_role == Role.MANAGER:
        return redirect('manager_dashboard')
    elif main_role == Role.THERAPIST:
        return redirect('therapist_dashboard')
    elif main_role == Role.RECEPTIONIST:
        return redirect('reception_dashboard')

    # Default fallback
    return redirect('default_dashboard')


@login_required
@role_required(Role.ADMIN)
def admin_dashboard(request):
    """Admin dashboard view"""
    context = {
        'title': 'Admin Dashboard',
        'user': request.user
    }
    return render(request, 'dashboards/admin_dashboard.html', context)


@login_required
@role_required(Role.MANAGER)
def manager_dashboard(request):
    """Manager dashboard view"""
    context = {
        'title': 'Manager Dashboard',
        'user': request.user
    }
    return render(request, 'dashboards/manager_dashboard.html', context)


@login_required
@role_required(Role.THERAPIST)
def therapist_dashboard(request):
    """Therapist dashboard view"""
    context = {
        'title': 'Therapist Dashboard',
        'user': request.user
    }
    return render(request, 'dashboards/therapist_dashboard.html', context)


@login_required
@role_required(Role.RECEPTIONIST)
def reception_dashboard(request):
    """Reception dashboard view"""
    context = {
        'title': 'Reception Dashboard',
        'user': request.user
    }
    return render(request, 'dashboards/reception_dashboard.html', context)


@login_required
def default_dashboard(request):
    """Default dashboard for users without a specific role"""
    context = {
        'title': 'Dashboard',
        'user': request.user
    }
    return render(request, 'dashboards/default_dashboard.html', context)
