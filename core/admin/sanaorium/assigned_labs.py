from core.models import AssignedLabs, LabResultValue, AssignedLabResult
from django.contrib import admin

from import_export.admin import ImportExportModelAdmin


@admin.register(AssignedLabs)
class AssignedLabsAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = [field.name for field in AssignedLabs._meta.fields]


@admin.register(AssignedLabResult)
class AssignedLabResultAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = [field.name for field in AssignedLabResult._meta.fields]


@admin.register(LabResultValue)
class LabResultValueAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = [field.name for field in LabResultValue._meta.fields]