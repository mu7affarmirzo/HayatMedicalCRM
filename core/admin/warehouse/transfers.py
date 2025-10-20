from django.contrib import admin
from import_export.admin import ImportExportModelAdmin

from core.models import (
    TransferModel, TransferItemsModel
)


@admin.register(TransferModel)
class TransferModelAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = [field.name for field in TransferModel._meta.fields]


@admin.register(TransferItemsModel)
class TransferItemsModelAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = [field.name for field in TransferItemsModel._meta.fields]



