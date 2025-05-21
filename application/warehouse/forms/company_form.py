from django import forms
from core.models import CompanyModel


class CompanyForm(forms.ModelForm):
    class Meta:
        model = CompanyModel
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Название компании'})
        }

    def clean_name(self):
        name = self.cleaned_data['name']
        # Check if name already exists for a different company
        if CompanyModel.objects.filter(name__iexact=name).exclude(
                pk=self.instance.pk if self.instance else None).exists():
            raise forms.ValidationError('Компания с таким названием уже существует.')
        return name

