from django import forms
from django.utils import timezone


class DietPlanForm(forms.Form):
    """Form for creating and updating diet plans"""
    
    DIET_TYPE_CHOICES = [
        ('standard', 'Стандартная диета'),
        ('therapeutic', 'Лечебная диета'),
        ('low_salt', 'Диета с низким содержанием соли'),
        ('diabetic', 'Диабетическая диета'),
        ('hypoallergenic', 'Гипоаллергенная диета'),
        ('liquid', 'Жидкая диета'),
        ('soft', 'Мягкая диета'),
        ('pureed', 'Протертая диета'),
        ('custom', 'Индивидуальная диета'),
    ]
    
    diet_type = forms.ChoiceField(
        choices=DIET_TYPE_CHOICES,
        required=True,
        label="Тип диеты",
        widget=forms.Select(attrs={'class': 'form-control select2'})
    )
    
    start_date = forms.DateField(
        required=True,
        label="Дата начала",
        widget=forms.DateInput(attrs={'class': 'form-control datepicker', 'type': 'date'})
    )
    
    end_date = forms.DateField(
        required=False,
        label="Дата окончания",
        widget=forms.DateInput(attrs={'class': 'form-control datepicker', 'type': 'date'})
    )
    
    restrictions = forms.CharField(
        required=False,
        label="Ограничения",
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Укажите продукты и ингредиенты, которые необходимо исключить...'
        })
    )
    
    recommendations = forms.CharField(
        required=False,
        label="Рекомендации",
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Укажите рекомендуемые продукты и режим питания...'
        })
    )
    
    calories_per_day = forms.IntegerField(
        required=False,
        label="Калории в день",
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': 500,
            'max': 5000,
            'placeholder': 'Например: 1800'
        })
    )
    
    meals_per_day = forms.IntegerField(
        required=False,
        label="Количество приемов пищи",
        initial=3,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': 1,
            'max': 10,
            'placeholder': 'Например: 5'
        })
    )
    
    notes = forms.CharField(
        required=False,
        label="Дополнительные примечания",
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Дополнительные указания и примечания...'
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set initial start date to today
        if not self.initial.get('start_date'):
            self.fields['start_date'].initial = timezone.now().date()
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        # Validate that start date is not in the past
        if start_date and start_date < timezone.now().date():
            self.add_error('start_date', 'Дата начала не может быть в прошлом')
        
        # Validate end date is after start date
        if start_date and end_date and end_date <= start_date:
            self.add_error('end_date', 'Дата окончания должна быть позже даты начала')
        
        return cleaned_data


class QuickDietForm(forms.Form):
    """Simplified form for quick diet assignment"""
    
    QUICK_DIET_CHOICES = [
        ('standard', 'Стандартная диета'),
        ('therapeutic', 'Лечебная диета'),
        ('low_salt', 'Диета с низким содержанием соли'),
        ('diabetic', 'Диабетическая диета'),
    ]
    
    diet_type = forms.ChoiceField(
        choices=QUICK_DIET_CHOICES,
        required=True,
        label="Тип диеты",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    notes = forms.CharField(
        required=False,
        label="Примечания",
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Краткие примечания...'
        })
    )