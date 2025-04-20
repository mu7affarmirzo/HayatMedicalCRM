from django.contrib import admin

from core.models import PatientModel, RoomType, Room, Booking, BookingDetail, Service, TariffService, Tariff, IllnessHistory

from import_export.admin import ImportExportModelAdmin


admin.site.site_header = 'Hayat CRM Administration'

admin.site.site_title = 'Hayat CRM Administration'

admin.site.index_title = 'Welcome to Hayat CRM Administration'


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