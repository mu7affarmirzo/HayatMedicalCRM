import datetime

from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

from core.models import BaseAuditModel, IllnessHistory, Service, Account


class MedicalServiceModel(BaseAuditModel):
    STATE_CHOICES = (
        ('recommended', 'Рекомендовано'),
        ('assigned', 'Назначено'),
        ('cancelled', 'Отменено'),
        ('stopped', 'Остановлено'),
        ('dispatched', 'Отправлено'),
    )

    illness_history = models.ForeignKey(IllnessHistory, on_delete=models.CASCADE, null=True, blank=True, related_name='assigned_med_services')
    medical_service = models.ForeignKey(Service, on_delete=models.SET_NULL, null=True)
    price = models.BigIntegerField(default=0)
    consulted_doctor = models.ForeignKey(Account, blank=True, null=True, on_delete=models.SET_NULL,
                                         related_name='md_consulted_doctor')
    state = models.CharField(choices=STATE_CHOICES, default='assigned', max_length=50)