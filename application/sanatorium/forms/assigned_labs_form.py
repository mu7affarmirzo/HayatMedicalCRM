from django import forms
from core.models import AssignedLabs, LabResearchModel, LabResearchCategoryModel


class AssignedLabsForm(forms.ModelForm):
    """Form for creating and updating lab assignments."""

    category_filter = forms.ModelChoiceField(
        queryset=LabResearchCategoryModel.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'category-filter'}),
        empty_label="Все категории",
        label="Категория анализов"
    )

    lab_search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Поиск анализов...',
            'id': 'lab-search'
        }),
        label='Поиск анализов'
    )

    class Meta:
        model = AssignedLabs
        fields = ['lab', 'state']
        widgets = {
            'lab': forms.Select(attrs={
                'class': 'form-control select2',
                'style': 'width: 100%;',
                'id': 'lab-select'
            }),
            'state': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Set lab queryset to active labs only
        self.fields['lab'].queryset = LabResearchModel.objects.filter(is_active=True)

        # Set custom field labels
        self.fields['lab'].label = "Лабораторный анализ"
        self.fields['state'].label = "Статус назначения"

        # Set custom choices for state field
        self.fields['state'].choices = (
            ('recommended', 'Рекомендован'),
            ('assigned', 'Назначен'),
            ('dispatched', 'Отправлен'),
            ('results', 'Результаты получены'),
            ('cancelled', 'Отменен'),
            ('stopped', 'Остановлен'),
        )

        # Set initial state
        self.fields['state'].initial = 'recommended'