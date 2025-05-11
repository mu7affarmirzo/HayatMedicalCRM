# models.py
from django.db import models
from django.conf import settings

from core.models import upload_documents_location, BaseAuditModel


class Document(BaseAuditModel):
    """Model to store documents related to illness histories"""
    CATEGORY_CHOICES = (
        ('medical_results', 'Результаты исследований'),
        ('consents', 'Согласия'),
        ('reports', 'Отчеты'),
        ('other', 'Прочее'),
    )

    illness_history = models.ForeignKey('IllnessHistory', on_delete=models.CASCADE, related_name='documents')
    file = models.FileField(upload_to=upload_documents_location)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    file_type = models.CharField(max_length=10)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='other')
    size = models.CharField(max_length=20)  # Human-readable file size

    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"

    class Meta:
        ordering = ['-created_at']
