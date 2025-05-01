from django import forms
from core.models import AssignedLabs, IllnessHistory, LabResearchModel


class AssignedLabsForm(forms.ModelForm):

    lab = forms.ModelChoiceField(
        queryset=LabResearchModel.objects.filter(is_active=True),
        widget=forms.Select(attrs={'class': 'form-control select2'}),
        required=True,
        label='Lab Test'
    )

    state = forms.ChoiceField(
        choices=AssignedLabs.STATE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        initial='recommended'
    )

    category_filter = forms.ChoiceField(
        choices=[('', 'All Categories')],  # Will be populated dynamically in __init__
        required=False,
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'category-filter'}),
        label='Filter by Category'
    )

    lab_search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search for lab tests...',
            'id': 'lab-search'
        }),
        label='Search Lab Tests'
    )

    class Meta:
        model = AssignedLabs
        fields = ['lab', 'state']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Dynamically populate category choices
        from core.models import LabResearchCategoryModel
        categories = LabResearchCategoryModel.objects.all()
        category_choices = [('', 'All Categories')]
        category_choices.extend([(c.id, c.name) for c in categories])
        self.fields['category_filter'].choices = category_choices

        # If we're editing an existing instance, pre-select the lab's category
        if 'instance' in kwargs and kwargs['instance'] and kwargs['instance'].lab and kwargs['instance'].lab.category:
            self.fields['category_filter'].initial = kwargs['instance'].lab.category.id