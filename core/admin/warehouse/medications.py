from django.contrib import admin
from import_export.admin import ImportExportModelAdmin

from core.models import (
    Warehouse, CompanyModel, MedicationModel, MedicationsInStockModel,
    DeliveryCompanyModel, MedicationExpenseModel
)


@admin.register(Warehouse)
class WarehouseAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = [field.name for field in Warehouse._meta.fields]


@admin.register(DeliveryCompanyModel)
class DeliveryCompanyModelAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = [field.name for field in DeliveryCompanyModel._meta.fields]


@admin.register(CompanyModel)
class CompanyModelAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = [field.name for field in CompanyModel._meta.fields]



@admin.register(MedicationModel)
class MedicationModelAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = [field.name for field in MedicationModel._meta.fields]


@admin.register(MedicationsInStockModel)
class MedicationsInStockModelAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = [field.name for field in MedicationsInStockModel._meta.fields]


@admin.register(MedicationExpenseModel)
class MedicationExpenseModelAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ['id', 'stock_item', 'expense_type', 'quantity', 'unit_quantity', 'expense_date', 'created_by', 'created_at']
    list_filter = ['expense_type', 'expense_date', 'created_at']
    search_fields = ['stock_item__item__name', 'reason']
    date_hierarchy = 'expense_date'
    readonly_fields = ['created_at', 'modified_at', 'created_by', 'modified_by']

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        obj.modified_by = request.user
        super().save_model(request, obj, form, change)

