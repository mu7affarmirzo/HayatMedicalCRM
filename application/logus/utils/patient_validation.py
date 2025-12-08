"""
Patient Validation Utilities
Provides validation functions for patient data including:
- Duplicate patient detection
- Phone number validation
- Data quality checks
"""

import re
import logging
from typing import List, Dict, Optional
from datetime import date
from django.db.models import Q
from core.models import PatientModel

logger = logging.getLogger(__name__)


def check_duplicate_patient(
    f_name: str,
    l_name: str,
    date_of_birth: date,
    mobile_phone: str = None,
    email: str = None,
    doc_number: str = None,
    exclude_id: int = None
) -> List[Dict]:
    """
    Check for potential duplicate patients based on multiple criteria.

    Args:
        f_name: First name
        l_name: Last name
        date_of_birth: Date of birth
        mobile_phone: Mobile phone number (optional)
        email: Email address (optional)
        doc_number: Document number (optional)
        exclude_id: Patient ID to exclude from search (for updates)

    Returns:
        List of dictionaries containing potential duplicate patients with match scores
    """
    potential_duplicates = []

    # Start with base queryset
    queryset = PatientModel.objects.filter(is_active=True)

    # Exclude specific patient ID (useful for updates)
    if exclude_id:
        queryset = queryset.exclude(id=exclude_id)

    # Priority 1: Exact phone number match (highest confidence)
    if mobile_phone:
        phone_matches = queryset.filter(mobile_phone_number=mobile_phone)
        if phone_matches.exists():
            for patient in phone_matches:
                potential_duplicates.append({
                    'patient': patient,
                    'match_type': 'exact_phone',
                    'confidence': 'high',
                    'score': 95,
                    'message': f'Найден пациент с таким же номером телефона: {patient.full_name}'
                })
            return potential_duplicates  # Return immediately for exact phone match

    # Priority 2: Exact document number match
    if doc_number:
        doc_matches = queryset.filter(doc_number=doc_number)
        if doc_matches.exists():
            for patient in doc_matches:
                potential_duplicates.append({
                    'patient': patient,
                    'match_type': 'exact_document',
                    'confidence': 'high',
                    'score': 90,
                    'message': f'Найден пациент с таким же номером документа: {patient.full_name}'
                })
            return potential_duplicates  # Return immediately for exact document match

    # Priority 3: Exact email match
    if email:
        email_matches = queryset.filter(email__iexact=email)
        if email_matches.exists():
            for patient in email_matches:
                potential_duplicates.append({
                    'patient': patient,
                    'match_type': 'exact_email',
                    'confidence': 'medium',
                    'score': 75,
                    'message': f'Найден пациент с таким же email: {patient.full_name}'
                })

    # Priority 4: Name + DOB match (case-insensitive)
    name_dob_matches = queryset.filter(
        f_name__iexact=f_name,
        l_name__iexact=l_name,
        date_of_birth=date_of_birth
    )

    if name_dob_matches.exists():
        for patient in name_dob_matches:
            # Check if already added from email match
            if not any(d['patient'].id == patient.id for d in potential_duplicates):
                potential_duplicates.append({
                    'patient': patient,
                    'match_type': 'name_dob',
                    'confidence': 'medium',
                    'score': 70,
                    'message': f'Найден пациент с таким же ФИО и датой рождения: {patient.full_name}'
                })

    # Priority 5: Fuzzy name match (similar names + same DOB)
    fuzzy_matches = queryset.filter(
        Q(f_name__istartswith=f_name[:3]) | Q(f_name__icontains=f_name),
        Q(l_name__istartswith=l_name[:3]) | Q(l_name__icontains=l_name),
        date_of_birth=date_of_birth
    ).exclude(
        f_name__iexact=f_name,
        l_name__iexact=l_name
    )

    if fuzzy_matches.exists():
        for patient in fuzzy_matches:
            # Check if already added
            if not any(d['patient'].id == patient.id for d in potential_duplicates):
                potential_duplicates.append({
                    'patient': patient,
                    'match_type': 'fuzzy_name',
                    'confidence': 'low',
                    'score': 50,
                    'message': f'Найден похожий пациент: {patient.full_name}'
                })

    # Sort by score (highest first)
    potential_duplicates.sort(key=lambda x: x['score'], reverse=True)

    # Limit to top 5 matches
    return potential_duplicates[:5]


