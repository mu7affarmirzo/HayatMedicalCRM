from HayatMedicalCRM.auth.decorators import nurse_required
from django.shortcuts import render
from django.core.paginator import Paginator
from django.utils import timezone

# Import all appointment models
from core.models import (
    ConsultingWithCardiologistModel,
    FinalAppointmentWithDoctorModel,
    AppointmentWithOnDutyDoctorModel,
    InitialAppointmentWithDoctorModel,
    RepeatedAppointmentWithDoctorModel,
    EkgAppointmentModel,
    AppointmentWithOnDutyDoctorOnArrivalModel,
    ConsultingWithNeurologistModel
)


