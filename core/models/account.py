from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager

from core.models.role import RolesModel


class MyAccountManager(BaseUserManager):
    def create_user(self, email, username, password=None):
        if not email:
            raise ValueError("Users must have email")
        if not username:
            raise ValueError("Users must have username")

        user = self.model(
            email=self.normalize_email(email),
            username=username,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, password):
        user = self.create_user(
            email=self.normalize_email(email),
            password=password,
            username=username,
        )
        user.is_admin = True
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user


class Account(AbstractBaseUser):
    email = models.EmailField(verbose_name="email", max_length=60, unique=True)
    username = models.CharField(max_length=30, unique=True)
    f_name = models.CharField(max_length=50, null=True)
    l_name = models.CharField(max_length=50, null=True)
    m_name = models.CharField(max_length=50, null=True)
    phone_number = models.CharField(max_length=30, null=True)
    tg_username = models.CharField(max_length=255, null=True, blank=True)
    sex = models.BooleanField(default=True)
    date_joined = models.DateTimeField(verbose_name='date joined', auto_now_add=True)
    last_login = models.DateTimeField(verbose_name='last login', auto_now=True)
    color = models.CharField(max_length=255, null=True, blank=True)
    is_admin = models.BooleanField(default=False)
    is_therapist = models.BooleanField(default=False, null=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    roles = models.ManyToManyField(RolesModel, related_name='users', blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    objects = MyAccountManager()

    def __str__(self):
        return self.email

    # Add methods for role checking
    def has_role(self, role_name):
        """Check if user has a specific role"""
        return self.roles.filter(name=role_name, is_active=True).exists()

    def get_main_role(self):
        """Return the primary role for the user (for redirection)"""
        # Priority order: Admin > Manager > Therapist > Receptionist
        if self.has_role(RolesModel.ADMIN) or self.is_superuser:
            return RolesModel.ADMIN
        elif self.has_role(RolesModel.MANAGER):
            return RolesModel.MANAGER
        elif self.has_role(RolesModel.THERAPIST):
            return RolesModel.THERAPIST
        elif self.has_role(RolesModel.RECEPTIONIST):
            return RolesModel.RECEPTIONIST
        elif self.has_role(RolesModel.DOCTOR):
            return RolesModel.DOCTOR
        elif self.has_role(RolesModel.NURSE):
            return RolesModel.NURSE
        elif self.has_role(RolesModel.WAREHOUSE):
            return RolesModel.WAREHOUSE
        elif self.has_role(RolesModel.CASHBOX):
            return RolesModel.CASHBOX
        return self.roles.first()

    # For checking permissions. to keep it simple all admin have ALL permissons
    def has_perm(self, perm, obj=None):
        return self.is_admin

    # Does this user have permission to view this app? (ALWAYS YES FOR SIMPLICITY)
    def has_module_perms(self, app_label):
        return True

    @property
    def full_name(self):
        try:
            m_name = self.m_name
        except:
            m_name = ''

        return f"{m_name} {self.f_name} {self.l_name}"

    @property
    def unread_notifications(self):
        return self.notifications.filter(state=False)

