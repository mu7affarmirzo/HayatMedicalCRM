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


class TariffChangeForm(forms.Form):
    """
    Form for changing tariff and/or room mid-stay for a booking detail.
    Implements the change_tariff() static method from BookingDetail model.
    """
    new_tariff = forms.ModelChoiceField(
        queryset=Tariff.objects.filter(is_active=True),
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Новый тариф",
        help_text="Выберите новый тариф для пациента"
    )

    new_room = forms.ModelChoiceField(
        queryset=Room.objects.filter(is_active=True),
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Новая комната",
        help_text="Выберите новую комнату для пациента"
    )

    change_date = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={
            'class': 'form-control',
            'type': 'datetime-local'
        }),
        label="Дата и время изменения",
        help_text="Когда вступает в силу новый тариф/комната",
        initial=timezone.now
    )

    reason = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Укажите причину изменения тарифа/комнаты'
        }),
        label="Причина изменения",
        help_text="Обязательное поле для аудита",
        required=True
    )

    def __init__(self, *args, **kwargs):
        booking_detail = kwargs.pop('booking_detail', None)
        super().__init__(*args, **kwargs)

        if booking_detail:
            self.booking_detail = booking_detail

            # Set current values as initial
            self.fields['new_tariff'].initial = booking_detail.tariff
            self.fields['new_room'].initial = booking_detail.room

            # Filter available rooms for the booking dates
            if booking_detail.booking:
                from application.logus.views.booking import get_available_rooms

                available_rooms = get_available_rooms(
                    booking_detail.booking.start_date,
                    booking_detail.booking.end_date
                )
                # Include current room in the list
                current_room_qs = Room.objects.filter(id=booking_detail.room.id)
                self.fields['new_room'].queryset = (available_rooms | current_room_qs).distinct()

            # Set min/max for change_date based on booking dates
            if booking_detail.booking:
                self.fields['change_date'].widget.attrs['min'] = booking_detail.booking.start_date.strftime('%Y-%m-%dT%H:%M')
                self.fields['change_date'].widget.attrs['max'] = booking_detail.booking.end_date.strftime('%Y-%m-%dT%H:%M')

    def clean_change_date(self):
        """Validate change date is within booking period"""
        change_date = self.cleaned_data.get('change_date')

        if hasattr(self, 'booking_detail'):
            booking = self.booking_detail.booking

            # Must be within booking period
            if change_date < booking.start_date:
                raise ValidationError(
                    f'Дата изменения не может быть раньше даты заезда ({booking.start_date.strftime("%d.%m.%Y %H:%M")})'
                )

            if change_date > booking.end_date:
                raise ValidationError(
                    f'Дата изменения не может быть позже даты выезда ({booking.end_date.strftime("%d.%m.%Y %H:%M")})'
                )

            # Cannot be in the past (except for current time adjustments)
            if change_date < timezone.now() - timezone.timedelta(hours=1):
                raise ValidationError(
                    'Дата изменения не может быть в прошлом (допускается отклонение до 1 часа)'
                )

        return change_date

    def clean(self):
        """Validate that something is actually changing"""
        cleaned_data = super().clean()

        if hasattr(self, 'booking_detail'):
            new_tariff = cleaned_data.get('new_tariff')
            new_room = cleaned_data.get('new_room')

            # Check if anything changed
            if (new_tariff == self.booking_detail.tariff and
                new_room == self.booking_detail.room):
                raise ValidationError(
                    'Необходимо изменить хотя бы тариф или комнату. '
                    'Если вы хотите оставить текущие значения, отмените операцию.'
                )

            # Validate room capacity if changing room
            if new_room and new_room != self.booking_detail.room:
                # Check if room is truly available
                change_date = cleaned_data.get('change_date')

                if change_date:
                    from application.logus.views.booking import get_available_rooms

                    # Check room is available from change_date onwards
                    available_rooms = get_available_rooms(
                        change_date,
                        self.booking_detail.booking.end_date
                    )

                    # Exclude current room from check (we're vacating it)
                    available_rooms = available_rooms.exclude(id=self.booking_detail.room.id)

                    if not available_rooms.filter(id=new_room.id).exists():
                        raise ValidationError(
                            f'Комната "{new_room.name}" недоступна в выбранный период. '
                            'Выберите другую комнату или измените дату.'
                        )

        return cleaned_data


