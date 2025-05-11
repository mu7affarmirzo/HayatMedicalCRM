import os

from django.db import models

from core.models import BaseAuditModel, IllnessHistory, LabResearchModel, upload_lab_files_location


class AssignedLabs(BaseAuditModel):
    STATE_CHOICES = (
        ('recommended', 'recommended'),
        ('assigned', 'assigned'),
        ('cancelled', 'cancelled'),
        ('stopped', 'stopped'),
        ('dispatched', 'dispatched'),
        ('results', 'results'),
    )
    illness_history = models.ForeignKey(IllnessHistory, on_delete=models.CASCADE, null=True, blank=True, related_name='assigned_labs')
    lab = models.ForeignKey(LabResearchModel, on_delete=models.SET_NULL, null=True, related_name="assigned_labs")

    state = models.CharField(choices=STATE_CHOICES, default='recommended', max_length=50)

    def __str__(self):
        return f"{self.illness_history} - {self.lab}"


class LabResultValue(BaseAuditModel):
    """
    Captures individual result metrics for a dispatched lab test.
    """
    assigned_lab = models.ForeignKey(
        AssignedLabs,
        on_delete=models.CASCADE,
        related_name="result_values",
    )
    name = models.CharField(max_length=255)
    value = models.CharField(max_length=100)
    unit = models.CharField(max_length=50, blank=True)
    reference_range = models.CharField(max_length=100, blank=True)
    flags = models.CharField(max_length=50, blank=True, help_text="E.g. High, Low, Critical")

    class Meta:
        ordering = ["name"]
        verbose_name = "Lab Result Value"
        verbose_name_plural = "Lab Result Values"

    def __str__(self):
        return f"{self.name}: {self.value} {self.unit}"


class AssignedLabResult(BaseAuditModel):
    assigned_lab = models.ForeignKey(AssignedLabs, related_name='lab_results', on_delete=models.CASCADE, null=True, blank=True)
    comments = models.TextField(null=True, blank=True)
    result_date = models.DateTimeField(auto_now_add=True)
    attached_file = models.FileField(upload_to=upload_lab_files_location, null=True, blank=True)
    file_format = models.CharField(max_length=10, null=True, blank=True)

    class Meta:
        ordering = ['-created_at']  # Most recent results first

    def save(self, *args, **kwargs):
        # Check if a file is uploaded or updated
        if self.attached_file and self.attached_file.name:
            # Extract file extension as format
            self.file_format = os.path.splitext(self.attached_file.name)[-1].replace('.', '').lower()

        super().save(*args, **kwargs)

    @property
    def get_file_name(self):
        return f"{self.attached_file.name}"

    def __str__(self):
        return f"Lab result for {self.assigned_lab} on {self.result_date}"

