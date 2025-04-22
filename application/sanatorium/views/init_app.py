from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from core.models import InitialAppointmentWithDoctorModel, IllnessHistory
from ..forms.init_appointment_form import InitialAppointmentForm


@login_required
def initial_appointment_detail(request, history_id):
    """View for displaying the initial appointment details."""
    history = get_object_or_404(IllnessHistory, id=history_id)

    # Get or create initial appointment for this history
    initial_appointment, created = InitialAppointmentWithDoctorModel.objects.get_or_create(
        illness_history=history,
        defaults={'doctor': request.user, 'created_by': request.user}
    )

    context = {
        'history': history,
        'appointment': initial_appointment,
        'active_page': {'initial_appointment': 'active'},
    }

    # Add all appointments for sidebar
    context.update(get_sidebar_appointments(history))

    return render(request, 'sanatorium/doctors/init_appointment/appointment_detail.html', context)


@login_required
def initial_appointment_update(request, history_id):
    """View for updating the initial appointment."""
    history = get_object_or_404(IllnessHistory, id=history_id)

    # Get or create initial appointment for this history
    initial_appointment, created = InitialAppointmentWithDoctorModel.objects.get_or_create(
        illness_history=history,
        defaults={'doctor': request.user, 'created_by': request.user}
    )

    if request.method == 'POST':
        form = InitialAppointmentForm(request.POST, instance=initial_appointment)
        if form.is_valid():
            appointment = form.save(commit=False)
            appointment.modified_by = request.user
            appointment.save()
            messages.success(request, 'Первичный прием успешно обновлен')
            return redirect('initial_appointment_detail', history_id=history_id)
    else:
        form = InitialAppointmentForm(instance=initial_appointment)

    context = {
        'history': history,
        'appointment': initial_appointment,
        'form': form,
        'active_page': {'initial_appointment': 'active'},
    }

    # Add all appointments for sidebar
    context.update(get_sidebar_appointments(history))

    return render(request, 'sanatorium/doctors/init_appointment/appointment_form.html', context)


def get_sidebar_appointments(history):
    """Helper function to get all appointments for the sidebar."""
    return {
        'cardiologist_appointments': [],  # Query these as needed
        'neurologist_appointments': [],
        'on_arrival_appointments': [],
        'repeated_appointments': [],
        'with_doc_on_duty_appointments': [],
        'ekg_appointments': [],
        'final_appointment': None,
    }