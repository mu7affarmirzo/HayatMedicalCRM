from django.contrib import admin
from import_export.admin import ImportExportModelAdmin

from core.models import (
    Warehouse, CompanyModel, MedicationModel, MedicationsInStockModel
)


@admin.register(Warehouse)
class WarehouseAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = [field.name for field in Warehouse._meta.fields]


@admin.register(CompanyModel)
class CompanyModelAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = [field.name for field in CompanyModel._meta.fields]


@admin.register(MedicationModel)
class MedicationModelAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = [field.name for field in MedicationModel._meta.fields]


@admin.register(MedicationsInStockModel)
class MedicationsInStockModelAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = [field.name for field in MedicationsInStockModel._meta.fields]

