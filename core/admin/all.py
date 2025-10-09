from dataclasses import field

from django.contrib import admin

from core.models import (
    Account, PatientModel, RoomType, Room, Booking,
    BookingDetail, Service, TariffService, Tariff,
    IllnessHistory, DiagnosisTemplate, ServiceTypeModel,
    Warehouse, CompanyModel, MedicationModel, MedicationsInStockModel,
    RolesModel, ProfessionModel, Region, District, TariffRoomPrice
)

from import_export.admin import ImportExportModelAdmin

admin.site.site_header = 'Hayat CRM Administration'

admin.site.site_title = 'Hayat CRM Administration'

admin.site.index_title = 'Welcome to Hayat CRM Administration'


@admin.register(DiagnosisTemplate)
class DiagnosisTemplateAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = [field.name for field in DiagnosisTemplate._meta.fields]


@admin.register(ProfessionModel)
class ProfessionModelAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = [field.name for field in ProfessionModel._meta.fields]


@admin.register(RolesModel)
class RolesModelAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = [field.name for field in RolesModel._meta.fields]


@admin.register(Account)
class AccountAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = [field.name for field in Account._meta.fields]


@admin.register(Region)
class RegionAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = [field.name for field in Region._meta.fields]


@admin.register(District)
class DistrictAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = [field.name for field in District._meta.fields]


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


@admin.register(TariffRoomPrice)
class TariffRoomPriceAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = [field.name for field in TariffRoomPrice._meta.fields]


@admin.register(IllnessHistory)
class IllnessHistoryAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = [field.name for field in IllnessHistory._meta.fields]


