from django.contrib import admin
from import_export.admin import ImportExportModelAdmin

from core.models import (
    TransferModel, TransferItemsModel, AccountTransferModel, AccountTransferItemsModel
)


@admin.register(TransferModel)
class TransferModelAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = [field.name for field in TransferModel._meta.fields]


@admin.register(TransferItemsModel)
class TransferItemsModelAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = [field.name for field in TransferItemsModel._meta.fields]



@admin.register(AccountTransferModel)
class AccountTransferModelAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = [field.name for field in AccountTransferModel._meta.fields]


@admin.register(AccountTransferItemsModel)
class AccountTransferItemsModelAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = [field.name for field in AccountTransferItemsModel._meta.fields]

