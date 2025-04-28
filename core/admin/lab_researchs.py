from django.contrib import admin
from import_export.admin import ImportExportModelAdmin

from core.models import (
    SpecimenType,
    LabTestGroupModel,
    LabTestMethodModel,
    LabMeasurementUnitModel,
    LabResearchCategoryModel,
    LabResearchSubCategoryModel,
    LabResearchModel,
    LabResearchTestModel,
    ReferenceRange,
    ReferenceRangeVersion,
    LabResult,
    LabTestResult,
)


@admin.register(SpecimenType)
class SpecimenTypeAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = [field.name for field in SpecimenType._meta.fields]


@admin.register(LabTestGroupModel)
class LabTestGroupModelAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = [field.name for field in LabTestGroupModel._meta.fields]


@admin.register(LabTestMethodModel)
class LabTestMethodModelAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = [field.name for field in LabTestMethodModel._meta.fields]


@admin.register(LabMeasurementUnitModel)
class LabMeasurementUnitModelAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = [field.name for field in LabMeasurementUnitModel._meta.fields]


@admin.register(LabResearchCategoryModel)
class LabResearchCategoryModelAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = [field.name for field in LabResearchCategoryModel._meta.fields]


@admin.register(LabResearchSubCategoryModel)
class LabResearchSubCategoryModelAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = [field.name for field in LabResearchSubCategoryModel._meta.fields]


@admin.register(LabResearchModel)
class LabResearchModelAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = [field.name for field in LabResearchModel._meta.fields]


@admin.register(LabResearchTestModel)
class LabResearchTestModelAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = [field.name for field in LabResearchTestModel._meta.fields]


@admin.register(ReferenceRange)
class ReferenceRangeAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = [field.name for field in ReferenceRange._meta.fields]


@admin.register(ReferenceRangeVersion)
class ReferenceRangeVersionAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = [field.name for field in ReferenceRangeVersion._meta.fields]


@admin.register(LabResult)
class LabResultAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = [field.name for field in LabResult._meta.fields]


@admin.register(LabTestResult)
class LabTestResultAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = [field.name for field in LabTestResult._meta.fields]