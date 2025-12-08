import datetime

from django.db import models

from core.models import BaseAuditModel

from django.db import models
from django.core.exceptions import ValidationError
from core.models import BaseAuditModel
import datetime


# New models for region and district
class Region(models.Model):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50, blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ('name',)


class District(models.Model):
    region = models.ForeignKey(Region, on_delete=models.CASCADE, related_name='districts')
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50, blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ('name',)


class PatientModel(BaseAuditModel):
    f_name = models.CharField(max_length=255)
    mid_name = models.CharField(max_length=255, null=True, blank=True)
    l_name = models.CharField(max_length=255)
    email = models.EmailField(null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    home_phone_number = models.CharField(max_length=255, blank=True, null=True)
    mobile_phone_number = models.CharField(max_length=255, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    additional_info = models.JSONField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    doc_type = models.CharField(max_length=255, blank=True, null=True)
    doc_number = models.CharField(max_length=255, blank=True, null=True)
    issued_data = models.DateField(auto_now=True)
    INN = models.CharField(max_length=255, blank=True, null=True)
    country = models.CharField(max_length=255, blank=True, null=True)

    # New fields for region and district
    region = models.ForeignKey(Region, on_delete=models.SET_NULL, null=True, blank=True, related_name='patients')
    district = models.ForeignKey(District, on_delete=models.SET_NULL, null=True, blank=True, related_name='patients')

    last_visit_at = models.DateTimeField(auto_now=True)
    gender = models.BooleanField()
    gestational_age = models.IntegerField(null=True, blank=True)

    @property
    def age(self):
        return datetime.date.today().year - self.date_of_birth.year

    @property
    def formatted_gender(self):
        return 'Мужской' if self.gender is True else 'Женский'

    def to_result(self):
        return {
            'age': self.age,
            'name': self.full_name,
            'gender': self.gender
        }

    @property
    def full_name(self):
        try:
            mid_name = self.mid_name
        except:
            mid_name = ''

        return f"{self.l_name} {self.f_name} {mid_name}"

    def __str__(self):
        try:
            mid_name = self.mid_name
        except:
            mid_name = ''

        return f"{self.l_name} {self.f_name} {mid_name}"

    class Meta:
        ordering = ('-created_at',)
        indexes = [
            # TASK-052: Database optimization indexes
            models.Index(fields=['f_name', 'l_name'], name='idx_patient_name'),
            models.Index(fields=['mobile_phone_number'], name='idx_patient_mobile'),
            models.Index(fields=['email'], name='idx_patient_email'),
            models.Index(fields=['date_of_birth'], name='idx_patient_dob'),
            models.Index(fields=['region', 'district'], name='idx_patient_location'),
            models.Index(fields=['is_active'], name='idx_patient_active'),
            models.Index(fields=['-created_at'], name='idx_patient_created'),
        ]


