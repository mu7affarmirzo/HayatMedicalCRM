from dataclasses import field

from django.contrib import admin

from core.models import (
    ConsultingWithNeurologistModel,
    ConsultingWithCardiologistModel,
    AppointmentWithOnDutyDoctorOnArrivalModel,
    RepeatedAppointmentWithDoctorModel,
    AppointmentWithOnDutyDoctorModel,
    EkgAppointmentModel,
    FinalAppointmentWithDoctorModel
)

from import_export.admin import ImportExportModelAdmin


@admin.register(ConsultingWithNeurologistModel)
class ConsultingWithNeurologistModelAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = [field.name for field in ConsultingWithNeurologistModel._meta.fields]


@admin.register(ConsultingWithCardiologistModel)
class ConsultingWithCardiologistModelAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = [field.name for field in ConsultingWithCardiologistModel._meta.fields]


@admin.register(AppointmentWithOnDutyDoctorOnArrivalModel)
class AppointmentWithOnDutyDoctorOnArrivalModelAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = [field.name for field in AppointmentWithOnDutyDoctorOnArrivalModel._meta.fields]


@admin.register(RepeatedAppointmentWithDoctorModel)
class RepeatedAppointmentWithDoctorModelAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = [field.name for field in RepeatedAppointmentWithDoctorModel._meta.fields]


@admin.register(AppointmentWithOnDutyDoctorModel)
class AppointmentWithOnDutyDoctorModelAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = [field.name for field in AppointmentWithOnDutyDoctorModel._meta.fields]


@admin.register(EkgAppointmentModel)
class EkgAppointmentModelAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = [field.name for field in EkgAppointmentModel._meta.fields]


@admin.register(FinalAppointmentWithDoctorModel)
class FinalAppointmentWithDoctorModelAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = [field.name for field in FinalAppointmentWithDoctorModel._meta.fields]



