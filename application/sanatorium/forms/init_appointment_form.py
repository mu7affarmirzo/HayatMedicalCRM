from django import forms
from django.utils.translation import gettext_lazy as _

from core.models import InitialAppointmentWithDoctorModel


class InitialAppointmentForm(forms.ModelForm):
    class Meta:
        model = InitialAppointmentWithDoctorModel
        exclude = ['created_by', 'modified_by', 'created_at', 'modified_at', 'doctor']

        # Group fields into fieldsets for easier rendering in template
        fieldsets = [
            (_('Basic Information'), {
                'fields': ['state', 'illness_history']
            }),
            (_('Patient Complaints and History'), {
                'fields': ['complaint', 'anamnesis_morbi', 'anamnesis_vitae']
            }),
            (_('Infectious Disease History'), {
                'fields': [
                    'contact_with_infectious', 'contact_with_orvi', 'is_away_two_month',
                    'transferred_infectious'
                ]
            }),
            (_('Medical History'), {
                'fields': [
                    'staying_hospital', 'receiving_blood_transfusions',
                    'surgical_massive_interventions_six_months', 'dentist_visits_last_six_months',
                    'profession_toxics', 'additional_data'
                ]
            }),
            (_('Physical Examination - General Status'), {
                'fields': [
                    'general_state', 'consciousness', 'consciousness_state', 'constitution'
                ]
            }),
            (_('Physical Examination - Skin'), {
                'fields': [
                    'skin', 'pigmentation', 'depigmentation', 'rashes', 'vascular_changes',
                    'hemorrhages', 'scarring', 'trophic_changes', 'visible_tumors',
                    'skin_moisture', 'skin_turgor', 'subcutaneous_fat'
                ]
            }),
            (_('Vital Signs'), {
                'fields': [
                    'temperature', 'height', 'weight', 'heart_beat',
                    'arterial_high', 'arterial_low', 'imt', 'extra_weight'
                ]
            }),
            (_('Other Body Systems'), {
                'fields': [
                    'swelling_pastiness', 'lymph_nodes', 'deformations', 'contractures',
                    'movement_restrictions'
                ]
            }),
            (_('Respiratory System'), {
                'fields': [
                    'respiratory_frequency', 'breathing_type', 'auscultative_breathing',
                    'wheezing', 'coughing', 'high_humidity', 'crepitus', 'lungs_percussion'
                ]
            }),
            (_('Cardiovascular System'), {
                'fields': [
                    'heart_edge', 'heart_tones', 'accent_in_aorta', 'noise_change_on_ot',
                    'ad_left', 'ad_right', 'ps_left', 'ps_right', 'pulse_noise_on_arteria'
                ]
            }),
            (_('Digestive System'), {
                'fields': [
                    'appetit', 'tongue', 'cracks_ulcers_in_mouth', 'stomach',
                    'liver', 'liver_edge', 'spleen', 'spleen_edge', 'stool', 'stool_frequency'
                ]
            }),
            (_('Other Systems'), {
                'fields': [
                    'urinary_system', 'effleurage_symptoms', 'thyroid', 'nerve_system'
                ]
            }),
            (_('Diagnosis and Summary'), {
                'fields': ['diagnosis', 'cito', 'summary']
            }),
        ]

    def clean(self):
        cleaned_data = super().clean()

        # Calculate BMI if height and weight are provided
        height = cleaned_data.get('height')
        weight = cleaned_data.get('weight')

        if height and weight and height > 0:
            height_in_meters = height / 100
            bmi = weight / (height_in_meters * height_in_meters)
            cleaned_data['imt'] = round(bmi, 2)

        # Additional validations can be added here
        # For example, ensure systolic pressure is higher than diastolic
        arterial_high = cleaned_data.get('arterial_high')
        arterial_low = cleaned_data.get('arterial_low')

        if arterial_high and arterial_low and arterial_high <= arterial_low:
            self.add_error('arterial_high', _('Systolic pressure must be higher than diastolic pressure.'))
            self.add_error('arterial_low', _('Diastolic pressure must be lower than systolic pressure.'))

        return cleaned_data