def validate_uzbekistan_phone(phone: str) -> Dict[str, any]:
    """
    Validate Uzbekistan phone number format.

    Accepted formats:
    - +998XXXXXXXXX (13 digits with country code)
    - 998XXXXXXXXX (12 digits without +)
    - XXXXXXXXX (9 digits, assumes 998 prefix)

    Valid operator codes:
    - Mobile: 90, 91, 93, 94, 95, 97, 98, 99, 33, 88, 50, 55, 77
    - Landline: 71, 75, 76, 74, 73, 78, 79, 61-69

    Args:
        phone: Phone number string

    Returns:
        Dictionary with validation result:
        {
            'valid': bool,
            'formatted': str (standardized format),
            'error': str (if invalid),
            'type': str ('mobile' or 'landline')
        }
    """
    # Remove all non-digit characters
    digits_only = re.sub(r'\D', '', phone)

    # Remove leading 8 if present (old format)
    if digits_only.startswith('8') and len(digits_only) == 10:
        digits_only = '998' + digits_only[1:]

    # Add 998 prefix if missing
    if len(digits_only) == 9:
        digits_only = '998' + digits_only

    # Validate length
    if len(digits_only) != 12:
        return {
            'valid': False,
            'formatted': None,
            'error': f'Неверная длина номера. Ожидается 9 цифр или +998XXXXXXXXX. Получено: {len(digits_only)} цифр',
            'type': None
        }

    # Validate country code
    if not digits_only.startswith('998'):
        return {
            'valid': False,
            'formatted': None,
            'error': 'Номер должен начинаться с кода Узбекистана (+998)',
            'type': None
        }

    # Extract operator code
    operator_code = digits_only[3:5]

    # Valid mobile operators
    mobile_operators = ['90', '91', '93', '94', '95', '97', '98', '99', '33', '88', '50', '55', '77']

    # Valid landline codes (Tashkent and regions)
    landline_codes = ['71', '75', '76', '74', '73', '78', '79'] + [str(i) for i in range(61, 70)]

    phone_type = None
    if operator_code in mobile_operators:
        phone_type = 'mobile'
    elif operator_code in landline_codes:
        phone_type = 'landline'
    else:
        return {
            'valid': False,
            'formatted': None,
            'error': f'Неверный код оператора: {operator_code}. Проверьте правильность номера',
            'type': None
        }

    # Format as +998 XX XXX-XX-XX
    formatted = f"+{digits_only[:3]} {digits_only[3:5]} {digits_only[5:8]}-{digits_only[8:10]}-{digits_only[10:12]}"

    return {
        'valid': True,
        'formatted': formatted,
        'raw': f"+{digits_only}",
        'error': None,
        'type': phone_type,
        'operator_code': operator_code
    }


def check_patient_data_quality(patient_data: Dict) -> Dict[str, List[str]]:
    """
    Check data quality of patient information.
    Returns warnings about missing or suspicious data.

    Args:
        patient_data: Dictionary containing patient fields

    Returns:
        Dictionary with 'warnings' and 'errors' lists
    """
    warnings = []
    errors = []

    # Check required fields
    required_fields = ['f_name', 'l_name', 'date_of_birth', 'mobile_phone_number']
    for field in required_fields:
        if not patient_data.get(field):
            errors.append(f'Обязательное поле "{field}" не заполнено')

    # Check date of birth is not in future
    dob = patient_data.get('date_of_birth')
    if dob and isinstance(dob, date):
        if dob > date.today():
            errors.append('Дата рождения не может быть в будущем')

        # Check age is reasonable (0-120 years)
        age = (date.today() - dob).days // 365
        if age > 120:
            warnings.append(f'Возраст пациента ({age} лет) кажется необычно большим')
        elif age < 0:
            errors.append('Дата рождения некорректна')

    # Check name length
    f_name = patient_data.get('f_name', '')
    l_name = patient_data.get('l_name', '')

    if len(f_name) < 2:
        warnings.append('Имя слишком короткое')
    if len(l_name) < 2:
        warnings.append('Фамилия слишком короткая')

    # Check for suspicious patterns
    if f_name and f_name.lower() in ['test', 'тест', 'admin', 'test patient']:
        warnings.append('Обнаружено тестовое имя')

    # Check email format if provided
    email = patient_data.get('email')
    if email:
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            errors.append('Неверный формат email адреса')

    # Check phone number if provided
    phone = patient_data.get('mobile_phone_number')
    if phone:
        validation = validate_uzbekistan_phone(phone)
        if not validation['valid']:
            errors.append(f"Номер телефона: {validation['error']}")

    # Check for missing recommended fields
    recommended_fields = ['mid_name', 'region', 'district', 'address']
    missing_recommended = [f for f in recommended_fields if not patient_data.get(f)]

    if missing_recommended:
        warnings.append(f'Рекомендуется заполнить: {", ".join(missing_recommended)}')

    return {
        'warnings': warnings,
        'errors': errors,
        'has_errors': len(errors) > 0,
        'has_warnings': len(warnings) > 0
    }


def suggest_patient_matches(search_query: str, limit: int = 10) -> List[PatientModel]:
    """
    Suggest patient matches based on partial search query.
    Useful for autocomplete/typeahead features.

    Args:
        search_query: Partial name, phone, or email
        limit: Maximum number of results

    Returns:
        List of PatientModel instances
    """
    if not search_query or len(search_query) < 2:
        return []

    # Search across multiple fields
    patients = PatientModel.objects.filter(
        Q(f_name__icontains=search_query) |
        Q(l_name__icontains=search_query) |
        Q(mid_name__icontains=search_query) |
        Q(mobile_phone_number__icontains=search_query) |
        Q(email__icontains=search_query),
        is_active=True
    ).order_by('-created_at')[:limit]

    return list(patients)


# Utility function for formatting patient info
def format_patient_summary(patient: PatientModel) -> str:
    """
    Create a human-readable summary of patient information.

    Args:
        patient: PatientModel instance

    Returns:
        Formatted string with patient summary
    """
    summary_parts = [
        f"ФИО: {patient.full_name}",
        f"Дата рождения: {patient.date_of_birth.strftime('%d.%m.%Y')}",
        f"Возраст: {patient.age} лет",
        f"Пол: {patient.formatted_gender}",
    ]

    if patient.mobile_phone_number:
        summary_parts.append(f"Телефон: {patient.mobile_phone_number}")

    if patient.email:
        summary_parts.append(f"Email: {patient.email}")

    if patient.region:
        summary_parts.append(f"Регион: {patient.region.name}")

    return " | ".join(summary_parts)
