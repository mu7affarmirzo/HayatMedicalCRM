from dataclasses import field

from django.contrib import admin

from core.models import (
    Account, PatientModel, RoomType, Room, Booking,
    BookingDetail, Service, TariffService, Tariff,
    IllnessHistory, DiagnosisTemplate, ServiceTypeModel,
    Warehouse, CompanyModel, ItemsModel, ItemsInStockModel,
)

from import_export.admin import ImportExportModelAdmin

admin.site.site_header = 'Hayat CRM Administration'

admin.site.site_title = 'Hayat CRM Administration'

admin.site.index_title = 'Welcome to Hayat CRM Administration'


@admin.register(Account)
class AccountAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = [field.name for field in Account._meta.fields]


@admin.register(PatientModel)
class PatientModelAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = [field.name for field in PatientModel._meta.fields]


@admin.register(RoomType)
class RoomTypeAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = [field.name for field in RoomType._meta.fields]


@admin.register(Room)
class RoomAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = [field.name for field in Room._meta.fields]


@admin.register(BookingDetail)
class BookingDetailAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    pass


@admin.register(Booking)
class BookingAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    pass


@admin.register(ServiceTypeModel)
class ServiceTypeModelAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = [field.name for field in ServiceTypeModel._meta.fields]


@admin.register(Service)
class ServiceAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = [field.name for field in Service._meta.fields]


@admin.register(TariffService)
class TariffServiceAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = [field.name for field in TariffService._meta.fields]


@admin.register(Tariff)
class TariffAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = [field.name for field in Tariff._meta.fields]


@admin.register(IllnessHistory)
class IllnessHistoryAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = [field.name for field in IllnessHistory._meta.fields]


@admin.register(Warehouse)
class WarehouseAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = [field.name for field in Warehouse._meta.fields]


@admin.register(CompanyModel)
class CompanyModelAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = [field.name for field in CompanyModel._meta.fields]


@admin.register(ItemsModel)
class ItemsModelAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = [field.name for field in ItemsModel._meta.fields]


@admin.register(ItemsInStockModel)
class ItemsInStockModelAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = [field.name for field in ItemsInStockModel._meta.fields]