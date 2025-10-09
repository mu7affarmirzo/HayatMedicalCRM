"""
Utility functions for checking user permissions programmatically
"""
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.shortcuts import redirect

from core.views import redirect_by_role


def user_has_role(user, *roles):
    """
    Check if user has any of the specified roles.

    Args:
        user: User object
        *roles: Variable number of role names or role objects

    Returns:
        bool: True if user has any of the roles, False otherwise

    Usage:
        if user_has_role(request.user, RolesModel.ADMIN, RolesModel.MANAGER):
            # Do something
    """
    if not user.is_authenticated:
        return False

    try:
        user_role = user.get_main_role()
    except AttributeError:
        return False

    for role in roles:
        if hasattr(role, 'name'):
            # It's a role object
            if user_role == role or user_role.name == role.name:
                return True
        else:
            # It's a string (role name)
            if user_role.name == role:
                return True

    return False


def user_has_all_roles(user, *roles):
    """
    Check if user has ALL of the specified roles.
    Useful when user can have multiple roles.

    Args:
        user: User object
        *roles: Variable number of role names or role objects

    Returns:
        bool: True if user has all roles, False otherwise
    """
    if not user.is_authenticated:
        return False

    try:
        user_roles = user.roles.all()
        user_role_names = [role.name for role in user_roles]
    except AttributeError:
        return False

    required_role_names = []
    for role in roles:
        if hasattr(role, 'name'):
            required_role_names.append(role.name)
        else:
            required_role_names.append(role)

    return all(role_name in user_role_names for role_name in required_role_names)


def require_role(user, *roles, raise_exception=True, message=None):
    """
    Check if user has required role(s) and optionally raise exception.

    Args:
        user: User object
        *roles: Variable number of role names or role objects
        raise_exception: If True, raises PermissionDenied if check fails
        message: Custom error message

    Returns:
        bool: True if user has permission

    Raises:
        PermissionDenied: If user doesn't have permission and raise_exception=True

    Usage in view:
        def my_view(request):
            require_role(request.user, RolesModel.ADMIN, RolesModel.MANAGER)
            # Rest of view code
    """
    has_permission = user_has_role(user, *roles)

    if not has_permission and raise_exception:
        error_message = message or f'У вас нет доступа. Требуется роль: {", ".join([str(r) for r in roles])}'
        raise PermissionDenied(error_message)

    return has_permission


def check_role_or_redirect(request, *roles, redirect_view=None):
    """
    Check user role and redirect if they don't have permission.

    Args:
        request: HttpRequest object
        *roles: Variable number of role names or role objects
        redirect_view: View name to redirect to (default: user's dashboard)

    Returns:
        None if user has permission, HttpResponse redirect if not

    Usage in view:
        def my_view(request):
            redirect_response = check_role_or_redirect(
                request,
                RolesModel.ADMIN,
                RolesModel.MANAGER
            )
            if redirect_response:
                return redirect_response

            # Rest of view code
    """
    has_permission = user_has_role(request.user, *roles)

    if not has_permission:
        messages.error(
            request,
            f'У вас нет доступа к этому разделу. Требуется роль: {", ".join([str(r) for r in roles])}'
        )

        if redirect_view:
            return redirect(redirect_view)
        else:
            # Redirect to user's appropriate dashboard
            return redirect_by_role(request.user)

    return None


def is_admin(user):
    """Check if user is admin"""
    from core.models import RolesModel
    return user_has_role(user, RolesModel.ADMIN)


def is_manager(user):
    """Check if user is manager"""
    from core.models import RolesModel
    return user_has_role(user, RolesModel.MANAGER)


def is_receptionist(user):
    """Check if user is receptionist"""
    from core.models import RolesModel
    return user_has_role(user, RolesModel.RECEPTIONIST)


def is_therapist(user):
    """Check if user is therapist"""
    from core.models import RolesModel
    return user_has_role(user, RolesModel.THERAPIST)


def is_doctor(user):
    """Check if user is doctor"""
    from core.models import RolesModel
    return user_has_role(user, RolesModel.DOCTOR)


def can_access_logus(user):
    """Check if user can access the logus (reception) system"""
    from core.models import RolesModel
    return user_has_role(
        user,
        RolesModel.RECEPTIONIST,
        RolesModel.ADMIN,
        RolesModel.MANAGER
    )


def can_access_admin_panel(user):
    """Check if user can access admin panel"""
    from core.models import RolesModel
    return user_has_role(user, RolesModel.ADMIN, RolesModel.MANAGER)


def can_manage_rooms(user):
    """Check if user can manage rooms"""
    from core.models import RolesModel
    return user_has_role(user, RolesModel.ADMIN, RolesModel.MANAGER)


def can_view_statistics(user):
    """Check if user can view statistics"""
    from core.models import RolesModel
    return user_has_role(
        user,
        RolesModel.ADMIN,
        RolesModel.MANAGER,
        RolesModel.RECEPTIONIST
    )