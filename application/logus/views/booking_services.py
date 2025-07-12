from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from application.logus.forms.booking import ServiceUsageForm
from core.models import BookingDetail, ServiceUsage, Service


@login_required
def booking_add_service_view(request, detail_id):
    """
    View for adding a service to a booking detail
    """
    booking_detail = get_object_or_404(BookingDetail, id=detail_id)
    booking = booking_detail.booking

    # Check if booking is in the right status
    if booking.status != 'checked_in':
        messages.error(request, f'Услуги можно добавлять только для бронирований в статусе "Заселен"')
        return redirect('booking_detail', booking_id=booking.id)

    if request.method == 'POST':
        form = ServiceUsageForm(request.POST)
        if form.is_valid():
            # Save the service usage with booking and detail references
            service_usage = form.save(commit=False)
            service_usage.booking = booking
            service_usage.booking_detail = booking_detail
            service_usage.created_by = request.user
            service_usage.modified_by = request.user
            service_usage.save()

            messages.success(request, f'Услуга "{service_usage.service.name}" успешно добавлена.')
            return redirect('booking_detail', booking_id=booking.id)
    else:
        form = ServiceUsageForm()

    context = {
        'form': form,
        'booking': booking,
        'booking_detail': booking_detail,
        'title': f'Добавление услуги для {booking_detail.client.full_name}',
    }

    return render(request, 'logus/booking/service_usage_form.html', context)


@login_required
def service_usage_edit_view(request, service_id):
    """
    View for editing a service usage
    """
    service_usage = get_object_or_404(ServiceUsage, id=service_id)
    booking = service_usage.booking

    # Check if booking is in the right status
    if booking.status != 'checked_in':
        messages.error(request, f'Услуги можно редактировать только для бронирований в статусе "Заселен"')
        return redirect('booking_detail', booking_id=booking.id)

    if request.method == 'POST':
        form = ServiceUsageForm(request.POST, instance=service_usage)
        if form.is_valid():
            # Save the service usage with the current user as modifier
            service_usage = form.save(commit=False)
            service_usage.modified_by = request.user
            service_usage.save()

            messages.success(request, f'Услуга "{service_usage.service.name}" успешно обновлена.')
            return redirect('booking_detail', booking_id=booking.id)
    else:
        form = ServiceUsageForm(instance=service_usage)

    context = {
        'form': form,
        'booking': booking,
        'service_usage': service_usage,
        'title': f'Редактирование услуги - {service_usage.service.name}',
    }

    return render(request, 'logus/booking/service_usage_form.html', context)


@login_required
def service_usage_delete_view(request, service_id):
    """
    View for deleting a service usage
    """
    service_usage = get_object_or_404(ServiceUsage, id=service_id)
    booking = service_usage.booking

    # Check if booking is in the right status
    if booking.status != 'checked_in':
        messages.error(request, f'Услуги можно удалять только для бронирований в статусе "Заселен"')
        return redirect('booking_detail', booking_id=booking.id)

    if request.method == 'POST':
        service_name = service_usage.service.name
        service_usage.delete()
        messages.success(request, f'Услуга "{service_name}" успешно удалена.')
        return redirect('booking_detail', booking_id=booking.id)

    return redirect('booking_detail', booking_id=booking.id)


@login_required
def booking_detail_view_detail(request, detail_id):
    """
    View for seeing detailed information about a specific booking detail
    """
    booking_detail = get_object_or_404(BookingDetail, id=detail_id)
    booking = booking_detail.booking

    # Get service usages for this booking detail
    service_usages = ServiceUsage.objects.filter(booking_detail=booking_detail)

    # Get services included in the tariff - use tariff_services directly instead of through services
    tariff_services = booking_detail.tariff.tariff_services.all().select_related('service')

    # Get service usage tracking if available
    service_sessions = {}
    for ts in tariff_services:
        try:
            tracking = booking_detail.service_sessions.get(tariff_service=ts)
            service_sessions[ts.id] = {
                'used': tracking.sessions_used,
                'remaining': tracking.sessions_remaining
            }
        except:
            service_sessions[ts.id] = {
                'used': 0,
                'remaining': ts.sessions_included
            }

    context = {
        'booking': booking,
        'booking_detail': booking_detail,
        'service_usages': service_usages,
        'tariff_services': tariff_services,
        'service_sessions': service_sessions,
        'title': f'Детали размещения - {booking_detail.client.full_name}',
    }

    return render(request, 'logus/booking/booking_detail.html', context)