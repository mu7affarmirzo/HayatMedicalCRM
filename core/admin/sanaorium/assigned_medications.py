from django.contrib import admin
from import_export.admin import ImportExportModelAdmin

from core.models import PrescribedMedication, MedicationSession


@admin.register(PrescribedMedication)
class PrescribedMedicationAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = [field.name for field in PrescribedMedication._meta.fields]


@admin.register(MedicationSession)
class MedicationSessionAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = [field.name for field in MedicationSession._meta.fields]
