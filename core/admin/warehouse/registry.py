from django.contrib import admin
from import_export.admin import ImportExportModelAdmin

from core.models import (
    IncomeModel, IncomeItemsModel
)


@admin.register(IncomeModel)
class IncomeModelAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = [field.name for field in IncomeModel._meta.fields]


@admin.register(IncomeItemsModel)
class IncomeItemsModelAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = [field.name for field in IncomeItemsModel._meta.fields]



