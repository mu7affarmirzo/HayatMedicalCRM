from django.contrib import admin

from core.models import PatientModel, RoomType, Room, Booking, BookingDetail

admin.site.site_header = 'Hayat CRM Administration'

admin.site.site_title = 'Hayat CRM Administration'

admin.site.index_title = 'Welcome to Hayat CRM Administration'


@admin.register(PatientModel)
class PatientModelAdmin(admin.ModelAdmin):
    list_display = [field.name for field in PatientModel._meta.fields]


@admin.register(RoomType)
class RoomTypeAdmin(admin.ModelAdmin):
    pass


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    pass


@admin.register(BookingDetail)
class BookingDetailAdmin(admin.ModelAdmin):
    pass


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    pass


# admin.site.register(PatientModel)