from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone

from core.models import Booking, BookingDetail, PatientModel, Room, Tariff, TariffRoomPrice, ServiceUsage, Service

from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone

from core.models import Booking, BookingDetail, PatientModel, Room


class BookingInitialForm(forms.Form):
    """
    Initial form for starting a booking - select patient, dates, and number of guests
    """
    patient = forms.ModelChoiceField(
        queryset=PatientModel.objects.filter(is_active=True),
        widget=forms.Select(attrs={
            'class': 'form-control select2 select2-primary',
            'style': 'width: 100%;',
            'data-dropdown-css-class': 'select2-primary'
        }),
        empty_label="-- Выберите пациента --",
        label="Пациент"
    )

    date_range = forms.CharField(
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'id': 'date-range',
                'placeholder': 'Выберите диапазон дат'
            }
        ),
        label="Диапазон дат"
    )

    guests_count = forms.IntegerField(
        min_value=1,
        max_value=10,
        initial=1,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '1',
            'max': '10'
        }),
        label="Количество гостей"
    )

    def clean(self):
        cleaned_data = super().clean()
        date_range = cleaned_data.get("date_range")

        if date_range:
            try:
                # Parse the date range string (format: "DD.MM.YYYY - DD.MM.YYYY")
                start_str, end_str = date_range.split(' - ')
                start_date = timezone.datetime.strptime(start_str + ' 14:00', '%d.%m.%Y %H:%M')
                end_date = timezone.datetime.strptime(end_str + ' 12:00', '%d.%m.%Y %H:%M')

                # Convert to timezone-aware datetime if needed
                if timezone.is_naive(start_date):
                    start_date = timezone.make_aware(start_date)
                if timezone.is_naive(end_date):
                    end_date = timezone.make_aware(end_date)

                # Store the parsed dates
                cleaned_data['start_date'] = start_date
                cleaned_data['end_date'] = end_date

                # Check if start date is in the past
                if start_date < timezone.now():
                    raise ValidationError("Дата заезда не может быть в прошлом")

                # Check if end date is after start date
                if end_date <= start_date:
                    raise ValidationError("Дата выезда должна быть позже даты заезда")

                # Check if the booking period is reasonable (e.g., not more than 30 days)
                duration = (end_date - start_date).days
                if duration > 30:
                    raise ValidationError("Период бронирования не может превышать 30 дней")

            except ValueError:
                raise ValidationError("Неверный формат диапазона дат. Используйте формат ДД.ММ.ГГГГ - ДД.ММ.ГГГГ")

        return cleaned_data


class RoomSelectionForm(forms.Form):
    """
    Form for selecting rooms after checking availability
    """

    def __init__(self, *args, **kwargs):
        available_rooms = kwargs.pop('available_rooms', None)
        guests_count = kwargs.pop('guests_count', 1)
        super().__init__(*args, **kwargs)

        if available_rooms:
            room_choices = [(room.id, f"{room.name} - {room.room_type.name}") for room in available_rooms]

            # Create multiple selection fields based on number of guests
            for i in range(guests_count):
                field_name = f'room_{i}'
                self.fields[field_name] = forms.ChoiceField(
                    choices=room_choices,
                    label=f"Комната для гостя {i + 1}",
                    widget=forms.Select(attrs={'class': 'form-control'})
                )


class BookingConfirmationForm(forms.Form):
    """
    Final form for confirming booking details and adding notes
    """
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Дополнительные примечания к бронированию...'
        }),
        label="Примечания"
    )


class RoomSelectionForm(forms.Form):
    """
    Form for selecting rooms after checking availability
    """

    # This will be dynamically populated with available rooms
    # The actual fields will be added in the view based on available rooms

    def __init__(self, *args, **kwargs):
        available_rooms = kwargs.pop('available_rooms', None)
        guests_count = kwargs.pop('guests_count', 1)
        super().__init__(*args, **kwargs)

        if available_rooms:
            room_choices = [(room.id, f"{room.name} - {room.room_type.name}") for room in available_rooms]

            # Create multiple selection fields based on number of guests
            for i in range(guests_count):
                field_name = f'room_{i}'
                self.fields[field_name] = forms.ChoiceField(
                    choices=room_choices,
                    label=f"Комната для гостя {i + 1}",
                    widget=forms.Select(attrs={'class': 'form-control'})
                )


class BookingConfirmationForm(forms.Form):
    """
    Final form for confirming booking details and adding notes
    """
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )



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


class ServiceUsageForm(forms.ModelForm):
    """Form for adding or editing a service usage"""

    class Meta:
        model = ServiceUsage
        fields = ['service', 'quantity', 'price', 'date_used', 'notes']
        widgets = {
            'service': forms.Select(attrs={'class': 'form-control select2'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'price': forms.NumberInput(attrs={'class': 'form-control'}),
            'date_used': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter services to active ones
        self.fields['service'].queryset = Service.objects.filter(is_active=True)

        # Format datetime field for HTML5 datetime-local input
        if self.instance.date_used:
            self.initial['date_used'] = self.instance.date_used.strftime('%Y-%m-%dT%H:%M')
        else:
            # Set default to now
            self.initial['date_used'] = timezone.now().strftime('%Y-%m-%dT%H:%M')

    def clean(self):
        cleaned_data = super().clean()
        service = cleaned_data.get('service')
        quantity = cleaned_data.get('quantity', 1)

        # Auto-calculate price based on service if not provided
        if service and not cleaned_data.get('price'):
            base_price = service.base_price or 0
            cleaned_data['price'] = base_price * quantity

        return cleaned_data