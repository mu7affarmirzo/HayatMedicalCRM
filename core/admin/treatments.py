from django.contrib import admin
from import_export.admin import ImportExportModelAdmin

from core.models import (
    MedicalServiceModel,
    ProcedureServiceModel,
    IndividualProcedureSessionModel,
)


@admin.register(MedicalServiceModel)
class MedicalServiceModelAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = [field.name for field in MedicalServiceModel._meta.fields]


@admin.register(ProcedureServiceModel)
class ProcedureServiceModelAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = [field.name for field in ProcedureServiceModel._meta.fields]


@admin.register(IndividualProcedureSessionModel)
class IndividualProcedureSessionModelAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = [field.name for field in IndividualProcedureSessionModel._meta.fields]