class ServiceSessionRecordForm(forms.Form):
    """
    Form for recording a service session (marks session as used).
    Used with ServiceSessionTracking model.
    """
    notes = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Дополнительные заметки о сеансе (необязательно)'
        }),
        label="Заметки",
        required=False
    )

    performed_by = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Кто провел сеанс'
        }),
        label="Исполнитель",
        help_text="Врач/медсестра, проводившая процедуру",
        required=False
    )

    session_date = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={
            'class': 'form-control',
            'type': 'datetime-local'
        }),
        label="Дата и время сеанса",
        initial=timezone.now,
        help_text="Когда был проведен сеанс"
    )

    def __init__(self, *args, **kwargs):
        tracking = kwargs.pop('tracking', None)
        super().__init__(*args, **kwargs)

        if tracking:
            self.tracking = tracking

            # Set min/max dates based on booking period
            if tracking.booking_detail and tracking.booking_detail.booking:
                booking = tracking.booking_detail.booking
                self.fields['session_date'].widget.attrs['min'] = booking.start_date.strftime('%Y-%m-%dT%H:%M')
                self.fields['session_date'].widget.attrs['max'] = booking.end_date.strftime('%Y-%m-%dT%H:%M')

    def clean_session_date(self):
        """Validate session date is within booking period"""
        session_date = self.cleaned_data.get('session_date')

        if hasattr(self, 'tracking'):
            booking = self.tracking.booking_detail.booking

            if session_date < booking.start_date:
                raise ValidationError(
                    f'Дата сеанса не может быть раньше даты заезда ({booking.start_date.strftime("%d.%m.%Y")})'
                )

            if session_date > booking.end_date:
                raise ValidationError(
                    f'Дата сеанса не может быть позже даты выезда ({booking.end_date.strftime("%d.%m.%Y")})'
                )

            # Cannot be in the future
            if session_date > timezone.now() + timezone.timedelta(hours=1):
                raise ValidationError(
                    'Дата сеанса не может быть в будущем (допускается отклонение до 1 часа)'
                )

        return session_date


