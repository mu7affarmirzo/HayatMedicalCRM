# core/models/role.py
from django.db import models


class RolesModel(models.Model):
    """Role model for managing user permissions"""
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    # Define role constants for easier access
    ADMIN = 'admin'
    THERAPIST = 'therapist'
    DOCTOR = 'doctor'
    NURSE = 'nurse'
    RECEPTIONIST = 'receptionist'
    MANAGER = 'manager'
    WAREHOUSE = 'warehouse'

    # Default roles
    DEFAULT_ROLES = [
        (ADMIN, 'Administrator'),
        (DOCTOR, 'Doctor'),
        (NURSE, 'Nurse'),
        (THERAPIST, 'Therapist'),
        (RECEPTIONIST, 'Receptionist'),
        (MANAGER, 'Manager'),
        (WAREHOUSE, 'Warehouse'),
    ]

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


class PermissionsModel(models.Model):
    code = models.IntegerField()
    name = models.CharField(max_length=255)
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.name)


class RolePermissionModel(models.Model):
    permission = models.ForeignKey(PermissionsModel, related_name='role_permission_perm', on_delete=models.CASCADE)
    role = models.ForeignKey(RolesModel, related_name='role_permission_role', on_delete=models.CASCADE)
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.role) + "-" + str(self.permission)
