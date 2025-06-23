# core/views/auth.py
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.csrf import csrf_protect

from core.decorator import role_required
from core.models.role import RolesModel
from core.forms import LoginForm  # We'll create this next

# Move this to settings.py for better organization
USER_ROLE_REDIRECTS = {
    'doctor': 'doctors_main_screen',
    'nurse': 'nurses:nurses_main_screen',
}

# Default if no role match is found
DEFAULT_REDIRECT = 'home'


def get_redirect_url_for_role(user):
    """Get the appropriate redirect URL based on user's role"""
    try:
        target_role = user.roles.first()
        if target_role and target_role.name in USER_ROLE_REDIRECTS:
            return USER_ROLE_REDIRECTS[target_role.role.name]
    except Exception as e:
        # Log the error here
        pass
    return DEFAULT_REDIRECT


@csrf_protect
def login_view(request):
    """Login view with role-based redirection"""
    if request.user.is_authenticated:
        x = redirect_by_role(request.user)
        return x
        # return redirect_by_role(request.user)

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
                # return redirect_by_role(user)
                return redirect_by_role(request.user)
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

    if main_role == RolesModel.ADMIN:
        return redirect('admin_dashboard')
    elif main_role == RolesModel.MANAGER:
        return redirect('manager_dashboard')
    elif main_role == RolesModel.THERAPIST:
        return redirect('therapist_dashboard')
    elif main_role == RolesModel.RECEPTIONIST:
        return redirect('logus:logus_dashboard')
    elif main_role == RolesModel.DOCTOR:
        return redirect('doctors_main_screen')
    elif main_role.name == "massagist":
        return redirect('massagist:massagist_dashboard')
    elif main_role.name == "massagist_dispatcher":
        return redirect('massagist:dispatcher_dashboard')

    redirect_path = USER_ROLE_REDIRECTS.get(main_role.name, 'default_dashboard')
    return redirect(redirect_path)


@login_required
@role_required(RolesModel.ADMIN)
def admin_dashboard(request):
    """Admin dashboard view"""
    context = {
        'title': 'Admin Dashboard',
        'user': request.user
    }
    return render(request, 'dashboards/admin_dashboard.html', context)


@login_required
@role_required(RolesModel.MANAGER)
def manager_dashboard(request):
    """Manager dashboard view"""
    context = {
        'title': 'Manager Dashboard',
        'user': request.user
    }
    return render(request, 'dashboards/manager_dashboard.html', context)


@login_required
@role_required(RolesModel.THERAPIST)
def therapist_dashboard(request):
    """Therapist dashboard view"""
    context = {
        'title': 'Therapist Dashboard',
        'user': request.user
    }
    return render(request, 'dashboards/therapist_dashboard.html', context)


@login_required
@role_required(RolesModel.RECEPTIONIST)
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
