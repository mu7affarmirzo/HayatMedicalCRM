from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone

from application.sanatorium.forms.patients import IllnessHistoryForm
from core.models import IllnessHistory, PatientModel


@login_required
def assigned_patients_list(request):
    # # Check if user is a doctor
    # if not request.user.is_therapist:
    #     return redirect('home')  # Redirect non-doctors

    # Get all illness histories where the current user is the assigned doctor
    patient_histories = IllnessHistory.objects.filter(doctor=request.user)

    # Get today's appointments
    today = timezone.now().date()
    today_appointments = IllnessHistory.objects.filter(
        doctor=request.user,
        booking__start_date__date=today
    ).count()

    # Get statistics
    stationary_count = patient_histories.filter(type='stationary').count()
    ambulatory_count = patient_histories.filter(type='ambulatory').count()

    context = {
        'patient_histories': patient_histories,
        'today_appointments': today_appointments,
        'stationary_count': stationary_count,
        'ambulatory_count': ambulatory_count,
        'total_patients': patient_histories.count(),
    }

    return render(request, 'sanatorium/nurses/doctors_dashboard.html', context)


@login_required
def patient_detail(request, history_id):
    # Get the illness history
    history = get_object_or_404(IllnessHistory, id=history_id)

    # Security check - only the assigned doctor can view
    if history.doctor != request.user and not request.user.is_admin:
        return redirect('doctors_main_screen')

    # Get patient data
    patient = history.patient
    booking = history.booking

    context = {
        'history': history,
        'patient': patient,
        'booking': booking,
    }

    return render(request, 'sanatorium/nurses/patient_detail.html', context)


@login_required
def patient_edit(request, history_id):
    # Get the illness history
    history = get_object_or_404(IllnessHistory, id=history_id)

    # Security check - only the assigned doctor can edit
    if history.doctor != request.user and not request.user.is_admin:
        return redirect('doctors_main_screen')

    if request.method == 'POST':
        # Handle form submission
        # This would involve a form to update diagnosis and other medical information
        form = IllnessHistoryForm(request.POST, instance=history)
        if form.is_valid():
            form.save()
            return redirect('patient_detail', history_id=history.id)
    else:
        form = IllnessHistoryForm(instance=history)

    context = {
        'form': form,
        'history': history,
        'patient': history.patient,
    }

    return render(request, 'sanatorium/nurses/patient_edit.html', context)


# Ajax view to get bookings for a patient
def get_patient_bookings(request):
    patient_id = request.GET.get('patient_id')
    bookings = []

    if patient_id:
        try:
            patient = PatientModel.objects.get(id=patient_id)
            booking_details = patient.bookings.select_related('booking')

            # Get unique bookings
            booking_ids = set()
            for detail in booking_details:
                booking = detail.booking
                if booking.id not in booking_ids:
                    booking_ids.add(booking.id)
                    bookings.append({
                        'id': booking.id,
                        'booking_number': booking.booking_number,
                        'start_date': booking.start_date.strftime('%d.%m.%Y')
                    })
        except PatientModel.DoesNotExist:
            pass

    return JsonResponse({'bookings': bookings})