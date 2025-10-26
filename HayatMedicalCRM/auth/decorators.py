from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

from core.views import redirect_by_role


def role_required(*allowed_roles, redirect_to_dashboard=True):
    """
    Decorator to check if user has one of the allowed roles.

    Usage:
        @role_required(RolesModel.RECEPTIONIST, RolesModel.ADMIN)
        def my_view(request):
            ...

    Args:
        *allowed_roles: Variable number of role names or role objects
        redirect_to_dashboard: If True, redirects to user's dashboard.
                              If False, returns 403 Forbidden.
    """

    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            user = request.user

            # Get user's main role
            try:
                user_role = user.get_main_role()
            except AttributeError:
                messages.error(request, 'Ошибка определения роли пользователя.')
                return redirect('login')

            # Check if user has any of the allowed roles
            has_permission = False

            for allowed_role in allowed_roles:
                # Handle both role objects and role names (strings)
                if hasattr(allowed_role, 'name'):
                    # It's a role object
                    if user_role == allowed_role or user_role.name == allowed_role.name:
                        has_permission = True
                        break
                else:
                    if user_role == allowed_role:
                        has_permission = True
                        break

            if not has_permission:
                messages.error(
                    request,
                    'У вас нет доступа к этому разделу. '
                    f'Требуется роль: {", ".join([str(r) for r in allowed_roles])}'
                )

                if redirect_to_dashboard:
                    # Redirect to user's appropriate dashboard
                    return redirect_by_role(user)
                else:
                    return HttpResponseForbidden(
                        '<h1>403 Forbidden</h1>'
                        '<p>У вас нет доступа к этому разделу.</p>'
                    )
            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator


def admin_required(view_func):
    """
    Decorator to check if user is admin.
    Shortcut for @role_required(RolesModel.ADMIN)
    """
    from core.models import RolesModel  # Import here to avoid circular import
    return role_required(RolesModel.ADMIN)(view_func)


def receptionist_required(view_func):
    """
    Decorator to check if user is receptionist or admin.
    """
    from core.models import RolesModel
    return role_required(RolesModel.RECEPTIONIST, RolesModel.ADMIN)(view_func)


def nurse_required(view_func):
    """
    Decorator to check if user is nurse or admin.
    """
    from core.models import RolesModel
    return role_required(RolesModel.NURSE, RolesModel.ADMIN)(view_func)


def therapist_required(view_func):
    """
    Decorator to check if user is therapist or admin.
    """
    from core.models import RolesModel
    return role_required(RolesModel.THERAPIST, RolesModel.ADMIN)(view_func)


def doctor_required(view_func):
    """
    Decorator to check if user is doctor or admin.
    """
    from core.models import RolesModel
    return role_required(RolesModel.DOCTOR, RolesModel.ADMIN)(view_func)


def warehouse_manager_required(view_func):
    """
    Decorator to check if user is warehouse manager or admin.
    """
    from core.models import RolesModel
    return role_required(RolesModel.WAREHOUSE, RolesModel.ADMIN)(view_func)


def cashbox_required(view_func):
    """
    Decorator to check if user is cashbox or admin.
    """
    from core.models import RolesModel
    return role_required(RolesModel.CASHBOX, RolesModel.ADMIN)(view_func)


def manager_required(view_func):
    """
    Decorator to check if user is manager or admin.
    """
    from core.models import RolesModel
    return role_required(RolesModel.MANAGER, RolesModel.ADMIN)(view_func)


# Additional utility decorator for checking multiple permissions
def any_role_required(*allowed_roles):
    """
    Decorator that allows access if user has ANY of the specified roles.
    Same as role_required but with a more explicit name.
    """
    return role_required(*allowed_roles)


def all_roles_required(*required_roles):
    """
    Decorator that requires user to have ALL specified roles.
    Useful for users with multiple roles.
    """

    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            user = request.user

            # Get all user roles
            try:
                user_roles = user.roles.all()  # Assuming ManyToMany relationship
                user_role_names = [role.name for role in user_roles]
            except AttributeError:
                messages.error(request, 'Ошибка определения ролей пользователя.')
                return redirect('login')

            # Check if user has all required roles
            required_role_names = []
            for role in required_roles:
                if hasattr(role, 'name'):
                    required_role_names.append(role.name)
                else:
                    required_role_names.append(role)

            has_all_roles = all(
                role_name in user_role_names
                for role_name in required_role_names
            )

            if not has_all_roles:
                messages.error(
                    request,
                    f'У вас нет доступа. Требуются роли: {", ".join(required_role_names)}'
                )
                return redirect_by_role(user)

            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator



class NurseRequiredMixin(UserPassesTestMixin):
    """Mixin to ensure that only nurses or admins can access the view"""

    def test_func(self):
        user = self.request.user
        # Check if user has NURSE or ADMIN role
        from core.models import RolesModel
        return user.has_role(RolesModel.NURSE) or user.has_role(RolesModel.ADMIN) or user.is_superuser


class DoctorRequiredMixin(UserPassesTestMixin):
    """Mixin to ensure that only nurses or admins can access the view"""

    def test_func(self):
        user = self.request.user
        # Check if user has NURSE or ADMIN role
        from core.models import RolesModel
        return user.has_role(RolesModel.DOCTOR) or user.has_role(RolesModel.ADMIN) or user.is_superuser


class WarehouseManagerRequiredMixin(UserPassesTestMixin):
    """Mixin to ensure that only nurses or admins can access the view"""

    def test_func(self):
        user = self.request.user
        # Check if user has NURSE or ADMIN role
        from core.models import RolesModel
        return user.has_role(RolesModel.WAREHOUSE) or user.has_role(RolesModel.ADMIN) or user.is_superuser


class CashboxRequiredMixin(UserPassesTestMixin):
    """Mixin to ensure that only cashbox or admins can access the view"""

    def test_func(self):
        user = self.request.user
        # Check if user has CASHBOX or ADMIN role
        from core.models import RolesModel
        return user.has_role(RolesModel.CASHBOX) or user.has_role(RolesModel.ADMIN) or user.is_superuser