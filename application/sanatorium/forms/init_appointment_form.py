from django import forms
from django.utils.translation import gettext_lazy as _

from core.models import InitialAppointmentWithDoctorModel, Account

from django import forms
from core.models import InitialAppointmentWithDoctorModel, DiagnosisTemplate


# class InitialAppointmentForm(forms.ModelForm):
#     """Form for creating and updating initial appointments."""
#
#     class Meta:
#         model = InitialAppointmentWithDoctorModel
#         exclude = ['created_by', 'modified_by', 'created_at', 'modified_at', 'illness_history']
#         widgets = {
#             'complaint': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
#             'anamnesis_morbi': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
#             'anamnesis_vitae': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
#             'contact_with_infectious': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
#             'summary': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
#             'diagnosis': forms.Select(attrs={'class': 'form-control select2'}),
#             'temperature': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
#             'height': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
#             'weight': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
#             # Add similar widget definitions for other fields
#         }


class InitialAppointmentForm(forms.ModelForm):
    """Form for creating and updating initial appointments."""

    class Meta:
        model = InitialAppointmentWithDoctorModel
        exclude = ['created_by', 'modified_by', 'created_at', 'modified_at', 'illness_history', 'doctor']
        widgets = {
            # Basic information
            'state': forms.Select(attrs={'class': 'form-control'}),

            # Complaints and anamnesis
            'complaint': forms.Textarea(
                attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Укажите жалобы пациента'}),
            'anamnesis_morbi': forms.Textarea(
                attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'История настоящего заболевания'}),
            'anamnesis_vitae': forms.Textarea(
                attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'История жизни'}),
            'contact_with_infectious': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),

            # Checkboxes
            'contact_with_orvi': forms.CheckboxInput(attrs={'class': 'custom-control-input'}),
            'is_away_two_month': forms.CheckboxInput(attrs={'class': 'custom-control-input'}),
            'cito': forms.CheckboxInput(attrs={'class': 'custom-control-input'}),

            # Text inputs
            'transferred_infectious': forms.TextInput(attrs={'class': 'form-control'}),
            'staying_hospital': forms.TextInput(attrs={'class': 'form-control'}),
            'receiving_blood_transfusions': forms.TextInput(attrs={'class': 'form-control'}),
            'surgical_massive_interventions_six_months': forms.TextInput(attrs={'class': 'form-control'}),
            'dentist_visits_last_six_months': forms.TextInput(attrs={'class': 'form-control'}),
            'profession_toxics': forms.TextInput(attrs={'class': 'form-control'}),
            'additional_data': forms.TextInput(attrs={'class': 'form-control'}),

            # Status praesens objectivus
            'general_state': forms.TextInput(attrs={'class': 'form-control'}),
            'consciousness': forms.Select(attrs={'class': 'form-control'}),
            'consciousness_state': forms.Select(attrs={'class': 'form-control'}),
            'constitution': forms.Select(attrs={'class': 'form-control'}),
            'skin': forms.Select(attrs={'class': 'form-control'}),
            'pigmentation': forms.TextInput(attrs={'class': 'form-control'}),
            'depigmentation': forms.TextInput(attrs={'class': 'form-control'}),
            'rashes': forms.TextInput(attrs={'class': 'form-control'}),
            'vascular_changes': forms.TextInput(attrs={'class': 'form-control'}),
            'hemorrhages': forms.TextInput(attrs={'class': 'form-control'}),
            'scarring': forms.TextInput(attrs={'class': 'form-control'}),
            'trophic_changes': forms.TextInput(attrs={'class': 'form-control'}),
            'visible_tumors': forms.TextInput(attrs={'class': 'form-control'}),
            'skin_moisture': forms.Select(attrs={'class': 'form-control'}),
            'skin_turgor': forms.Select(attrs={'class': 'form-control'}),
            'subcutaneous_fat': forms.Select(attrs={'class': 'form-control'}),

            # Measurements
            'temperature': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'min': '35', 'max': '42'}),
            'height': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'placeholder': 'см'}),
            'weight': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'placeholder': 'кг'}),
            'heart_beat': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'уд/мин'}),
            'arterial_high': forms.NumberInput(attrs={'class': 'form-control'}),
            'arterial_low': forms.NumberInput(attrs={'class': 'form-control'}),
            'imt': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'readonly': 'readonly'}),
            'extra_weight': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'readonly': 'readonly'}),
            'swelling_pastiness': forms.TextInput(attrs={'class': 'form-control'}),
            'lymph_nodes': forms.Select(attrs={'class': 'form-control'}),

            # Musculoskeletal system
            'deformations': forms.TextInput(attrs={'class': 'form-control'}),
            'contractures': forms.TextInput(attrs={'class': 'form-control'}),
            'movement_restrictions': forms.TextInput(attrs={'class': 'form-control'}),

            # Respiratory system
            'respiratory_frequency': forms.NumberInput(attrs={'class': 'form-control'}),
            'breathing_type': forms.Select(attrs={'class': 'form-control'}),
            'auscultative_breathing': forms.Select(attrs={'class': 'form-control'}),
            'wheezing': forms.Select(attrs={'class': 'form-control'}),
            'coughing': forms.Select(attrs={'class': 'form-control'}),
            'high_humidity': forms.TextInput(attrs={'class': 'form-control'}),
            'crepitus': forms.Select(attrs={'class': 'form-control'}),
            'lungs_percussion': forms.Select(attrs={'class': 'form-control'}),

            # Cardiovascular system
            'heart_edge': forms.Select(attrs={'class': 'form-control'}),
            'heart_tones': forms.Select(attrs={'class': 'form-control'}),
            'accent_in_aorta': forms.Select(attrs={'class': 'form-control'}),
            'noise_change_on_ot': forms.Select(attrs={'class': 'form-control'}),
            'ad_left': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '120/80'}),
            'ad_right': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '120/80'}),
            'ps_left': forms.TextInput(attrs={'class': 'form-control'}),
            'ps_right': forms.TextInput(attrs={'class': 'form-control'}),
            'pulse_noise_on_arteria': forms.Select(attrs={'class': 'form-control'}),

            # Digestive system
            'appetit': forms.Select(attrs={'class': 'form-control'}),
            'tongue': forms.Select(attrs={'class': 'form-control'}),
            'cracks_ulcers_in_mouth': forms.Select(attrs={'class': 'form-control'}),
            'stomach': forms.Select(attrs={'class': 'form-control'}),
            'liver': forms.Select(attrs={'class': 'form-control'}),
            'liver_edge': forms.Select(attrs={'class': 'form-control'}),
            'spleen': forms.Select(attrs={'class': 'form-control'}),
            'spleen_edge': forms.Select(attrs={'class': 'form-control'}),
            'stool': forms.Select(attrs={'class': 'form-control'}),
            'stool_frequency': forms.TextInput(attrs={'class': 'form-control'}),

            # Urinary system
            'urinary_system': forms.TextInput(attrs={'class': 'form-control'}),
            'effleurage_symptoms': forms.Select(attrs={'class': 'form-control'}),
            'thyroid': forms.Select(attrs={'class': 'form-control'}),
            'nerve_system': forms.Select(attrs={'class': 'form-control'}),

            # Diagnosis and summary
            'diagnosis': forms.Select(attrs={'class': 'form-control select2', 'style': 'width: 100%;'}),
            'summary': forms.Textarea(
                attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Заключение по результатам осмотра'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter doctors to show only those who are doctors

        # Add help text where needed
        self.fields['temperature'].help_text = "Нормальная температура: 36.0-37.0°C"
        self.fields['imt'].help_text = "Индекс массы тела (рассчитывается автоматически)"
        self.fields['extra_weight'].help_text = "Избыточный вес рассчитывается автоматически"

        # Make some fields not required
        optional_fields = [
            'pigmentation', 'depigmentation', 'rashes', 'vascular_changes',
            'hemorrhages', 'scarring', 'trophic_changes', 'visible_tumors',
            'deformations', 'contractures', 'movement_restrictions',
            'high_humidity', 'accent_in_aorta', 'noise_change_on_ot',
            'cracks_ulcers_in_mouth', 'liver_edge', 'spleen_edge',
        ]

        for field in optional_fields:
            self.fields[field].required = False