from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone

from core.models import Booking, BookingDetail, PatientModel, Room


class BookingInitialForm(forms.Form):
    """
    Initial form for starting a booking - select patient, dates, and number of guests
    """
    patient = forms.ModelChoiceField(
        queryset=PatientModel.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control select2', 'style': 'width: 100%;'})
    )

    date_range = forms.CharField(
        widget=forms.TextInput(
            attrs={'class': 'form-control', 'id': 'date-range'}
        )
    )

    guests_count = forms.IntegerField(
        min_value=1,
        initial=1,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
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