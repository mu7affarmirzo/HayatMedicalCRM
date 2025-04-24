import datetime

from django.db import models

from core.models import BaseAuditModel


class PatientModel(BaseAuditModel):
    f_name = models.CharField(max_length=255)
    mid_name = models.CharField(max_length=255, null=True, blank=True)
    l_name = models.CharField(max_length=255)
    email = models.EmailField(null=True, blank=True)
    date_of_birth = models.DateField(auto_now=False)
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
    last_visit_at = models.DateTimeField(auto_now=True)

    gender = models.BooleanField()
    gestational_age = models.IntegerField(null=True, blank=True)

    @property
    def age(self):
        return datetime.date.today().year - self.date_of_birth.year

    @property
    def formatted_gender(self):
        return 'Мужской' if self.gender is True else 'Женскый'

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

        return f"{self.f_name} {self.l_name} {mid_name}"

    class Meta:
        ordering = ('-created_at', )
