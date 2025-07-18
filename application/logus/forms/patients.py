from django import forms
from core.models import IllnessHistory, DiagnosisTemplate, ProfessionModel, ToxicFactorModel, TagModel, Booking, Account


class IllnessHistoryForm(forms.ModelForm):
    class Meta:
        model = IllnessHistory
        fields = [
            'type', 'is_sick_leave', 'profession', 'toxic_factors', 'tags',
            'state', 'initial_diagnosis', 'at_arrival_diagnosis', 'diagnosis',
            'notes'
        ]
        widgets = {
            'type': forms.Select(attrs={'class': 'form-control'}),
            'is_sick_leave': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'profession': forms.Select(attrs={'class': 'form-control select2'}),
            'toxic_factors': forms.SelectMultiple(attrs={'class': 'form-control select2', 'multiple': 'multiple'}),
            'tags': forms.Select(attrs={'class': 'form-control select2'}),
            'state': forms.Select(attrs={'class': 'form-control'}),
            'initial_diagnosis': forms.Select(attrs={'class': 'form-control select2'}),
            'at_arrival_diagnosis': forms.Select(attrs={'class': 'form-control select2'}),
            'diagnosis': forms.Select(attrs={'class': 'form-control select2'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super(IllnessHistoryForm, self).__init__(*args, **kwargs)

        # Make some fields optional
        self.fields['profession'].required = False
        self.fields['toxic_factors'].required = False
        self.fields['tags'].required = False
        self.fields['initial_diagnosis'].required = False
        self.fields['at_arrival_diagnosis'].required = False
        self.fields['diagnosis'].required = False

        # Set labels in Russian
        self.fields['type'].label = 'Тип лечения'
        self.fields['is_sick_leave'].label = 'Больничный лист'
        self.fields['profession'].label = 'Профессия'
        self.fields['toxic_factors'].label = 'Токсические факторы'
        self.fields['tags'].label = 'Теги'
        self.fields['state'].label = 'Статус'
        self.fields['initial_diagnosis'].label = 'Первичный диагноз'
        self.fields['at_arrival_diagnosis'].label = 'Диагноз при поступлении'
        self.fields['diagnosis'].label = 'Итоговый диагноз'
        self.fields['notes'].label = 'Примечания'


class IllnessHistoryEditForm(forms.ModelForm):
    class Meta:
        model = IllnessHistory
        fields = [
            'series_number',
            'booking',
            'type',
            'is_sick_leave',
            'state',
            'at_arrival_diagnosis',
            'nurses',
            'doctor',
            'notes'
        ]
        widgets = {
            'series_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите номер серии'
            }),
            'booking': forms.Select(attrs={
                'class': 'form-control select2',
                'style': 'width: 100%;'
            }),
            'type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'is_sick_leave': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'state': forms.Select(attrs={
                'class': 'form-control'
            }),
            'at_arrival_diagnosis': forms.Select(attrs={
                'class': 'form-control select2',
                'style': 'width: 100%;'
            }),
            'nurses': forms.SelectMultiple(attrs={
                'class': 'form-control select2',
                'style': 'width: 100%;',
                'multiple': 'multiple'
            }),
            'doctor': forms.Select(attrs={
                'class': 'form-control select2',
                'style': 'width: 100%;'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Введите примечания...'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Filter bookings to only active ones
        self.fields['booking'].queryset = Booking.objects.filter(
            status__in=['pending', 'confirmed', 'checked_in']
        ).order_by('-created_at')

        # Filter doctors to only accounts with doctor/therapist roles
        self.fields['doctor'].queryset = Account.objects.filter(
            is_therapist=True,
            is_active=True
        ).order_by('f_name', 'l_name')

        # Filter nurses to only accounts with therapist roles (assuming nurses are also marked as therapists)
        self.fields['nurses'].queryset = Account.objects.filter(
            is_therapist=True,
            is_active=True
        ).order_by('f_name', 'l_name')

        # Filter diagnosis templates if the model exists
        try:
            self.fields['at_arrival_diagnosis'].queryset = DiagnosisTemplate.objects.filter(
                is_active=True
            ).order_by('name')
        except:
            # If DiagnosisTemplate doesn't exist, leave empty
            pass

        # Make some fields required
        self.fields['series_number'].required = True
        self.fields['booking'].required = True

        # Add empty options
        self.fields['booking'].empty_label = "-- Выберите бронирование --"
        self.fields['doctor'].empty_label = "-- Выберите врача --"
        self.fields['at_arrival_diagnosis'].empty_label = "-- Выберите диагноз --"

    def clean_series_number(self):
        series_number = self.cleaned_data.get('series_number')

        # Check for uniqueness excluding current instance
        qs = IllnessHistory.objects.filter(series_number=series_number)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            raise forms.ValidationError("История болезни с таким номером серии уже существует.")

        return series_number
