from django import forms
from django.core.exceptions import ValidationError
from core.models import FinalAppointmentWithDoctorModel, DiagnosisTemplate
from django.utils import timezone


class FinalAppointmentEnhancedForm(forms.ModelForm):
    """Enhanced form for creating and updating final doctor appointments with comprehensive features."""

    class Meta:
        model = FinalAppointmentWithDoctorModel
        exclude = ['created_by', 'modified_by', 'created_at', 'modified_at', 'doctor', 'illness_history', 'imt', 'imt_interpretation']
        widgets = {
            # Status field
            'state': forms.Select(attrs={
                'class': 'form-control select2',
                'data-placeholder': 'Выберите статус приема'
            }),

            # Patient assessment
            'objective_status': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Подробное описание объективного состояния пациента: общий вид, состояние кожных покровов, лимфатических узлов, органов дыхания, сердечно-сосудистой системы, пищеварения, мочеполовой системы, нервной системы...'
            }),
            'file': forms.FileInput(attrs={
                'class': 'form-control-file',
                'accept': '.pdf,.doc,.docx,.jpg,.jpeg,.png'
            }),

            # Vitals
            'height': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '170.0',
                'step': '0.1',
                'min': '50',
                'max': '250',
                'data-calculation': 'bmi'
            }),
            'weight': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '70.0',
                'step': '0.1',
                'min': '20',
                'max': '300',
                'data-calculation': 'bmi'
            }),
            'heart_beat': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '72',
                'min': '30',
                'max': '200'
            }),
            'arterial_high_low': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'мм рт.ст.',
                'readonly': True,
                'value': 'мм рт.ст.'
            }),
            'arterial_high': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '120',
                'min': '60',
                'max': '250'
            }),
            'arterial_low': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '80',
                'min': '40',
                'max': '150'
            }),

            # Diagnosis and conclusion
            'diagnosis': forms.SelectMultiple(attrs={
                'class': 'form-control select2',
                'style': 'width: 100%;',
                'data-placeholder': 'Выберите диагнозы'
            }),
            'summary': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': 'Подробное заключение врача: динамика заболевания, эффективность проведенного лечения, рекомендации по дальнейшему ведению пациента, прогноз...'
            }),
            'treatment_results': forms.Select(attrs={
                'class': 'form-control select2',
                'data-placeholder': 'Выберите результат лечения'
            }),
        }

    # Additional fields for enhanced functionality
    treatment_effectiveness = forms.ChoiceField(
        choices=[
            ('', 'Выберите эффективность'),
            ('excellent', 'Отличная - полное выздоровление'),
            ('good', 'Хорошая - значительное улучшение'),
            ('satisfactory', 'Удовлетворительная - частичное улучшение'),
            ('poor', 'Неудовлетворительная - минимальное улучшение'),
            ('none', 'Отсутствует - без динамики')
        ],
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control select2',
            'data-placeholder': 'Оцените эффективность лечения'
        })
    )
    
    recommendations = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Рекомендации пациенту: режим, диета, медикаментозная терапия, контрольные обследования, сроки повторного осмотра...'
        })
    )
    
    follow_up_required = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'custom-control-input'
        })
    )
    
    follow_up_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    discharge_ready = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'custom-control-input'
        })
    )

    def __init__(self, *args, **kwargs):
        self.illness_history = kwargs.pop('illness_history', None)
        super().__init__(*args, **kwargs)

        # Set diagnosis queryset
        self.fields['diagnosis'].queryset = DiagnosisTemplate.objects.filter(is_active=True)

        # Set custom field labels
        self.fields['state'].label = "Статус приема"
        
        # Patient assessment
        self.fields['objective_status'].label = "Объективный статус пациента"
        self.fields['file'].label = "Прикрепить документы"

        # Vitals
        self.fields['height'].label = "Рост (см)"
        self.fields['weight'].label = "Вес (кг)"
        self.fields['heart_beat'].label = "Частота сердечных сокращений (уд/мин)"
        self.fields['arterial_high_low'].label = "Единицы измерения"
        self.fields['arterial_high'].label = "Систолическое артериальное давление"
        self.fields['arterial_low'].label = "Диастолическое артериальное давление"

        # Diagnosis and conclusion
        self.fields['diagnosis'].label = "Клинические диагнозы"
        self.fields['summary'].label = "Заключение лечащего врача"
        self.fields['treatment_results'].label = "Общий результат лечения"
        
        # Enhanced fields
        self.fields['treatment_effectiveness'].label = "Эффективность лечения"
        self.fields['recommendations'].label = "Рекомендации пациенту"
        self.fields['follow_up_required'].label = "Требуется повторный осмотр"
        self.fields['follow_up_date'].label = "Дата повторного осмотра"
        self.fields['discharge_ready'].label = "Пациент готов к выписке"

        # Set help texts
        self.fields['height'].help_text = "Рост пациента в сантиметрах"
        self.fields['weight'].help_text = "Вес пациента в килограммах (ИМТ будет рассчитан автоматически)"
        self.fields['heart_beat'].help_text = "Пульс в покое"
        self.fields['arterial_high'].help_text = "Верхнее (систолическое) давление"
        self.fields['arterial_low'].help_text = "Нижнее (диастолическое) давление"
        self.fields['diagnosis'].help_text = "Выберите один или несколько диагнозов"
        self.fields['summary'].help_text = "Подробное медицинское заключение по результатам лечения"
        self.fields['follow_up_date'].help_text = "Рекомендуемая дата следующего визита (если требуется)"

        # Pre-populate some fields if this is an update
        if self.instance and self.instance.pk:
            # Auto-fill recommendations based on treatment results
            if not self.instance.summary and self.illness_history:
                self.fields['summary'].initial = self._generate_summary_template()

    def _generate_summary_template(self):
        """Generate a template for the summary based on patient's treatment history"""
        if not self.illness_history:
            return ""
        
        template = f"""Пациент {self.illness_history.patient.full_name} находился на лечении в санатории с {self.illness_history.created_at.strftime('%d.%m.%Y')}.

ПРОВЕДЕННОЕ ЛЕЧЕНИЕ:
[Описать основные лечебные мероприятия]

ДИНАМИКА СОСТОЯНИЯ:
[Описать изменения в состоянии пациента за период лечения]

РЕЗУЛЬТАТЫ ОБСЛЕДОВАНИЙ:
[Указать результаты контрольных исследований]

ЗАКЛЮЧЕНИЕ:
[Общая оценка эффективности лечения и прогноз]

РЕКОМЕНДАЦИИ:
[Рекомендации по дальнейшему ведению пациента]"""
        
        return template

    def clean(self):
        cleaned_data = super().clean()
        height = cleaned_data.get('height')
        weight = cleaned_data.get('weight')
        arterial_high = cleaned_data.get('arterial_high')
        arterial_low = cleaned_data.get('arterial_low')
        follow_up_required = cleaned_data.get('follow_up_required')
        follow_up_date = cleaned_data.get('follow_up_date')
        
        # Validate height and weight for BMI calculation
        if height and weight:
            if height < 50 or height > 250:
                raise ValidationError("Рост должен быть в диапазоне от 50 до 250 см")
            if weight < 20 or weight > 300:
                raise ValidationError("Вес должен быть в диапазоне от 20 до 300 кг")
        
        # Validate blood pressure
        if arterial_high and arterial_low:
            if arterial_low >= arterial_high:
                raise ValidationError("Диастолическое давление не может быть больше или равно систолическому")
            if arterial_high < 60 or arterial_high > 250:
                raise ValidationError("Систолическое давление должно быть в диапазоне от 60 до 250 мм рт.ст.")
            if arterial_low < 40 or arterial_low > 150:
                raise ValidationError("Диастолическое давление должно быть в диапазоне от 40 до 150 мм рт.ст.")
        
        # Validate follow-up date
        if follow_up_required and not follow_up_date:
            raise ValidationError("Если требуется повторный осмотр, необходимо указать дату")
        
        if follow_up_date and follow_up_date <= timezone.now().date():
            raise ValidationError("Дата повторного осмотра должна быть в будущем")
        
        # Require diagnosis for completed appointments
        if cleaned_data.get('state') == 'Приём завершён' and not cleaned_data.get('diagnosis'):
            raise ValidationError("Для завершенного приема необходимо указать диагноз")
        
        # Require summary for completed appointments
        if cleaned_data.get('state') == 'Приём завершён' and not cleaned_data.get('summary'):
            raise ValidationError("Для завершенного приема необходимо написать заключение")
        
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Calculate BMI if height and weight are provided
        if instance.height and instance.weight:
            height_m = instance.height / 100  # Convert cm to meters
            instance.imt = instance.weight / (height_m ** 2)
            
            # Set BMI interpretation
            if instance.imt < 18.5:
                instance.imt_interpretation = 1  # Underweight
            elif 18.5 <= instance.imt < 25:
                instance.imt_interpretation = 2  # Normal
            elif 25 <= instance.imt < 30:
                instance.imt_interpretation = 3  # Overweight
            else:
                instance.imt_interpretation = 4  # Obese
        
        if commit:
            instance.save()
            self.save_m2m()
        
        return instance


class FinalAppointmentSearchForm(forms.Form):
    """Form for searching and filtering final appointments"""
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Поиск по имени пациента...'
        })
    )
    
    status = forms.ChoiceField(
        required=False,
        choices=[('', 'Все статусы')] + list(FinalAppointmentWithDoctorModel._meta.get_field('state').choices),
        widget=forms.Select(attrs={
            'class': 'form-control select2'
        })
    )
    
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    treatment_result = forms.ChoiceField(
        required=False,
        choices=[('', 'Все результаты')] + list(FinalAppointmentWithDoctorModel._meta.get_field('treatment_results').choices),
        widget=forms.Select(attrs={
            'class': 'form-control select2'
        })
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.fields['search'].label = "Поиск"
        self.fields['status'].label = "Статус"
        self.fields['date_from'].label = "Дата с"
        self.fields['date_to'].label = "Дата по"
        self.fields['treatment_result'].label = "Результат лечения"