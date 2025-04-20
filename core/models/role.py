# core/models/role.py
from django.db import models


class Role(models.Model):
    """Role model for managing user permissions"""
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    # Define role constants for easier access
    ADMIN = 'admin'
    THERAPIST = 'therapist'
    RECEPTIONIST = 'receptionist'
    MANAGER = 'manager'

    # Default roles
    DEFAULT_ROLES = [
        (ADMIN, 'Administrator'),
        (THERAPIST, 'Therapist'),
        (RECEPTIONIST, 'Receptionist'),
        (MANAGER, 'Manager'),
    ]

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']
