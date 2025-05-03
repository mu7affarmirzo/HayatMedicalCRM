from django.contrib import admin
from import_export.admin import ImportExportModelAdmin

from core.models import PrescribedMedication, MedicationAdministration


@admin.register(PrescribedMedication)
class PrescribedMedicationAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = [field.name for field in PrescribedMedication._meta.fields]


@admin.register(MedicationAdministration)
class MedicationAdministrationAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = [field.name for field in MedicationAdministration._meta.fields]