class CheckInForm(forms.Form):
    """
    TASK-024: Enhanced check-in form with medical screening
    Used when checking in a guest to record initial health assessment
    """

    # Check-in details
    actual_checkin_time = forms.DateTimeField(
        label='Фактическое время заселения',
        required=True,
        widget=forms.DateTimeInput(attrs={
            'class': 'form-control',
            'type': 'datetime-local'
        }),
        help_text='Время фактического заселения гостя'
    )

    room_condition = forms.ChoiceField(
        label='Состояние комнаты',
        required=True,
        choices=[
            ('excellent', 'Отличное'),
            ('good', 'Хорошее'),
            ('fair', 'Удовлетворительное'),
            ('poor', 'Требует внимания')
        ],
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    # Medical screening fields
    temperature = forms.DecimalField(
        label='Температура тела (°C)',
        required=False,
        max_digits=4,
        decimal_places=1,
        min_value=35.0,
        max_value=42.0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '36.6',
            'step': '0.1'
        })
    )

    blood_pressure_systolic = forms.IntegerField(
        label='Артериальное давление (систолическое)',
        required=False,
        min_value=60,
        max_value=250,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '120'
        })
    )

    blood_pressure_diastolic = forms.IntegerField(
        label='Артериальное давление (диастолическое)',
        required=False,
        min_value=40,
        max_value=150,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '80'
        })
    )

    pulse = forms.IntegerField(
        label='Пульс (уд/мин)',
        required=False,
        min_value=40,
        max_value=200,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '70'
        })
    )

    weight = forms.DecimalField(
        label='Вес (кг)',
        required=False,
        max_digits=5,
        decimal_places=2,
        min_value=1.0,
        max_value=300.0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '70.0',
            'step': '0.1'
        })
    )

    height = forms.IntegerField(
        label='Рост (см)',
        required=False,
        min_value=50,
        max_value=250,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '170'
        })
    )

    allergies = forms.CharField(
        label='Аллергии',
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Укажите известные аллергии или оставьте пустым'
        })
    )

    current_medications = forms.CharField(
        label='Текущие лекарства',
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Укажите принимаемые лекарства или оставьте пустым'
        })
    )

    medical_conditions = forms.CharField(
        label='Хронические заболевания',
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Укажите хронические заболевания или оставьте пустым'
        })
    )

    mobility_status = forms.ChoiceField(
        label='Статус мобильности',
        required=True,
        choices=[
            ('fully_mobile', 'Полностью мобильный'),
            ('needs_assistance', 'Нуждается в помощи'),
            ('wheelchair', 'Инвалидная коляска'),
            ('bedridden', 'Лежачий')
        ],
        widget=forms.Select(attrs={'class': 'form-control'}),
        initial='fully_mobile'
    )

    special_dietary_requirements = forms.CharField(
        label='Особые диетические требования',
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Укажите диетические ограничения или требования'
        })
    )

    emergency_contact_name = forms.CharField(
        label='ФИО контактного лица',
        required=False,
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'ФИО родственника или контактного лица'
        })
    )

    emergency_contact_phone = forms.CharField(
        label='Телефон контактного лица',
        required=False,
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+998 XX XXX-XX-XX'
        })
    )

    emergency_contact_relationship = forms.CharField(
        label='Отношение',
        required=False,
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Например: супруг(а), сын/дочь, друг'
        })
    )

    # Additional check-in notes
    check_in_notes = forms.CharField(
        label='Примечания при заселении',
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Любые дополнительные заметки о заселении'
        })
    )

    # Staff confirmation
    belongings_checked = forms.BooleanField(
        label='Личные вещи проверены',
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    room_orientation_completed = forms.BooleanField(
        label='Ориентация по комнате проведена',
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    facility_tour_completed = forms.BooleanField(
        label='Экскурсия по учреждению проведена',
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    documents_signed = forms.BooleanField(
        label='Документы подписаны',
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    def __init__(self, *args, **kwargs):
        self.booking_detail = kwargs.pop('booking_detail', None)
        super().__init__(*args, **kwargs)

        # Set initial check-in time to now
        if not self.is_bound:
            self.initial['actual_checkin_time'] = timezone.now().strftime('%Y-%m-%dT%H:%M')

    def clean_actual_checkin_time(self):
        """Validate check-in time"""
        checkin_time = self.cleaned_data.get('actual_checkin_time')

        if self.booking_detail:
            booking = self.booking_detail.booking

            # Cannot check in before the start date
            if checkin_time < booking.start_date - timezone.timedelta(hours=2):
                raise ValidationError(
                    f'Время заселения не может быть более чем на 2 часа раньше времени заезда '
                    f'({booking.start_date.strftime("%d.%m.%Y %H:%M")})'
                )

            # Check-in time shouldn't be too far in the future
            if checkin_time > timezone.now() + timezone.timedelta(hours=1):
                raise ValidationError('Время заселения не может быть в будущем')

        return checkin_time

    def clean(self):
        """Additional validation"""
        cleaned_data = super().clean()

        # Validate blood pressure values if either is provided
        systolic = cleaned_data.get('blood_pressure_systolic')
        diastolic = cleaned_data.get('blood_pressure_diastolic')

        if systolic and diastolic:
            if systolic <= diastolic:
                raise ValidationError(
                    'Систолическое давление должно быть выше диастолического'
                )

        # If emergency contact name is provided, phone should also be provided
        if cleaned_data.get('emergency_contact_name') and not cleaned_data.get('emergency_contact_phone'):
            self.add_error('emergency_contact_phone',
                          'Пожалуйста, укажите телефон контактного лица')

        return cleaned_data