from django import forms
from core.models import IllnessHistory, DiagnosisTemplate, ProfessionModel, ToxicFactorModel, TagModel


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