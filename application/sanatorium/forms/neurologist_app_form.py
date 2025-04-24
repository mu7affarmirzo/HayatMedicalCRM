from django import forms
from core.models import ConsultingWithNeurologistModel, Account


class ConsultingWithNeurologistForm(forms.ModelForm):
    """Form for creating and updating neurologist consultations."""

    class Meta:
        model = ConsultingWithNeurologistModel
        exclude = ['created_by', 'modified_by', 'created_at', 'modified_at', 'illness_history', 'doctor']
        widgets = {
            # Basic information
            'state': forms.Select(attrs={'class': 'form-control'}),
            'is_familiar_with_anamnesis': forms.CheckboxInput(attrs={'class': 'custom-control-input'}),
            'complaint': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Жалобы пациента'}),
            'anamnesis': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Анамнез'}),

            # Eye examination
            'palpebral_fissures': forms.TextInput(attrs={'class': 'form-control'}),
            'pupils': forms.TextInput(attrs={'class': 'form-control'}),
            'reaction_on_pupils': forms.TextInput(attrs={'class': 'form-control'}),
            'aye_frame_movement': forms.TextInput(attrs={'class': 'form-control'}),
            'nystagmus': forms.TextInput(attrs={'class': 'form-control'}),

            # Face and oral examination
            'face': forms.TextInput(attrs={'class': 'form-control'}),
            'tongue': forms.TextInput(attrs={'class': 'form-control'}),
            'soft_sk': forms.TextInput(attrs={'class': 'form-control'}),
            'phonation_swallowing': forms.TextInput(attrs={'class': 'form-control'}),

            # Muscle examination
            'reflexes': forms.TextInput(attrs={'class': 'form-control'}),
            'muscle_strength': forms.TextInput(attrs={'class': 'form-control'}),
            'muscle_tones': forms.TextInput(attrs={'class': 'form-control'}),

            # Deep reflexes
            'deep_reflexes_hand': forms.TextInput(attrs={'class': 'form-control'}),
            'deep_reflexes_foot': forms.TextInput(attrs={'class': 'form-control'}),
            'stylo_radial': forms.TextInput(attrs={'class': 'form-control'}),
            'biceps': forms.TextInput(attrs={'class': 'form-control'}),
            'triceps': forms.TextInput(attrs={'class': 'form-control'}),
            'knees': forms.TextInput(attrs={'class': 'form-control'}),
            'achilles': forms.TextInput(attrs={'class': 'form-control'}),
            'abdominal': forms.TextInput(attrs={'class': 'form-control'}),
            'pathological_reflexes': forms.TextInput(attrs={'class': 'form-control'}),

            # Balance and coordination
            'romberg_position': forms.TextInput(attrs={'class': 'form-control'}),
            'complicated_position': forms.TextInput(attrs={'class': 'form-control'}),
            'finger_test': forms.TextInput(attrs={'class': 'form-control'}),
            'heel_knee_test': forms.TextInput(attrs={'class': 'form-control'}),
            'gait': forms.TextInput(attrs={'class': 'form-control'}),

            # Other neurological examination
            'sensitivity': forms.TextInput(attrs={'class': 'form-control'}),
            'cognitive_test': forms.TextInput(attrs={'class': 'form-control'}),
            'emotional_volitional_sphere': forms.TextInput(attrs={'class': 'form-control'}),
            'insomnia': forms.TextInput(attrs={'class': 'form-control'}),

            # Spine examination
            'movements_in_the_cervical_spine': forms.TextInput(attrs={'class': 'form-control'}),
            'movements_in_the_spinal_spine': forms.TextInput(attrs={'class': 'form-control'}),
            'spinous_processes': forms.TextInput(attrs={'class': 'form-control'}),
            'paravertebral_points': forms.TextInput(attrs={'class': 'form-control'}),
            'lasegues_symptom': forms.TextInput(attrs={'class': 'form-control'}),

            # Conclusion
            'cito': forms.CheckboxInput(attrs={'class': 'custom-control-input'}),
            'for_sanatorium_treatment': forms.Select(attrs={'class': 'form-control'}),
            'summary': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Заключение'}),
            'recommendation': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Рекомендации'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set field labels
        self.fields['is_familiar_with_anamnesis'].label = "Ознакомлен с анамнезом"
        self.fields['palpebral_fissures'].label = "Глазные щели"
        self.fields['for_sanatorium_treatment'].label = "Для санаторно-курортного лечения"