from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django import forms
from core.models import Booking, BookingDetail, Room, PatientModel, Tariff, TariffRoomPrice


class BookingForm(forms.ModelForm):
    """Form for updating the main Booking record"""

    class Meta:
        model = Booking
        fields = ['start_date', 'end_date', 'notes', 'status']
        widgets = {
            'start_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'end_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Format datetime fields for HTML5 datetime-local input
        if self.instance.start_date:
            self.initial['start_date'] = self.instance.start_date.strftime('%Y-%m-%dT%H:%M')
        if self.instance.end_date:
            self.initial['end_date'] = self.instance.end_date.strftime('%Y-%m-%dT%H:%M')


@login_required
def booking_edit_view(request, booking_id):
    """
    View for editing a booking
    """
    booking = get_object_or_404(Booking, id=booking_id)

    # Check if booking can be edited
    if booking.status in ['cancelled', 'completed']:
        messages.error(request,
                       f'Бронирование #{booking.booking_number} нельзя редактировать в статусе "{booking.get_status_display()}"')
        return redirect('logus:booking_detail', booking_id=booking.id)

    if request.method == 'POST':
        form = BookingForm(request.POST, instance=booking)
        if form.is_valid():
            # Save the booking with the current user as modifier
            booking = form.save(commit=False)
            booking.modified_by = request.user
            booking.save()

            messages.success(request, f'Бронирование #{booking.booking_number} успешно обновлено.')
            return redirect('logus:booking_detail', booking_id=booking.id)
    else:
        form = BookingForm(instance=booking)

    context = {
        'form': form,
        'booking': booking,
        'title': f'Редактирование бронирования #{booking.booking_number}',
    }

    return render(request, 'logus/booking/booking_form.html', context)


class BookingDetailForm(forms.ModelForm):
    """Form for updating a BookingDetail record"""

    class Meta:
        model = BookingDetail
        fields = ['client', 'room', 'tariff', 'price']
        widgets = {
            'client': forms.Select(attrs={'class': 'form-control select2'}),
            'room': forms.Select(attrs={'class': 'form-control select2'}),
            'tariff': forms.Select(attrs={'class': 'form-control select2'}),
            'price': forms.NumberInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, booking=None, **kwargs):
        super().__init__(*args, **kwargs)

        # Filter clients to active ones
        self.fields['client'].queryset = PatientModel.objects.filter(is_active=True)

        # Filter rooms to active ones
        self.fields['room'].queryset = Room.objects.filter(is_active=True)

        # Filter tariffs to active ones
        self.fields['tariff'].queryset = Tariff.objects.filter(is_active=True)

        # Store booking for validation
        self.booking = booking or self.instance.booking

    def clean(self):
        cleaned_data = super().clean()
        room = cleaned_data.get('room')

        # Check if room is available for this booking (except for the current booking detail)
        if room and self.booking:
            start_date = self.booking.start_date
            end_date = self.booking.end_date

            # Check if this room is already booked during this period
            overlapping_bookings = BookingDetail.objects.filter(
                room=room,
                booking__start_date__lt=end_date,
                booking__end_date__gt=start_date,
                booking__status__in=['pending', 'confirmed', 'checked_in']
            )

            # Exclude current instance if editing
            if self.instance and self.instance.pk:
                overlapping_bookings = overlapping_bookings.exclude(pk=self.instance.pk)

            if overlapping_bookings.exists():
                self.add_error('room', 'Эта комната уже забронирована на указанный период.')

        # Auto-calculate price based on tariff and room
        tariff = cleaned_data.get('tariff')
        if room and tariff and not cleaned_data.get('price'):
            try:
                price_record = TariffRoomPrice.objects.get(
                    tariff=tariff,
                    room_type=room.room_type
                )
                cleaned_data['price'] = price_record.price
            except TariffRoomPrice.DoesNotExist:
                self.add_error('tariff', 'Нет цены для данного сочетания тарифа и типа комнаты.')

        return cleaned_data


@login_required
def booking_detail_edit_view(request, detail_id):
    """
    View for editing a booking detail
    """
    booking_detail = get_object_or_404(BookingDetail, id=detail_id)
    booking = booking_detail.booking

    # Check if booking can be edited
    if booking.status in ['cancelled', 'completed']:
        messages.error(request,
                       f'Бронирование #{booking.booking_number} нельзя редактировать в статусе "{booking.get_status_display()}"')
        return redirect('logus:booking_detail', booking_id=booking.id)

    if request.method == 'POST':
        form = BookingDetailForm(request.POST, instance=booking_detail, booking=booking)
        if form.is_valid():
            # Save the booking detail with the current user as modifier
            booking_detail = form.save(commit=False)
            booking_detail.modified_by = request.user
            booking_detail.save()

            messages.success(request, f'Данные о размещении для {booking_detail.client.full_name} успешно обновлены.')
            return redirect('logus:booking_detail', booking_id=booking.id)
    else:
        form = BookingDetailForm(instance=booking_detail, booking=booking)

    context = {
        'form': form,
        'booking': booking,
        'booking_detail': booking_detail,
        'title': f'Редактирование размещения - {booking_detail.client.full_name}',
    }

    return render(request, 'logus/booking/booking_detail_form.html', context)


@login_required
def booking_detail_add_view(request, booking_id):
    """
    View for adding a new guest to an existing booking
    """
    booking = get_object_or_404(Booking, id=booking_id)

    # Check if booking can be edited
    if booking.status in ['cancelled', 'completed']:
        messages.error(request,
                       f'Нельзя добавить гостя к бронированию #{booking.booking_number} в статусе "{booking.get_status_display()}"')
        return redirect('logus:booking_detail', booking_id=booking.id)

    if request.method == 'POST':
        form = BookingDetailForm(request.POST, booking=booking)
        if form.is_valid():
            # Save the booking detail with the current user
            booking_detail = form.save(commit=False)
            booking_detail.booking = booking
            booking_detail.created_by = request.user
            booking_detail.modified_by = request.user
            booking_detail.save()

            messages.success(request, f'Гость {booking_detail.client.full_name} успешно добавлен к бронированию.')
            return redirect('logus:booking_detail', booking_id=booking.id)
    else:
        form = BookingDetailForm(booking=booking)

    context = {
        'form': form,
        'booking': booking,
        'title': f'Добавление гостя к бронированию #{booking.booking_number}',
    }

    return render(request, 'logus/booking/booking_detail_form.html', context)


@login_required
def booking_detail_delete_view(request, detail_id):
    """
    View for deleting a booking detail
    """
    booking_detail = get_object_or_404(BookingDetail, id=detail_id)
    booking = booking_detail.booking

    # Check if booking can be edited
    if booking.status in ['cancelled', 'completed']:
        messages.error(request,
                       f'Нельзя удалить гостя из бронирования #{booking.booking_number} в статусе "{booking.get_status_display()}"')
        return redirect('logus:booking_detail', booking_id=booking.id)

    # Prevent deleting if it's the only guest
    if booking.details.count() <= 1:
        messages.error(request, f'Нельзя удалить единственного гостя из бронирования. Удалите бронирование полностью.')
        return redirect('logus:booking_detail', booking_id=booking.id)

    if request.method == 'POST':
        client_name = booking_detail.client.full_name
        booking_detail.delete()
        messages.success(request, f'Гость {client_name} успешно удален из бронирования.')
        return redirect('logus:booking_detail', booking_id=booking.id)

    return redirect('logus:booking_detail', booking_id=booking.id)