# HAYAT MEDICAL CRM - RECEPTION MODULE DEEP ANALYSIS
## Complete Analysis of Registration, Booking & Patient Management System

**Analysis Date:** December 8, 2024
**Module:** Logus (Reception/Booking)
**Analyst:** System Architecture Review

---

## TABLE OF CONTENTS

1. [Executive Summary](#executive-summary)
2. [Architecture Overview](#architecture-overview)
3. [Core Data Models](#core-data-models)
4. [Patient Registration Workflow](#patient-registration-workflow)
5. [Booking Creation Process](#booking-creation-process)
6. [Current Features Inventory](#current-features-inventory)
7. [URL Routing & Endpoints](#url-routing--endpoints)
8. [Templates & UI Components](#templates--ui-components)
9. [Integration Points](#integration-points)
10. [Missing Features](#missing-features)
11. [Improvement Recommendations](#improvement-recommendations)
12. [Security Concerns](#security-concerns)
13. [Performance Optimization Opportunities](#performance-optimization-opportunities)
14. [Implementation Roadmap](#implementation-roadmap)

---

## EXECUTIVE SUMMARY

The Hayat Medical CRM Reception Module (Logus) is a **comprehensive patient registration and booking management system** built on Django. It successfully implements core functionality for:

- Patient registration with detailed demographics
- Multi-step booking wizard with room selection
- Availability management and occupancy tracking
- Tariff-based pricing with room type variations
- Service usage tracking and billing integration
- Medical record (illness history) integration

### Health Score: **7.5/10**

**Strengths:**
- ✅ Well-structured 3-step booking wizard
- ✅ Comprehensive patient data model
- ✅ Flexible tariff and pricing system
- ✅ Automatic illness history creation
- ✅ Room availability calculation
- ✅ Service session tracking

**Critical Issues:**
- ❌ Security vulnerabilities (`@csrf_exempt` decorators)
- ❌ Duplicate code and forms
- ❌ Missing UI for mid-stay tariff changes
- ❌ Incomplete payment processing workflow
- ❌ No advance reservation system
- ❌ Limited search and filtering capabilities

---

## ARCHITECTURE OVERVIEW

### Module Structure

```
/application/logus/
├── views/
│   ├── dashboard.py              # Reception dashboard & current guests
│   ├── booking.py                # Booking CRUD & wizard
│   ├── patient.py                # Patient management
│   ├── illness_history.py        # Medical records
│   └── payment.py                # Payment processing (stub)
├── forms/
│   ├── booking_forms.py          # Booking wizard forms
│   └── patient_form.py           # Patient registration forms
├── urls/
│   ├── __init__.py               # Main router
│   ├── booking.py                # Booking routes
│   └── patients.py               # Patient routes
├── signals.py                    # Auto-create illness history
└── utils.py                      # Helper functions

/core/models/
├── booking.py                    # Booking, BookingDetail, BookingBilling
├── clients.py                    # PatientModel, Region, District
├── rooms.py                      # Room, RoomType
├── tariffs.py                    # Tariff, TariffService, TariffRoomPrice
├── services.py                   # Service, ServiceUsage, ServiceSessionTracking
├── illness_history.py            # IllnessHistory
└── transactions.py               # TransactionsModel (payments)
```

### Technology Stack

| Component | Technology |
|-----------|------------|
| Backend Framework | Django 4.x+ |
| Views | Mixed CBV & FBV |
| ORM | Django ORM with PostgreSQL/SQLite |
| Frontend | AdminLTE3 + Bootstrap |
| JavaScript | jQuery + vanilla JS |
| Date Handling | Python datetime + dateutil |
| Dropdowns | Select2 |
| AJAX | jQuery.ajax() |
| Authentication | Django auth + custom decorators |

---

## CORE DATA MODELS

### 1. Patient Registration Models

#### PatientModel (`/core/models/clients.py`)

**Purpose:** Store comprehensive patient demographics and contact information

| Field | Type | Purpose | Constraints |
|-------|------|---------|-------------|
| `f_name` | CharField(200) | First name | Required |
| `mid_name` | CharField(200) | Middle name | Optional |
| `l_name` | CharField(200) | Last name | Required |
| `email` | EmailField | Email address | Unique, Optional |
| `date_of_birth` | DateField | Birth date | Required |
| `home_phone_number` | CharField(20) | Home phone | Optional |
| `mobile_phone_number` | CharField(20) | Mobile phone | Required |
| `address` | TextField | Home address | Optional |
| `gender` | BooleanField | Gender (True=Male) | Required |
| `gestational_age` | IntegerField | Pregnancy week | Optional |
| `region` | ForeignKey | Administrative region | Optional |
| `district` | ForeignKey | District | Optional |
| `doc_type` | CharField(50) | Document type | Optional |
| `doc_number` | CharField(50) | Document number | Optional |
| `INN` | CharField(20) | Tax ID | Optional |
| `country` | CharField(100) | Country | Optional |
| `is_active` | BooleanField | Active status | Default: True |
| `additional_info` | JSONField | Extra data | Default: {} |
| `created_at` | DateTimeField | Creation timestamp | Auto |
| `updated_at` | DateTimeField | Update timestamp | Auto |
| `created_by` | ForeignKey(Account) | Creator | Auto |
| `modified_by` | ForeignKey(Account) | Last modifier | Auto |

**Properties & Methods:**
- `full_name` → `"{f_name} {mid_name} {l_name}"`
- `age` → Calculated from `date_of_birth`
- `formatted_gender` → Returns "Мужской" or "Женский"
- `to_result()` → Returns dict with age, name, gender

**Issues Identified:**
- ⚠️ Gender as boolean is limiting (should be CharField with choices)
- ⚠️ No phone number format validation
- ⚠️ Email uniqueness constraint can cause issues for family members
- ⚠️ No duplicate detection mechanism
- ⚠️ `INN` field name should be lowercase per PEP 8

**Supporting Models:**

**Region:**
```python
- name: CharField(200)
- is_active: BooleanField (default=True)
```

**District:**
```python
- name: CharField(200)
- region: ForeignKey(Region)
- is_active: BooleanField (default=True)
```

---

### 2. Booking Models

#### Booking (`/core/models/booking.py`)

**Purpose:** Main booking container representing a reservation

| Field | Type | Purpose | Validation |
|-------|------|---------|------------|
| `booking_number` | CharField(50) | Unique identifier | Auto-generated: `BK-YYYYMMDD-XXXX` |
| `staff` | ForeignKey(Account) | Receptionist | Required |
| `start_date` | DateTimeField | Check-in | Required |
| `end_date` | DateTimeField | Check-out | Required, > start_date |
| `notes` | TextField | Booking notes | Optional |
| `status` | CharField(20) | Booking state | See below |
| `created_at` | DateTimeField | Creation time | Auto |
| `updated_at` | DateTimeField | Update time | Auto |

**Status Choices:**
```python
PENDING = "pending"              # В ожидании
CONFIRMED = "confirmed"          # Подтверждено
CHECKED_IN = "checked_in"        # Заселен
IN_PROGRESS = "in_progress"      # В процессе
COMPLETED = "completed"          # Завершено
CANCELLED = "cancelled"          # Отменено
DISCHARGED = "discharged"        # Выписан
```

**Methods:**
- `total_price()` → Sums all BookingDetail prices + ServiceUsage
- `is_active` → Returns True for CONFIRMED, CHECKED_IN, IN_PROGRESS
- `status_display_color` → Returns CSS class for status badge
- `generate_booking_number()` → Static method to create unique numbers

**Status Lifecycle:**
```
PENDING → CONFIRMED → CHECKED_IN → IN_PROGRESS → COMPLETED
                 ↓
             CANCELLED
```

**Triggers:**
- When status changes to `CHECKED_IN`: Auto-creates IllnessHistory records

---

#### BookingDetail (`/core/models/booking.py`)

**Purpose:** Individual guest within a group booking

| Field | Type | Purpose | Notes |
|-------|------|---------|-------|
| `booking` | ForeignKey(Booking) | Parent booking | Cascade delete |
| `client` | ForeignKey(PatientModel) | Guest | Required |
| `room` | ForeignKey(Room) | Assigned room | Required |
| `tariff` | ForeignKey(Tariff) | Treatment package | Required |
| `price` | DecimalField(10,2) | Booking price | From TariffRoomPrice |
| `start_date` | DateField | Actual check-in | Nullable |
| `end_date` | DateField | Actual check-out | Nullable |
| `effective_from` | DateTimeField | Tariff start | For mid-stay changes |
| `effective_to` | DateTimeField | Tariff end | For mid-stay changes |
| `is_current` | BooleanField | Active tariff | Default: True |

**Key Methods:**
```python
@staticmethod
def change_tariff(booking_detail, new_tariff, new_room, change_date):
    """
    Changes tariff/room mid-stay by:
    1. Setting is_current=False on old detail
    2. Setting effective_to on old detail
    3. Creating new BookingDetail with is_current=True
    4. Setting effective_from on new detail
    """
    # Implementation in model

def get_active_detail_at(booking, date):
    """Returns BookingDetail active at specific date"""

def get_days_in_period(self):
    """Calculates days in tariff period"""

def get_prorated_price(self):
    """Calculates price for partial stay"""
```

**Post-save Signal:**
```python
@receiver(post_save, sender=BookingDetail)
def _initialize_service_tracking(sender, instance, created, **kwargs):
    """
    Automatically creates ServiceSessionTracking records
    for each service included in the tariff
    """
    if created and instance.tariff:
        for tariff_service in instance.tariff.tariff_services.all():
            ServiceSessionTracking.objects.create(
                booking_detail=instance,
                service=tariff_service.service,
                tariff_service=tariff_service,
                sessions_included=tariff_service.sessions_included,
                sessions_used=0
            )
```

**Issues Identified:**
- ⚠️ `change_tariff()` method exists but no UI to invoke it
- ⚠️ Overlap prevention only checks room availability, not patient double-booking
- ⚠️ No validation that patient age/gender matches room/tariff restrictions

---

#### BookingBilling (`/core/models/booking.py`)

**Purpose:** Financial summary for a booking

| Field | Type | Purpose |
|-------|------|---------|
| `booking` | OneToOneField(Booking) | Parent booking |
| `tariff_base_amount` | DecimalField(10,2) | Base tariff cost |
| `additional_services_amount` | DecimalField(10,2) | Extra services |
| `medications_amount` | DecimalField(10,2) | Medications |
| `lab_research_amount` | DecimalField(10,2) | Lab tests |
| `total_amount` | DecimalField(10,2) | Total cost |
| `billing_status` | CharField(20) | Payment state |
| `created_at` | DateTimeField | Creation time |
| `updated_at` | DateTimeField | Update time |

**Billing Status Choices:**
```python
PENDING = "pending"              # Ожидается
CALCULATED = "calculated"        # Рассчитано
INVOICED = "invoiced"            # Выставлен счет
PAID = "paid"                    # Оплачено
PARTIALLY_PAID = "partially_paid"  # Частично оплачено
```

**Methods:**
```python
def calculate_total(self):
    """Sums all billing components"""
    self.total_amount = (
        self.tariff_base_amount +
        self.additional_services_amount +
        self.medications_amount +
        self.lab_research_amount
    )
    return self.total_amount

@property
def is_calculated(self):
    return self.billing_status != 'pending'

@property
def is_invoiced(self):
    return self.billing_status in ['invoiced', 'paid', 'partially_paid']
```

**Issues Identified:**
- ⚠️ No automatic recalculation when services added
- ⚠️ Status transitions not enforced
- ⚠️ No validation that total_amount matches sum of components

---

### 3. Room Management Models

#### Room (`/core/models/rooms.py`)

| Field | Type | Purpose |
|-------|------|---------|
| `name` | CharField(100) | Room identifier |
| `room_type` | ForeignKey(RoomType) | Room category |
| `price` | DecimalField(10,2) | Base price |
| `capacity` | IntegerField | Max occupants |
| `is_active` | BooleanField | Active status |

**Method:**
```python
def is_available(self, start_date, end_date):
    """
    Checks if room is available for date range
    Returns True if no overlapping bookings exist
    """
    overlapping = BookingDetail.objects.filter(
        room=self,
        booking__status__in=['pending', 'confirmed', 'checked_in', 'in_progress'],
        booking__start_date__lt=end_date,
        booking__end_date__gt=start_date
    ).exists()
    return not overlapping
```

**RoomType:**
```python
- name: CharField(100)           # e.g., "Standard", "Deluxe", "Suite"
- description: TextField
```

**Issues Identified:**
- ⚠️ Capacity not enforced (can assign multiple people to single room)
- ⚠️ No room maintenance scheduling
- ⚠️ No room features/amenities tracking
- ⚠️ No floor/building organization

---

### 4. Tariff & Service Models

#### Tariff (`/core/models/tariffs.py`)

**Purpose:** Treatment package with included services

| Field | Type | Purpose |
|-------|------|---------|
| `name` | CharField(200) | Tariff name |
| `description` | TextField | Description |
| `services` | ManyToMany(Service) | Through TariffService |
| `price` | DecimalField(10,2) | Base price |
| `is_active` | BooleanField | Active status |

**TariffService (Through Model):**
```python
- tariff: ForeignKey(Tariff)
- service: ForeignKey(Service)
- sessions_included: IntegerField    # Number of sessions in package
```

**TariffRoomPrice (Pricing Matrix):**
```python
- tariff: ForeignKey(Tariff)
- room_type: ForeignKey(RoomType)
- price: DecimalField(10,2)          # Price for this combination
```

**Example:**
```
Tariff: "Wellness Package"
Services:
  - Massage (5 sessions included)
  - Pool Access (unlimited)
  - Gym Access (unlimited)

Pricing:
  - Standard Room: 500,000 UZS
  - Deluxe Room: 750,000 UZS
  - Suite: 1,200,000 UZS
```

---

#### Service (`/core/models/services.py`)

| Field | Type | Purpose |
|-------|------|---------|
| `type` | ForeignKey(ServiceTypeModel) | Service category |
| `name` | CharField(200) | Service name |
| `description` | TextField | Description |
| `duration_minutes` | IntegerField | Duration |
| `price` | DecimalField(10,2) | Per-session price |
| `is_active` | BooleanField | Active status |

**ServiceTypeModel:**
```python
- name: CharField(200)               # e.g., "Massage", "Pool", "Medical"
- description: TextField
```

---

#### ServiceUsage (`/core/models/services.py`)

**Purpose:** Track additional services used during stay

| Field | Type | Purpose |
|-------|------|---------|
| `booking` | ForeignKey(Booking) | Parent booking |
| `booking_detail` | ForeignKey(BookingDetail) | Guest |
| `service` | ForeignKey(Service) | Service used |
| `quantity` | IntegerField | Number of times |
| `price` | DecimalField(10,2) | Total price |
| `date_used` | DateField | Usage date |
| `notes` | TextField | Notes |

---

#### ServiceSessionTracking (`/core/models/services.py`)

**Purpose:** Track usage of tariff-included services

| Field | Type | Purpose |
|-------|------|---------|
| `booking_detail` | ForeignKey(BookingDetail) | Guest |
| `service` | ForeignKey(Service) | Service tracked |
| `tariff_service` | ForeignKey(TariffService) | Tariff link |
| `sessions_included` | IntegerField | Sessions in tariff |
| `sessions_used` | IntegerField | Sessions consumed |
| `sessions_billed` | IntegerField | Sessions charged |

**Properties:**
```python
@property
def sessions_remaining(self):
    return max(0, self.sessions_included - self.sessions_used)

@property
def sessions_exceeded(self):
    return max(0, self.sessions_used - self.sessions_included)
```

**Issues Identified:**
- ⚠️ No UI to increment `sessions_used`
- ⚠️ No automatic billing when sessions exceed included amount
- ⚠️ No scheduling/appointment system for services

---

### 5. Medical Record Models

#### IllnessHistory (`/core/models/illness_history.py`)

**Purpose:** Medical record for patient stay

| Field | Type | Purpose |
|-------|------|---------|
| `series_number` | CharField(50) | Unique identifier |
| `patient` | ForeignKey(PatientModel) | Patient |
| `booking` | ForeignKey(Booking) | Related booking |
| `type` | CharField(20) | STATIONARY/AMBULATORY |
| `is_sick_leave` | BooleanField | Sick leave issued |
| `profession` | ForeignKey(ProfessionModel) | Patient profession |
| `toxic_factors` | ManyToMany(ToxicFactorModel) | Work hazards |
| `tags` | ForeignKey(TagModel) | Classification tags |
| `state` | CharField(20) | REGISTRATION/OPEN/CLOSED |
| `initial_diagnosis` | ForeignKey(DiagnosisTemplate) | Initial diagnosis |
| `at_arrival_diagnosis` | ForeignKey(DiagnosisTemplate) | Arrival diagnosis |
| `diagnosis` | ForeignKey(DiagnosisTemplate) | Final diagnosis |
| `nurses` | ManyToMany(Account) | Assigned nurses |
| `doctor` | ForeignKey(Account) | Assigned doctor |
| `notes` | TextField | Medical notes |

**Auto-Creation Signal:**
```python
@receiver(post_save, sender=Booking)
def create_illness_history(sender, instance, created, **kwargs):
    """
    When booking status changes to CHECKED_IN,
    automatically create IllnessHistory for each guest
    """
    if instance.status == 'checked_in':
        for detail in instance.booking_details.all():
            if not IllnessHistory.objects.filter(
                patient=detail.client,
                booking=instance
            ).exists():
                IllnessHistory.objects.create(
                    patient=detail.client,
                    booking=instance,
                    state='registration',
                    type='STATIONARY'
                )
```

**Issues Identified:**
- ⚠️ State transitions not enforced
- ⚠️ No validation that doctor is assigned
- ⚠️ Auto-creation happens on check-in but doctor might not be available
- ⚠️ No connection to appointment scheduling

---

## PATIENT REGISTRATION WORKFLOW

### Registration Entry Points

**1. Direct Registration**
```
URL: /logus/patients/create/
View: patient_create_view()
Form: PatientForm (full registration)
```

**2. Quick Registration (During Booking)**
```
URL: /logus/patients/quick-create/
View: patient_quick_create()
Form: PatientQuickForm (minimal fields)
Method: AJAX POST → Returns JSON
```

**3. Patient Registration Page**
```
URL: /logus/booking/patient-registration/
View: patient_registration()
Form: SimplePatientForm
```

### Registration Forms

#### 1. PatientForm (Full Registration)
**Location:** `/application/logus/forms/patient_form.py`

**Fields:**
```python
- f_name (required)
- mid_name (optional)
- l_name (required)
- email (optional, unique)
- date_of_birth (required, date widget)
- home_phone_number (optional)
- mobile_phone_number (required)
- address (optional, textarea)
- gender (required, radio buttons)
- gestational_age (optional, for pregnant patients)
- region (required, Select2 dropdown)
- district (required, Select2 dropdown, cascading)
- doc_type (optional)
- doc_number (optional)
- INN (optional)
- country (optional)
```

**Widgets:**
```python
date_of_birth: DateInput with type='date'
region: Select2Single
district: Select2Single (populated via AJAX)
gender: RadioSelect
address: Textarea (rows=3)
```

**JavaScript:**
```javascript
// Cascading region → district
$('#id_region').change(function() {
    const regionId = $(this).val();
    $.ajax({
        url: '/logus/patients/get-districts/',
        data: { region_id: regionId },
        success: function(data) {
            $('#id_district').empty();
            data.forEach(district => {
                $('#id_district').append(
                    $('<option>').val(district.id).text(district.name)
                );
            });
        }
    });
});
```

---

#### 2. SimplePatientForm (Quick Registration)
**Location:** `/application/logus/forms/patient_form.py`

**Fields:**
```python
- f_name (required)
- mid_name (optional)
- l_name (required)
- date_of_birth (required)
- gender (required, radio)
- mobile_phone_number (required)
```

**Use Case:** Fast registration during booking process

---

#### 3. PatientQuickForm (AJAX Modal)
**Location:** `/application/logus/forms/patient_form.py`

**Fields:**
```python
- f_name (required)
- mid_name (optional)
- l_name (required)
- date_of_birth (required, masked input: DD.MM.YYYY)
- gender (required)
- mobile_phone_number (required, masked input)
```

**Features:**
- Input masks for date and phone
- Minimal validation
- Returns JSON response

---

### Patient Management Views

#### Patient List
```
URL: /logus/patients/
View: PatientListView (ListView)
Template: patients_list.html

Features:
- Pagination (15 per page)
- Search query parameter
- Active patients filter (is_active=True)
- Ordered by created_at DESC
```

**Search Fields:**
```python
Q(f_name__icontains=query) |
Q(l_name__icontains=query) |
Q(mid_name__icontains=query) |
Q(mobile_phone_number__icontains=query) |
Q(email__icontains=query)
```

---

#### Patient Detail
```
URL: /logus/patients/<patient_id>/
View: PatientDetailView (DetailView)
Template: patient_detail.html

Displays:
- Full patient information
- Related bookings (with status)
- Illness histories
- Contact information
- Audit trail (created_by, created_at, updated_at)
```

---

#### Patient Update
```
URL: /logus/patients/<patient_id>/update/
View: PatientUpdateView (UpdateView)
Form: PatientForm
Template: patient_form.html

Features:
- All fields editable (including is_active)
- Region/District cascading dropdown
- Audit trail updated (modified_by, updated_at)
- Success message on save
```

---

### AJAX Endpoints

#### Get Districts
```
URL: /logus/patients/get-districts/
Method: GET
Parameters: region_id

Response:
[
    {"id": 1, "name": "District 1"},
    {"id": 2, "name": "District 2"}
]
```

#### Quick Create Patient
```
URL: /logus/patients/quick-create/
Method: POST
Form Data: PatientQuickForm fields

Response (Success):
{
    "success": true,
    "patient_id": 42,
    "patient_name": "John Doe"
}

Response (Error):
{
    "success": false,
    "errors": {
        "mobile_phone_number": ["This field is required"]
    }
}
```

---

### Patient Registration Process Flow

```
┌─────────────────────────────────────────────────────────────┐
│ START: User needs to register patient                        │
└───────────────┬─────────────────────────────────────────────┘
                │
                ▼
        ┌───────────────┐
        │ Entry Point?  │
        └───┬───────┬───┘
            │       │
    ┌───────┘       └────────┐
    │                        │
    ▼                        ▼
┌─────────────┐      ┌──────────────┐
│ Direct      │      │ During       │
│ Registration│      │ Booking      │
└──────┬──────┘      └──────┬───────┘
       │                    │
       ▼                    ▼
┌─────────────┐      ┌──────────────┐
│ Full Form   │      │ Quick Form   │
│ All fields  │      │ Min fields   │
└──────┬──────┘      └──────┬───────┘
       │                    │
       └────────┬───────────┘
                ▼
        ┌───────────────┐
        │ Select Region │
        └───────┬───────┘
                ▼
        ┌───────────────┐
        │ AJAX Load     │
        │ Districts     │
        └───────┬───────┘
                ▼
        ┌───────────────┐
        │ Select District│
        └───────┬───────┘
                ▼
        ┌───────────────┐
        │ Fill Other    │
        │ Details       │
        └───────┬───────┘
                ▼
        ┌───────────────┐
        │ Validate Form │
        └───┬───────┬───┘
            │       │
      Valid │       │ Invalid
            │       │
            ▼       ▼
    ┌───────────┐  ┌──────────┐
    │ Create    │  │ Show     │
    │ Patient   │  │ Errors   │
    └─────┬─────┘  └────┬─────┘
          │             │
          │             └─────┐
          ▼                   │
    ┌───────────┐             │
    │ Auto-fill │             │
    │ Audit     │             │
    │ Fields    │             │
    └─────┬─────┘             │
          │                   │
          ▼                   │
    ┌───────────┐             │
    │ Save to   │             │
    │ Database  │             │
    └─────┬─────┘             │
          │                   │
          ▼                   │
    ┌───────────┐             │
    │ Success   │             │
    │ Message   │◄────────────┘
    └─────┬─────┘
          │
          ▼
    ┌───────────┐
    │ Redirect  │
    │ to Next   │
    └───────────┘
```

---

## BOOKING CREATION PROCESS

### Three-Step Booking Wizard

The booking process is implemented as a **three-step wizard** with session-based state management.

---

### Step 1: Initial Booking Setup

```
URL: /logus/booking/start/
View: booking_start()
Method: GET (display form), POST (process form)
Form: BookingInitialForm
Template: booking_start.html
```

**Form Fields:**
```python
class BookingInitialForm(forms.Form):
    patient = forms.ModelChoiceField(
        queryset=PatientModel.objects.filter(is_active=True),
        widget=Select2Single,
        label="Пациент"
    )
    date_range = forms.CharField(
        widget=forms.TextInput(attrs={
            'placeholder': 'ДД.ММ.ГГГГ - ДД.ММ.ГГГГ',
            'class': 'daterange-picker'
        }),
        label="Даты заезда и выезда"
    )
    guests_count = forms.IntegerField(
        min_value=1,
        max_value=10,
        initial=1,
        label="Количество гостей"
    )
```

**Validation:**
```python
def clean(self):
    data = super().clean()
    date_range = data.get('date_range')

    # Parse date range: "20.12.2024 - 25.12.2024"
    try:
        start_str, end_str = date_range.split(' - ')
        start_date = datetime.strptime(start_str.strip(), '%d.%m.%Y')
        end_date = datetime.strptime(end_str.strip(), '%d.%m.%Y')
    except:
        raise ValidationError("Неверный формат дат")

    # Validate start date not in past
    if start_date.date() < timezone.now().date():
        raise ValidationError("Дата заезда не может быть в прошлом")

    # Validate end date after start date
    if end_date <= start_date:
        raise ValidationError("Дата выезда должна быть после даты заезда")

    # Validate duration <= 30 days
    if (end_date - start_date).days > 30:
        raise ValidationError("Максимальная продолжительность бронирования - 30 дней")

    data['start_date'] = start_date
    data['end_date'] = end_date
    return data
```

**Process:**
```python
def booking_start(request):
    if request.method == 'POST':
        form = BookingInitialForm(request.POST)
        if form.is_valid():
            # Store in session
            request.session['booking_data'] = {
                'patient_id': form.cleaned_data['patient'].id,
                'start_date': form.cleaned_data['start_date'].isoformat(),
                'end_date': form.cleaned_data['end_date'].isoformat(),
                'guests_count': form.cleaned_data['guests_count'],
                'date_range': form.cleaned_data['date_range']
            }
            return redirect('logus:booking_select_rooms')
    else:
        form = BookingInitialForm()

    return render(request, 'logus/booking/booking_start.html', {
        'form': form
    })
```

---

### Step 2: Room Selection

```
URL: /logus/booking/select-rooms/
View: booking_select_rooms()
Method: GET (display form), POST (process form)
Form: RoomSelectionForm (dynamically generated)
Template: booking_select_rooms.html
```

**Dynamic Form Generation:**
```python
class RoomSelectionForm(forms.Form):
    def __init__(self, *args, **kwargs):
        guests_count = kwargs.pop('guests_count')
        available_rooms = kwargs.pop('available_rooms')
        super().__init__(*args, **kwargs)

        # Create one dropdown per guest
        for i in range(guests_count):
            self.fields[f'room_{i}'] = forms.ModelChoiceField(
                queryset=available_rooms,
                widget=forms.Select(attrs={'class': 'form-control'}),
                label=f"Комната для гостя {i+1}"
            )
```

**Room Availability Logic:**
```python
def get_available_rooms(start_date, end_date):
    """
    Returns rooms that are NOT occupied during the date range
    """
    # Get all occupied room IDs
    occupied_room_ids = BookingDetail.objects.filter(
        booking__status__in=['pending', 'confirmed', 'checked_in', 'in_progress'],
        booking__start_date__lt=end_date,
        booking__end_date__gt=start_date
    ).values_list('room_id', flat=True).distinct()

    # Return rooms not in occupied list
    return Room.objects.filter(
        is_active=True
    ).exclude(
        id__in=occupied_room_ids
    )
```

**Availability Matrix:**
```python
def get_room_type_availability(start_date, end_date):
    """
    Returns availability by room type and date
    """
    date_range = get_date_range(start_date, end_date)
    room_types = RoomType.objects.all()

    availability = {}
    for room_type in room_types:
        availability[room_type.name] = {}
        for date in date_range:
            day_start = datetime.combine(date, time.min)
            day_end = datetime.combine(date, time.max)

            available_count = get_available_rooms(day_start, day_end).filter(
                room_type=room_type
            ).count()

            total_count = Room.objects.filter(
                room_type=room_type,
                is_active=True
            ).count()

            availability[room_type.name][date] = {
                'available': available_count,
                'total': total_count,
                'percentage': (available_count / total_count * 100) if total_count > 0 else 0
            }

    return availability
```

**View Process:**
```python
def booking_select_rooms(request):
    # Retrieve from session
    booking_data = request.session.get('booking_data')
    if not booking_data:
        return redirect('logus:booking_start')

    start_date = datetime.fromisoformat(booking_data['start_date'])
    end_date = datetime.fromisoformat(booking_data['end_date'])
    guests_count = booking_data['guests_count']

    available_rooms = get_available_rooms(start_date, end_date)

    if request.method == 'POST':
        form = RoomSelectionForm(
            request.POST,
            guests_count=guests_count,
            available_rooms=available_rooms
        )
        if form.is_valid():
            # Extract selected room IDs
            selected_rooms = []
            for i in range(guests_count):
                room = form.cleaned_data[f'room_{i}']
                selected_rooms.append(room.id)

            # Store in session
            booking_data['selected_rooms'] = selected_rooms
            request.session['booking_data'] = booking_data

            return redirect('logus:booking_confirm')
    else:
        form = RoomSelectionForm(
            guests_count=guests_count,
            available_rooms=available_rooms
        )

    # Get availability matrix
    availability = get_room_type_availability(start_date, end_date)

    return render(request, 'logus/booking/booking_select_rooms.html', {
        'form': form,
        'availability': availability,
        'start_date': start_date,
        'end_date': end_date
    })
```

---

### Step 3: Confirmation & Creation

```
URL: /logus/booking/confirm/
View: booking_confirm()
Method: GET (display summary), POST (create booking)
Form: BookingConfirmationForm
Template: booking_confirm.html
```

**Form:**
```python
class BookingConfirmationForm(forms.Form):
    notes = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3}),
        required=False,
        label="Примечания"
    )
```

**View Process:**
```python
@transaction.atomic
def booking_confirm(request):
    # Retrieve from session
    booking_data = request.session.get('booking_data')
    if not booking_data:
        return redirect('logus:booking_start')

    patient = PatientModel.objects.get(id=booking_data['patient_id'])
    start_date = datetime.fromisoformat(booking_data['start_date'])
    end_date = datetime.fromisoformat(booking_data['end_date'])
    selected_rooms = booking_data['selected_rooms']

    rooms = Room.objects.filter(id__in=selected_rooms)

    if request.method == 'POST':
        form = BookingConfirmationForm(request.POST)
        if form.is_valid():
            # Create Booking
            booking = Booking.objects.create(
                booking_number=Booking.generate_booking_number(),
                staff=request.user,
                start_date=start_date,
                end_date=end_date,
                notes=form.cleaned_data['notes'],
                status='confirmed'
            )

            # Get default tariff (or first active tariff)
            default_tariff = Tariff.objects.filter(is_active=True).first()
            if not default_tariff:
                messages.error(request, "Нет активных тарифов")
                return redirect('logus:booking_start')

            # Create BookingDetail for each room
            for room in rooms:
                # Look up price from TariffRoomPrice
                tariff_price = TariffRoomPrice.objects.filter(
                    tariff=default_tariff,
                    room_type=room.room_type
                ).first()

                price = tariff_price.price if tariff_price else room.price

                BookingDetail.objects.create(
                    booking=booking,
                    client=patient,
                    room=room,
                    tariff=default_tariff,
                    price=price,
                    effective_from=start_date,
                    is_current=True
                )

            # Clear session
            del request.session['booking_data']

            messages.success(request, f"Бронирование {booking.booking_number} создано")
            return redirect('logus:booking_detail_view', booking_id=booking.id)
    else:
        form = BookingConfirmationForm()

    return render(request, 'logus/booking/booking_confirm.html', {
        'form': form,
        'patient': patient,
        'start_date': start_date,
        'end_date': end_date,
        'rooms': rooms
    })
```

**Booking Creation Flow:**
```
1. Create Booking record
   - Generate unique booking_number
   - Set staff = current user
   - Set dates from session
   - Set status = 'confirmed'

2. Get default tariff
   - Query first active Tariff
   - Abort if none found

3. For each selected room:
   a. Lookup TariffRoomPrice
      - tariff = default_tariff
      - room_type = room.room_type

   b. Calculate price
      - If TariffRoomPrice exists: use tariff_price.price
      - Else: fallback to room.price

   c. Create BookingDetail
      - booking = new booking
      - client = patient
      - room = current room
      - tariff = default_tariff
      - price = calculated price
      - effective_from = start_date
      - is_current = True

   d. Trigger post_save signal
      - Auto-create ServiceSessionTracking records
      - One record per service in tariff

4. Clear session['booking_data']

5. Redirect to booking detail page
```

---

### Booking Management Views

#### Booking List

```
URL: /logus/booking/list/
View: booking_list()
Template: booking_list.html
```

**Features:**
- Filter by date range
- Filter by status
- Search by booking number or patient name
- Statistics summary
- Pagination
- Upcoming check-ins

**Implementation:**
```python
def booking_list(request):
    bookings = Booking.objects.all().select_related(
        'staff'
    ).prefetch_related(
        'booking_details__client',
        'booking_details__room'
    ).order_by('-created_at')

    # Filter by date range
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    if date_from and date_to:
        try:
            start = datetime.strptime(date_from, '%d.%m.%Y')
            end = datetime.strptime(date_to, '%d.%m.%Y')
            bookings = bookings.filter(
                start_date__gte=start,
                start_date__lte=end
            )
        except ValueError:
            messages.warning(request, "Неверный формат даты")

    # Filter by status
    status = request.GET.get('status')
    if status:
        bookings = bookings.filter(status=status)

    # Search
    search = request.GET.get('search')
    if search:
        bookings = bookings.filter(
            Q(booking_number__icontains=search) |
            Q(booking_details__client__f_name__icontains=search) |
            Q(booking_details__client__l_name__icontains=search)
        ).distinct()

    # Statistics
    total_count = bookings.count()
    stats = {
        'total': total_count,
        'pending': bookings.filter(status='pending').count(),
        'confirmed': bookings.filter(status='confirmed').count(),
        'checked_in': bookings.filter(status='checked_in').count(),
        'completed': bookings.filter(status='completed').count(),
        'cancelled': bookings.filter(status='cancelled').count(),
    }

    # Upcoming check-ins (next 3 days)
    today = timezone.now().date()
    upcoming_date = today + timedelta(days=3)
    upcoming_bookings = Booking.objects.filter(
        status__in=['pending', 'confirmed'],
        start_date__gte=today,
        start_date__lte=upcoming_date
    ).order_by('start_date')

    # Paginate
    paginator = Paginator(bookings, 25)
    page = request.GET.get('page')
    bookings_page = paginator.get_page(page)

    return render(request, 'logus/booking/booking_list.html', {
        'bookings': bookings_page,
        'stats': stats,
        'upcoming_bookings': upcoming_bookings,
        'status_choices': Booking.STATUS_CHOICES
    })
```

---

#### Booking Detail

```
URL: /logus/booking/detail/<booking_id>/
View: booking_detail_view()
Template: booking_detail.html
```

**Displays:**
- Booking summary (number, dates, status, notes)
- All guests (BookingDetail records)
  - Patient info
  - Room assignment
  - Tariff
  - Price
- Tariff services with session tracking
  - Sessions included
  - Sessions used
  - Sessions remaining
- Additional services used (ServiceUsage)
  - Service name
  - Quantity
  - Price
  - Date used
- Illness histories
- Financial summary
  - Tariff base total
  - Additional services total
  - Grand total
- Action buttons (based on status)

**Implementation:**
```python
def booking_detail_view(request, booking_id):
    booking = get_object_or_404(
        Booking.objects.select_related('staff'),
        id=booking_id
    )

    booking_details = booking.booking_details.select_related(
        'client',
        'room',
        'tariff'
    ).filter(is_current=True)

    # Get service session tracking
    for detail in booking_details:
        detail.service_tracking = ServiceSessionTracking.objects.filter(
            booking_detail=detail
        ).select_related('service', 'tariff_service')

    # Get additional services
    additional_services = ServiceUsage.objects.filter(
        booking=booking
    ).select_related('service', 'booking_detail__client')

    # Get illness histories
    illness_histories = IllnessHistory.objects.filter(
        booking=booking
    ).select_related('patient', 'doctor')

    # Calculate financial summary
    tariff_total = sum(detail.price for detail in booking_details)
    services_total = sum(service.price for service in additional_services)
    grand_total = tariff_total + services_total

    return render(request, 'logus/booking/booking_detail.html', {
        'booking': booking,
        'booking_details': booking_details,
        'additional_services': additional_services,
        'illness_histories': illness_histories,
        'tariff_total': tariff_total,
        'services_total': services_total,
        'grand_total': grand_total
    })
```

---

#### Status Update (AJAX)

```
URL: /logus/booking/status/<booking_id>/
View: update_booking_status()
Method: POST
```

**Implementation:**
```python
@require_POST
def update_booking_status(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    new_status = request.POST.get('status')

    if new_status not in dict(Booking.STATUS_CHOICES):
        return JsonResponse({'success': False, 'error': 'Invalid status'})

    old_status = booking.status
    booking.status = new_status

    # Append to notes
    timestamp = timezone.now().strftime('%d.%m.%Y %H:%M')
    booking.notes += f"\n[{timestamp}] Статус изменен: {old_status} → {new_status} ({request.user.get_full_name()})"

    booking.save()

    return JsonResponse({
        'success': True,
        'status': new_status,
        'status_display': booking.get_status_display()
    })
```

---

#### Edit Booking

```
URL: /logus/booking/<booking_id>/edit/
View: booking_edit_view()
Form: BookingForm
Template: booking_form.html
```

**Form:**
```python
class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['start_date', 'end_date', 'notes', 'status']
        widgets = {
            'start_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'notes': forms.Textarea(attrs={'rows': 4}),
        }

    def clean(self):
        data = super().clean()

        # Cannot edit cancelled or completed bookings
        if self.instance.status in ['cancelled', 'completed']:
            raise ValidationError("Невозможно редактировать завершенное или отмененное бронирование")

        # Validate dates
        if data['end_date'] <= data['start_date']:
            raise ValidationError("Дата выезда должна быть после даты заезда")

        return data
```

---

#### Add Guest to Existing Booking

```
URL: /logus/booking/<booking_id>/add-guest/
View: booking_detail_add_view()
Form: BookingDetailForm
Template: booking_detail_form.html
```

**Form:**
```python
class BookingDetailForm(forms.ModelForm):
    class Meta:
        model = BookingDetail
        fields = ['client', 'room', 'tariff', 'price']
        widgets = {
            'client': Select2Single,
            'room': forms.Select,
            'tariff': forms.Select,
        }

    def __init__(self, *args, **kwargs):
        booking = kwargs.pop('booking')
        super().__init__(*args, **kwargs)

        # Filter available rooms for booking dates
        available_rooms = get_available_rooms(
            booking.start_date,
            booking.end_date
        )
        self.fields['room'].queryset = available_rooms

        # Filter active tariffs
        self.fields['tariff'].queryset = Tariff.objects.filter(is_active=True)
```

**View:**
```python
@transaction.atomic
def booking_detail_add_view(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)

    if booking.status in ['cancelled', 'completed']:
        messages.error(request, "Невозможно добавить гостя к завершенному бронированию")
        return redirect('logus:booking_detail_view', booking_id=booking.id)

    if request.method == 'POST':
        form = BookingDetailForm(request.POST, booking=booking)
        if form.is_valid():
            detail = form.save(commit=False)
            detail.booking = booking
            detail.effective_from = booking.start_date
            detail.is_current = True
            detail.save()

            messages.success(request, "Гость добавлен")
            return redirect('logus:booking_detail_view', booking_id=booking.id)
    else:
        form = BookingDetailForm(booking=booking)

    return render(request, 'logus/booking/booking_detail_form.html', {
        'form': form,
        'booking': booking
    })
```

---

#### Edit Guest

```
URL: /logus/booking/booking-details/<detail_id>/edit/
View: booking_detail_edit_view()
Form: BookingDetailForm
Template: booking_detail_form.html
```

**Allows Changing:**
- Patient assignment
- Room assignment
- Tariff
- Price

---

#### Delete Guest

```
URL: /logus/booking/booking-details/<detail_id>/delete/
View: booking_detail_delete_view()
Method: POST (confirmation)
```

**Restrictions:**
```python
def booking_detail_delete_view(request, detail_id):
    detail = get_object_or_404(BookingDetail, id=detail_id)
    booking = detail.booking

    # Cannot delete if only guest
    if booking.booking_details.filter(is_current=True).count() <= 1:
        messages.error(request, "Невозможно удалить последнего гостя")
        return redirect('logus:booking_detail_view', booking_id=booking.id)

    # Cannot delete from completed bookings
    if booking.status in ['cancelled', 'completed']:
        messages.error(request, "Невозможно удалить гостя из завершенного бронирования")
        return redirect('logus:booking_detail_view', booking_id=booking.id)

    detail.delete()
    messages.success(request, "Гость удален")
    return redirect('logus:booking_detail_view', booking_id=booking.id)
```

---

## CURRENT FEATURES INVENTORY

### ✅ Implemented Features

#### Patient Management
- [x] Patient registration (full form)
- [x] Patient quick registration (minimal form)
- [x] Patient list with search
- [x] Patient detail view
- [x] Patient update/edit
- [x] Region/District cascading dropdowns
- [x] Active/inactive patient filtering
- [x] Audit trail (created_by, modified_by, timestamps)

#### Booking Management
- [x] Three-step booking wizard
  - [x] Step 1: Patient, dates, guest count
  - [x] Step 2: Room selection with availability matrix
  - [x] Step 3: Confirmation and creation
- [x] Booking list with filters
  - [x] Date range filter
  - [x] Status filter
  - [x] Search (booking #, patient name)
- [x] Booking detail view
- [x] Booking status update
- [x] Booking edit
- [x] Add guest to existing booking
- [x] Edit guest details
- [x] Remove guest from booking
- [x] Booking statistics dashboard
- [x] Upcoming check-ins widget

#### Room Management
- [x] Room availability calculation
- [x] Availability matrix by room type and date
- [x] Occupancy rate calculation
- [x] Room assignment to guests
- [x] Room type categorization

#### Tariff & Pricing
- [x] Tariff selection for bookings
- [x] Tariff-room type pricing matrix
- [x] Price calculation from TariffRoomPrice
- [x] Fallback to room base price
- [x] Included services tracking
- [x] Service session tracking (included, used, remaining)

#### Service Management
- [x] Service usage recording
- [x] Additional service charges
- [x] Service session tracking per booking detail
- [x] Auto-initialization of session tracking

#### Billing Integration
- [x] BookingBilling auto-creation
- [x] Multi-component billing (tariff, services, medications, labs)
- [x] Billing status tracking
- [x] Total calculation

#### Medical Integration
- [x] Auto-create IllnessHistory on check-in
- [x] Link booking to medical records
- [x] Patient medical history tracking

#### Dashboard
- [x] Reception dashboard with quick stats
- [x] Current guests list
- [x] Room availability overview
- [x] Quick booking link

---

## MISSING FEATURES

### 🔴 Critical Missing Features

#### 1. **Mid-Stay Tariff/Room Changes**
**Status:** Method exists, no UI

**Impact:** HIGH - Cannot handle patient upgrades/downgrades

**Implementation:**
```python
# Method exists in model:
BookingDetail.change_tariff(booking_detail, new_tariff, new_room, change_date)

# Need to create:
- View: tariff_change_view()
- URL: /logus/booking/booking-details/<detail_id>/change-tariff/
- Template: booking_detail_tariff_change.html
- Form: TariffChangeForm
```

**Form Required:**
```python
class TariffChangeForm(forms.Form):
    new_tariff = forms.ModelChoiceField(
        queryset=Tariff.objects.filter(is_active=True),
        label="Новый тариф"
    )
    new_room = forms.ModelChoiceField(
        queryset=Room.objects.filter(is_active=True),
        label="Новая комната"
    )
    change_date = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        label="Дата изменения"
    )
    reason = forms.CharField(
        widget=forms.Textarea,
        label="Причина изменения"
    )
```

---

#### 2. **Service Session Management UI**
**Status:** Tracking exists, no UI to update

**Impact:** HIGH - Cannot track actual service usage

**Missing Components:**
- View to increment `sessions_used`
- UI to mark service as completed
- Automatic billing when sessions exceed included amount
- Service scheduling/appointment system

**Required Implementation:**
```python
# View to record service usage
def record_service_session(request, tracking_id):
    tracking = get_object_or_404(ServiceSessionTracking, id=tracking_id)

    if request.method == 'POST':
        # Increment sessions_used
        tracking.sessions_used += 1

        # If exceeded, create ServiceUsage for billing
        if tracking.sessions_exceeded > 0:
            ServiceUsage.objects.create(
                booking=tracking.booking_detail.booking,
                booking_detail=tracking.booking_detail,
                service=tracking.service,
                quantity=1,
                price=tracking.service.price,
                date_used=timezone.now().date()
            )

        tracking.save()
        messages.success(request, "Сеанс записан")

    return redirect('logus:booking_detail_view', booking_id=tracking.booking_detail.booking.id)
```

---

#### 3. **Duplicate Patient Detection**
**Status:** Not implemented

**Impact:** HIGH - Data quality issues

**Current Situation:**
- No check for duplicate patients by:
  - Name + date of birth
  - Phone number
  - Document number
  - Email

**Required Implementation:**
```python
def check_duplicate_patient(f_name, l_name, date_of_birth, mobile_phone):
    """
    Check for potential duplicate patients
    Returns: list of potential matches
    """
    # Exact match by phone
    phone_matches = PatientModel.objects.filter(
        mobile_phone_number=mobile_phone
    )
    if phone_matches.exists():
        return list(phone_matches)

    # Fuzzy match by name + DOB
    name_dob_matches = PatientModel.objects.filter(
        f_name__iexact=f_name,
        l_name__iexact=l_name,
        date_of_birth=date_of_birth
    )
    if name_dob_matches.exists():
        return list(name_dob_matches)

    return []

# Add to form clean method:
def clean(self):
    data = super().clean()
    duplicates = check_duplicate_patient(
        data.get('f_name'),
        data.get('l_name'),
        data.get('date_of_birth'),
        data.get('mobile_phone_number')
    )
    if duplicates:
        self.add_error(None, f"Найдено {len(duplicates)} похожих пациентов")
        # Show list of duplicates for confirmation
    return data
```

---

#### 4. **Advance Reservation System**
**Status:** Not implemented

**Impact:** HIGH - Cannot handle future bookings properly

**Current Limitation:**
- Booking wizard validates start_date >= today
- No concept of "reservation" vs "active booking"
- No deposit/prepayment handling

**Required Features:**
- Reservation status (before PENDING)
- Deposit tracking
- Reservation expiration
- Confirmation workflow (reservation → confirmed)
- Waitlist when rooms unavailable

**Implementation Plan:**
```python
# Add to Booking.STATUS_CHOICES:
RESERVATION = "reservation"  # Before check-in

# New model:
class BookingDeposit(models.Model):
    booking = models.ForeignKey(Booking)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateTimeField()
    payment_method = models.CharField(max_length=50)
    transaction = models.ForeignKey(TransactionsModel, null=True)

# New view:
def create_reservation(request):
    # Similar to booking_confirm but:
    # - Set status = 'reservation'
    # - Collect deposit
    # - Set reservation expiration
    pass
```

---

#### 5. **Room Capacity Enforcement**
**Status:** Not enforced

**Impact:** MEDIUM - Can overbook rooms

**Current Situation:**
- Room has `capacity` field
- No validation that occupants <= capacity
- Can assign multiple BookingDetails to same room simultaneously

**Required Fix:**
```python
# In booking confirmation:
def validate_room_capacity(self):
    for room_id, occupants in room_occupancy.items():
        room = Room.objects.get(id=room_id)
        if occupants > room.capacity:
            raise ValidationError(
                f"Room {room.name} capacity ({room.capacity}) exceeded ({occupants} guests)"
            )
```

---

#### 6. **Phone Number Validation**
**Status:** No validation

**Impact:** MEDIUM - Data quality

**Required Implementation:**
```python
# In PatientForm:
def clean_mobile_phone_number(self):
    phone = self.cleaned_data['mobile_phone_number']

    # Remove non-digits
    digits_only = re.sub(r'\D', '', phone)

    # Validate Uzbekistan phone format
    if not re.match(r'^998\d{9}$', digits_only):
        raise ValidationError(
            "Неверный формат номера. Ожидается: +998XXXXXXXXX"
        )

    return f"+{digits_only}"

# Widget with input mask:
mobile_phone_number = forms.CharField(
    widget=forms.TextInput(attrs={
        'data-inputmask': "'mask': '+999 99 999-99-99'"
    })
)
```

---

#### 7. **Patient Search Enhancement**
**Status:** Basic substring search only

**Impact:** MEDIUM - Poor UX for receptionists

**Current Limitations:**
- Only searches 5 fields
- No advanced filters
- No search by age range
- No search by region/district
- No saved searches

**Required Implementation:**
```python
class AdvancedPatientSearchForm(forms.Form):
    # Text search
    query = forms.CharField(required=False)

    # Demographic filters
    gender = forms.ChoiceField(required=False)
    age_min = forms.IntegerField(required=False)
    age_max = forms.IntegerField(required=False)
    region = forms.ModelChoiceField(Region.objects.all(), required=False)
    district = forms.ModelChoiceField(District.objects.all(), required=False)

    # Date filters
    registered_from = forms.DateField(required=False)
    registered_to = forms.DateField(required=False)

    # Booking filters
    has_active_booking = forms.BooleanField(required=False)
    last_visit_from = forms.DateField(required=False)
    last_visit_to = forms.DateField(required=False)
```

---

### ⚠️ Important Missing Features

#### 8. **Booking Audit Trail**
**Status:** Basic audit exists, no detailed history

**Impact:** MEDIUM - Compliance/accountability

**Current:**
- `created_by`, `modified_by` fields
- Notes field with manual timestamp appends

**Missing:**
- Automatic change log
- Who changed what and when
- Reverting to previous state
- Detailed action history

**Implementation:**
```python
class BookingHistory(models.Model):
    booking = models.ForeignKey(Booking)
    action = models.CharField(max_length=50)  # created, updated, status_changed, etc.
    field_name = models.CharField(max_length=100)
    old_value = models.TextField()
    new_value = models.TextField()
    changed_by = models.ForeignKey(Account)
    changed_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True)

    class Meta:
        ordering = ['-changed_at']

# Signal to auto-create history:
@receiver(post_save, sender=Booking)
def log_booking_change(sender, instance, created, **kwargs):
    # Compare with previous state and log changes
    pass
```

---

#### 9. **Booking Reports & Analytics**
**Status:** Not implemented

**Impact:** MEDIUM - No business intelligence

**Missing Reports:**
- Occupancy reports (daily, weekly, monthly)
- Revenue reports
- Average length of stay
- Popular room types
- Cancellation rates
- No-show tracking
- Patient demographics
- Seasonal trends

**Required Implementation:**
```python
def booking_reports_view(request):
    # Date range selection
    # Report type selection
    # Generate report
    # Export to PDF/Excel
    pass

# Example reports:
- Occupancy Report
- Revenue Report
- Room Type Performance
- Cancellation Analysis
- Patient Demographics
- Length of Stay Analysis
```

---

#### 10. **Multi-Patient Booking Handling**
**Status:** Partial implementation

**Impact:** MEDIUM - UX issue for families

**Current:**
- Can book multiple rooms
- All rooms assigned to same patient (from step 1)
- Must manually edit to assign different patients

**Better Workflow:**
```
Step 1: Dates + Guest Count
Step 2: Room Selection
Step 3: Patient Assignment
  - For each room:
    - Select existing patient OR
    - Quick register new patient
Step 4: Confirmation
```

**Implementation:**
```python
# New form in step 3:
class PatientAssignmentForm(forms.Form):
    def __init__(self, *args, **kwargs):
        rooms = kwargs.pop('rooms')
        super().__init__(*args, **kwargs)

        for i, room in enumerate(rooms):
            self.fields[f'patient_{i}'] = forms.ModelChoiceField(
                queryset=PatientModel.objects.filter(is_active=True),
                required=False,
                label=f"Пациент для {room.name}"
            )
            self.fields[f'create_new_{i}'] = forms.BooleanField(
                required=False,
                label="Зарегистрировать нового"
            )
```

---

#### 11. **Room Maintenance Scheduling**
**Status:** Not implemented

**Impact:** MEDIUM - Operational efficiency

**Missing:**
- Room maintenance status
- Scheduled maintenance periods
- Mark room as "under maintenance"
- Exclude from availability during maintenance
- Maintenance history

**Implementation:**
```python
class RoomMaintenance(models.Model):
    room = models.ForeignKey(Room)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    maintenance_type = models.CharField(max_length=50)  # cleaning, repair, renovation
    description = models.TextField()
    status = models.CharField(max_length=20)  # scheduled, in_progress, completed
    performed_by = models.ForeignKey(Account)

# Update get_available_rooms():
def get_available_rooms(start_date, end_date):
    # Existing logic...

    # Exclude rooms under maintenance
    maintenance_room_ids = RoomMaintenance.objects.filter(
        status__in=['scheduled', 'in_progress'],
        start_date__lt=end_date,
        end_date__gt=start_date
    ).values_list('room_id', flat=True)

    available_rooms = available_rooms.exclude(id__in=maintenance_room_ids)

    return available_rooms
```

---

#### 12. **Payment Processing UI in Logus**
**Status:** Stub view exists, no implementation

**Impact:** MEDIUM - Receptionist workflow incomplete

**Current:**
- Payment processing handled in Cashbox module
- No quick payment link in booking detail
- Receptionist must navigate to cashbox

**Better Integration:**
```python
# Add to booking_detail.html:
{% if booking.billing.billing_status != 'paid' %}
<a href="{% url 'logus:quick_payment' booking.id %}" class="btn btn-success">
    Принять оплату
</a>
{% endif %}

# New view:
def quick_payment(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)

    if request.method == 'POST':
        form = QuickPaymentForm(request.POST)
        if form.is_valid():
            # Create transaction
            # Update billing status
            # Redirect back to booking detail
            pass
    else:
        form = QuickPaymentForm(initial={
            'amount': booking.billing.total_amount
        })

    return render(request, 'logus/payment/quick_payment.html', {
        'booking': booking,
        'form': form
    })
```

---

#### 13. **Check-in/Check-out Workflow**
**Status:** Basic status change only

**Impact:** MEDIUM - No formalized process

**Current:**
- Simple status update button
- No validation
- No checklist
- No signature capture
- No document printing

**Enhanced Workflow:**
```python
class CheckInForm(forms.Form):
    # Verify patient identity
    patient_present = forms.BooleanField(label="Пациент присутствует")
    id_verified = forms.BooleanField(label="Документ проверен")

    # Medical screening
    temperature = forms.DecimalField(max_digits=4, decimal_places=1, required=False)
    blood_pressure = forms.CharField(max_length=20, required=False)
    complaints = forms.CharField(widget=forms.Textarea, required=False)

    # Room assignment
    room_condition = forms.ChoiceField(choices=[
        ('good', 'Хорошее'),
        ('needs_cleaning', 'Требуется уборка'),
        ('damaged', 'Повреждения')
    ])

    # Assign doctor
    doctor = forms.ModelChoiceField(
        queryset=Account.objects.filter(role='doctor', is_active=True)
    )

    # Documents
    rules_explained = forms.BooleanField(label="Правила объяснены")
    consent_signed = forms.BooleanField(label="Согласие подписано")

def check_in_view(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)

    if request.method == 'POST':
        form = CheckInForm(request.POST)
        if form.is_valid():
            # Update booking status
            booking.status = 'checked_in'
            booking.save()

            # Create illness history (already automated via signal)

            # Assign doctor to illness history
            for history in booking.illness_histories.all():
                history.doctor = form.cleaned_data['doctor']
                history.state = 'open'
                history.save()

            # Log check-in details
            CheckInLog.objects.create(
                booking=booking,
                performed_by=request.user,
                **form.cleaned_data
            )

            # Print welcome packet
            return redirect('logus:print_welcome_packet', booking_id=booking.id)
    else:
        form = CheckInForm()

    return render(request, 'logus/booking/check_in.html', {
        'booking': booking,
        'form': form
    })
```

---

#### 14. **Waitlist Management**
**Status:** Not implemented

**Impact:** LOW-MEDIUM - Lost revenue opportunity

**When rooms are unavailable:**
- No option to add to waitlist
- No notification when room becomes available
- Manual follow-up required

**Implementation:**
```python
class Waitlist(models.Model):
    patient = models.ForeignKey(PatientModel)
    desired_start_date = models.DateField()
    desired_end_date = models.DateField()
    room_type = models.ForeignKey(RoomType, null=True)
    guests_count = models.IntegerField()
    priority = models.IntegerField(default=0)
    status = models.CharField(max_length=20)  # active, notified, converted, expired
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(Account)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-priority', 'created_at']

def check_waitlist_on_cancellation(booking):
    """
    When booking is cancelled, check if anyone on waitlist
    can be accommodated
    """
    # Find waitlist entries matching dates and room requirements
    # Send notifications
    pass
```

---

#### 15. **Document Generation & Printing**
**Status:** Not implemented

**Impact:** MEDIUM - Manual document creation

**Missing Documents:**
- Booking confirmation letter
- Welcome packet
- Room assignment slip
- Treatment schedule
- Check-out summary
- Invoice/receipt

**Implementation:**
```python
from reportlab.pdfgen import canvas
from django.http import HttpResponse

def print_booking_confirmation(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)

    # Create PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="booking_{booking.booking_number}.pdf"'

    p = canvas.Canvas(response)

    # Header
    p.drawString(100, 800, "HAYAT MEDICAL CENTER")
    p.drawString(100, 780, "Подтверждение бронирования")

    # Booking details
    p.drawString(100, 750, f"Номер бронирования: {booking.booking_number}")
    p.drawString(100, 730, f"Пациент: {booking.booking_details.first().client.full_name}")
    p.drawString(100, 710, f"Даты: {booking.start_date.strftime('%d.%m.%Y')} - {booking.end_date.strftime('%d.%m.%Y')}")

    # Rooms
    y = 680
    for detail in booking.booking_details.all():
        p.drawString(100, y, f"Комната: {detail.room.name} - {detail.tariff.name}")
        y -= 20

    # Footer
    p.drawString(100, 100, "Спасибо за выбор Hayat Medical Center!")

    p.showPage()
    p.save()

    return response
```

---

### 📋 Nice-to-Have Features

#### 16. **Calendar View**
**Status:** Not implemented

**Impact:** LOW - UX enhancement

**Current:** List view only

**Desired:** Interactive calendar showing:
- Bookings by date
- Room availability
- Color-coded statuses
- Drag-and-drop rebooking

---

#### 17. **SMS/Email Notifications**
**Status:** Not implemented

**Impact:** LOW - Customer service

**Use Cases:**
- Booking confirmation
- Check-in reminder (1 day before)
- Payment reminder
- Post-visit follow-up

---

#### 18. **Mobile-Responsive UI**
**Status:** AdminLTE3 is responsive, but forms may need work

**Impact:** LOW - Mobile usage

---

#### 19. **REST API**
**Status:** Not implemented

**Impact:** LOW - Future integrations

**For:**
- Mobile app
- Partner integrations
- Kiosk check-in

---

#### 20. **Multi-Language Support**
**Status:** Partial (Russian hardcoded)

**Impact:** LOW - International patients

**Current:**
- Some strings use `gettext_lazy()`
- Most strings hardcoded in Russian

**Required:**
- Full i18n implementation
- Language switcher
- Translate all strings

---

## SECURITY CONCERNS

### 🔴 Critical Security Issues

#### 1. **CSRF Exempt Decorator**
**Location:** `/application/logus/views/patient.py`

```python
@csrf_exempt
def patient_registration(request):
    # ...
```

**Risk:** HIGH - CSRF attacks possible

**Fix:**
```python
# Remove @csrf_exempt
# Ensure {% csrf_token %} in template
# Use POST method properly

def patient_registration(request):
    if request.method == 'POST':
        form = SimplePatientForm(request.POST)
        if form.is_valid():
            # Process
            pass
    else:
        form = SimplePatientForm()

    return render(request, template, {'form': form})
```

---

#### 2. **No Input Sanitization**
**Risk:** MEDIUM - XSS possible in notes fields

**Fix:**
```python
from django.utils.html import escape

# In templates, use:
{{ booking.notes|escape|linebreaks }}

# Or use Django's built-in autoescape (already enabled by default)
```

---

#### 3. **No Rate Limiting**
**Risk:** MEDIUM - Brute force, DoS

**Fix:**
```python
# Install django-ratelimit
from django_ratelimit.decorators import ratelimit

@ratelimit(key='ip', rate='10/m', method='POST')
def booking_start(request):
    # ...
```

---

#### 4. **Sensitive Data in Session**
**Risk:** LOW-MEDIUM - Session hijacking exposure

**Current:**
```python
request.session['booking_data'] = {
    'patient_id': 42,
    # ...
}
```

**Better:**
```python
# Use encrypted session backend
SESSION_ENGINE = 'django.contrib.sessions.backends.signed_cookies'

# Or store minimal data and re-query:
request.session['booking_token'] = uuid.uuid4().hex
# Store booking_data in cache with token as key
```

---

#### 5. **No Permission Checks on Some Views**
**Risk:** LOW - Depends on decorator coverage

**Audit Required:**
```bash
# Check all views have @login_required or @receptionist_required
grep -r "def.*_view" application/logus/views/
```

---

### ⚠️ Data Privacy Concerns

#### 6. **Patient Data Access Logging**
**Status:** Not implemented

**Requirement:** HIPAA/GDPR compliance

**Implementation:**
```python
class PatientAccessLog(models.Model):
    patient = models.ForeignKey(PatientModel)
    accessed_by = models.ForeignKey(Account)
    accessed_at = models.DateTimeField(auto_now_add=True)
    access_type = models.CharField(max_length=50)  # view, edit, delete
    ip_address = models.GenericIPAddressField()

@receiver(post_save, sender=PatientModel)
def log_patient_access(sender, instance, created, **kwargs):
    # Log access
    pass
```

---

#### 7. **Soft Delete vs Hard Delete**
**Current:** `is_active` flag (soft delete)

**Issue:** No hard delete capability for GDPR "right to be forgotten"

**Fix:**
```python
def patient_delete_permanently(request, patient_id):
    # Check if patient has any bookings
    # If yes, anonymize instead of delete
    # If no, hard delete
    pass
```

---

## PERFORMANCE OPTIMIZATION OPPORTUNITIES

### Database Query Optimization

#### 1. **N+1 Query Problem**
**Location:** Multiple views

**Example:**
```python
# BAD:
bookings = Booking.objects.all()
for booking in bookings:
    print(booking.booking_details.all())  # N+1 queries

# GOOD:
bookings = Booking.objects.prefetch_related('booking_details').all()
for booking in bookings:
    print(booking.booking_details.all())  # 2 queries total
```

**Fix All Views:**
```python
# booking_list view:
bookings = Booking.objects.select_related(
    'staff'
).prefetch_related(
    'booking_details__client',
    'booking_details__room',
    'booking_details__tariff'
).all()

# patient_detail view:
patient = PatientModel.objects.prefetch_related(
    'booking_details__booking',
    'illness_histories'
).get(id=patient_id)
```

---

#### 2. **Add Database Indexes**
**Current:** Likely missing indexes on frequently queried fields

**Add:**
```python
class Booking(models.Model):
    # ...
    class Meta:
        indexes = [
            models.Index(fields=['status', 'start_date']),
            models.Index(fields=['booking_number']),
            models.Index(fields=['-created_at']),
        ]

class PatientModel(models.Model):
    # ...
    class Meta:
        indexes = [
            models.Index(fields=['mobile_phone_number']),
            models.Index(fields=['f_name', 'l_name']),
            models.Index(fields=['is_active', '-created_at']),
        ]

class BookingDetail(models.Model):
    # ...
    class Meta:
        indexes = [
            models.Index(fields=['booking', 'is_current']),
            models.Index(fields=['client']),
        ]
```

---

#### 3. **Caching**
**Status:** No caching implemented

**Opportunities:**
```python
from django.core.cache import cache

# Cache room availability:
def get_available_rooms_cached(start_date, end_date):
    cache_key = f"available_rooms_{start_date}_{end_date}"
    rooms = cache.get(cache_key)

    if rooms is None:
        rooms = get_available_rooms(start_date, end_date)
        cache.set(cache_key, rooms, 300)  # 5 minutes

    return rooms

# Cache dashboard stats:
def get_dashboard_stats_cached():
    cache_key = "dashboard_stats"
    stats = cache.get(cache_key)

    if stats is None:
        stats = calculate_dashboard_stats()
        cache.set(cache_key, stats, 60)  # 1 minute

    return stats

# Invalidate cache on booking changes:
@receiver(post_save, sender=Booking)
def invalidate_availability_cache(sender, instance, **kwargs):
    # Clear relevant cache keys
    cache.delete_pattern("available_rooms_*")
    cache.delete("dashboard_stats")
```

---

#### 4. **Pagination Optimization**
**Current:** Django default paginator (counts all results)

**Optimize for large datasets:**
```python
from django.core.paginator import Paginator

# Add approximate count for large tables:
class ApproximatePaginator(Paginator):
    def __init__(self, *args, approximate_threshold=1000, **kwargs):
        super().__init__(*args, **kwargs)
        self.approximate_threshold = approximate_threshold

    @property
    def count(self):
        if not hasattr(self, '_count'):
            try:
                self._count = self.object_list.count()
            except (AttributeError, TypeError):
                self._count = len(self.object_list)

            # Use approximate count for large datasets
            if self._count > self.approximate_threshold:
                # PostgreSQL specific:
                cursor = connection.cursor()
                cursor.execute("SELECT reltuples FROM pg_class WHERE relname = 'logus_booking'")
                self._count = int(cursor.fetchone()[0])

        return self._count
```

---

### Frontend Optimization

#### 5. **Lazy Loading**
- Load availability matrix via AJAX
- Load booking details on demand
- Implement infinite scroll for long lists

---

#### 6. **Asset Optimization**
- Minify CSS/JS
- Combine files
- Use CDN for AdminLTE
- Enable gzip compression

---

## IMPROVEMENT RECOMMENDATIONS

### Code Quality

#### 1. **Remove Duplicate Code**
**Issue:** Multiple patient forms doing same thing

**Consolidate:**
```python
# Keep only:
- PatientForm (full registration)
- PatientQuickForm (minimal for AJAX)

# Remove:
- SimplePatientForm (duplicate of PatientQuickForm)
- PatientRegistrationForm (duplicate)
```

---

#### 2. **Remove Duplicate Views**
**Issue:** `add_new_patient()` and `patient_registration()` both exist

**Consolidate:**
```python
# Keep one implementation
# Remove the other
# Update URL routing
```

---

#### 3. **Consistent Form Validation**
**Issue:** Some forms validate in `clean()`, some in view

**Standardize:**
- All validation in form's `clean()` methods
- Views should only handle `form.is_valid()` check
- Custom validation in `clean_<field>()` methods

---

#### 4. **Error Handling**
**Current:** Basic error handling

**Improve:**
```python
import logging
logger = logging.getLogger(__name__)

def booking_confirm(request):
    try:
        # Booking creation logic
    except ValidationError as e:
        logger.warning(f"Booking validation failed: {e}")
        messages.error(request, str(e))
        return redirect('logus:booking_start')
    except Exception as e:
        logger.error(f"Unexpected error in booking_confirm: {e}", exc_info=True)
        messages.error(request, "Произошла ошибка. Пожалуйста, попробуйте снова.")
        return redirect('logus:booking_start')
```

---

#### 5. **Add Type Hints**
```python
from typing import Optional, List
from django.http import HttpRequest, HttpResponse

def booking_start(request: HttpRequest) -> HttpResponse:
    # ...

def get_available_rooms(
    start_date: datetime,
    end_date: datetime
) -> List[Room]:
    # ...
```

---

#### 6. **Add Docstrings**
```python
def get_available_rooms(start_date, end_date):
    """
    Returns list of rooms available for booking during specified date range.

    A room is considered available if it has no overlapping bookings
    with status in ['pending', 'confirmed', 'checked_in', 'in_progress'].

    Args:
        start_date (datetime): Check-in date
        end_date (datetime): Check-out date

    Returns:
        QuerySet[Room]: Available rooms

    Example:
        >>> start = datetime(2024, 12, 20, 14, 0)
        >>> end = datetime(2024, 12, 25, 12, 0)
        >>> rooms = get_available_rooms(start, end)
        >>> print([r.name for r in rooms])
        ['Room 101', 'Room 102', 'Room 203']
    """
    # Implementation
```

---

### Testing

#### 7. **Unit Tests**
```python
# /application/logus/tests/test_booking.py

from django.test import TestCase
from core.models import Booking, PatientModel, Room

class BookingCreationTestCase(TestCase):
    def setUp(self):
        self.patient = PatientModel.objects.create(...)
        self.room = Room.objects.create(...)

    def test_booking_number_generation(self):
        booking_number = Booking.generate_booking_number()
        self.assertRegex(booking_number, r'BK-\d{8}-\d{4}')

    def test_room_availability(self):
        # Test availability calculation
        pass

    def test_booking_creation(self):
        # Test full booking workflow
        pass

    def test_booking_validation(self):
        # Test date validation
        pass
```

---

#### 8. **Integration Tests**
```python
class BookingWorkflowTestCase(TestCase):
    def test_complete_booking_wizard(self):
        # Test entire 3-step process
        # Step 1: Initial form
        response = self.client.post('/logus/booking/start/', {
            'patient': self.patient.id,
            'date_range': '20.12.2024 - 25.12.2024',
            'guests_count': 2
        })
        self.assertEqual(response.status_code, 302)

        # Step 2: Room selection
        # Step 3: Confirmation
        # Assert booking created
```

---

#### 9. **Load Testing**
```python
# Using locust
from locust import HttpUser, task, between

class ReceptionUser(HttpUser):
    wait_time = between(1, 5)

    @task
    def view_booking_list(self):
        self.client.get("/logus/booking/list/")

    @task(3)
    def search_patients(self):
        self.client.get("/logus/patients/?search=test")

    @task
    def create_booking(self):
        # Simulate booking creation
        pass
```

---

### UI/UX Improvements

#### 10. **Inline Patient Creation**
**Current:** Redirect to separate page

**Better:** Modal popup for quick registration

```html
<!-- In booking_start.html -->
<select name="patient" id="id_patient">
    <option value="">---</option>
    {% for patient in patients %}
    <option value="{{ patient.id }}">{{ patient.full_name }}</option>
    {% endfor %}
</select>
<button type="button" class="btn btn-sm btn-primary" data-toggle="modal" data-target="#quickPatientModal">
    + Новый пациент
</button>

<!-- Modal -->
<div class="modal" id="quickPatientModal">
    <form id="quickPatientForm">
        <!-- Patient fields -->
    </form>
</div>

<script>
$('#quickPatientForm').submit(function(e) {
    e.preventDefault();
    $.ajax({
        url: '{% url "logus:patient_quick_create" %}',
        method: 'POST',
        data: $(this).serialize(),
        success: function(data) {
            // Add to dropdown
            $('#id_patient').append(
                $('<option>').val(data.patient_id).text(data.patient_name)
            ).val(data.patient_id);
            $('#quickPatientModal').modal('hide');
        }
    });
});
</script>
```

---

#### 11. **Breadcrumb Navigation**
```html
<!-- In base template -->
<ol class="breadcrumb">
    <li class="breadcrumb-item"><a href="{% url 'logus:reception_dashboard' %}">Главная</a></li>
    {% block breadcrumb %}{% endblock %}
</ol>

<!-- In booking_start.html -->
{% block breadcrumb %}
<li class="breadcrumb-item"><a href="{% url 'logus:booking_list' %}">Бронирования</a></li>
<li class="breadcrumb-item active">Новое бронирование</li>
{% endblock %}
```

---

#### 12. **Keyboard Shortcuts**
```javascript
// Add keyboard shortcuts for common actions
document.addEventListener('keydown', function(e) {
    // Ctrl+N: New booking
    if (e.ctrlKey && e.key === 'n') {
        e.preventDefault();
        window.location = '{% url "logus:booking_start" %}';
    }

    // Ctrl+P: New patient
    if (e.ctrlKey && e.key === 'p') {
        e.preventDefault();
        window.location = '{% url "logus:patient_create_view" %}';
    }

    // Ctrl+F: Focus search
    if (e.ctrlKey && e.key === 'f') {
        e.preventDefault();
        document.querySelector('input[name="search"]').focus();
    }
});
```

---

#### 13. **Status Color Coding**
**Current:** Basic status display

**Enhance:**
```html
<!-- Consistent status badges -->
{% if booking.status == 'pending' %}
<span class="badge badge-warning">В ожидании</span>
{% elif booking.status == 'confirmed' %}
<span class="badge badge-info">Подтверждено</span>
{% elif booking.status == 'checked_in' %}
<span class="badge badge-success">Заселен</span>
{% elif booking.status == 'in_progress' %}
<span class="badge badge-primary">В процессе</span>
{% elif booking.status == 'completed' %}
<span class="badge badge-secondary">Завершено</span>
{% elif booking.status == 'cancelled' %}
<span class="badge badge-danger">Отменено</span>
{% endif %}

<!-- Color-coded rows -->
<tr class="booking-row booking-status-{{ booking.status }}">
    <!-- ... -->
</tr>

<style>
.booking-status-checked_in {
    background-color: #d4edda;
}
.booking-status-cancelled {
    background-color: #f8d7da;
    text-decoration: line-through;
}
</style>
```

---

#### 14. **Toast Notifications**
**Current:** Django messages

**Enhance:** Real-time toast notifications
```javascript
// Add toastr library
<link href="https://cdnjs.cloudflare.com/ajax/libs/toastr.js/latest/toastr.min.css" rel="stylesheet">
<script src="https://cdnjs.cloudflare.com/ajax/libs/toastr.js/latest/toastr.min.js"></script>

// In base template:
{% if messages %}
<script>
{% for message in messages %}
    toastr.{{ message.tags }}('{{ message }}');
{% endfor %}
</script>
{% endif %}
```

---

### Data Model Improvements

#### 15. **Gender Field Fix**
**Current:** `gender = BooleanField()`

**Change to:**
```python
class PatientModel(models.Model):
    GENDER_CHOICES = [
        ('M', 'Мужской'),
        ('F', 'Женский'),
        ('O', 'Другой'),
        ('U', 'Не указано'),
    ]
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
```

**Migration:**
```python
# Migration to convert boolean to char
def convert_gender(apps, schema_editor):
    PatientModel = apps.get_model('core', 'PatientModel')
    for patient in PatientModel.objects.all():
        patient.gender = 'M' if patient.gender else 'F'
        patient.save()
```

---

#### 16. **Add Booking Source Tracking**
```python
class Booking(models.Model):
    SOURCE_CHOICES = [
        ('walk_in', 'Прямое обращение'),
        ('phone', 'Телефон'),
        ('website', 'Веб-сайт'),
        ('mobile_app', 'Мобильное приложение'),
        ('partner', 'Партнер'),
        ('repeat', 'Повторное обращение'),
    ]
    source = models.CharField(
        max_length=20,
        choices=SOURCE_CHOICES,
        default='walk_in',
        verbose_name="Источник бронирования"
    )
    referral = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Реферал/Партнер"
    )
```

---

#### 17. **Add Cancellation Tracking**
```python
class Booking(models.Model):
    # Existing fields...

    cancelled_at = models.DateTimeField(null=True, blank=True)
    cancelled_by = models.ForeignKey(
        Account,
        null=True,
        blank=True,
        related_name='cancelled_bookings',
        on_delete=models.SET_NULL
    )
    cancellation_reason = models.TextField(blank=True)
    refund_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
```

---

## IMPLEMENTATION ROADMAP

### Priority 1: Critical Fixes (Week 1-2)

**Security:**
- [ ] Remove `@csrf_exempt` decorator
- [ ] Add rate limiting
- [ ] Audit all views for proper decorators
- [ ] Add input sanitization

**Data Integrity:**
- [ ] Implement duplicate patient detection
- [ ] Add phone number validation
- [ ] Enforce room capacity
- [ ] Add comprehensive form validation

**Code Quality:**
- [ ] Remove duplicate forms
- [ ] Remove duplicate views
- [ ] Consolidate patient registration flow
- [ ] Add error handling

**Estimated Time:** 40 hours

---

### Priority 2: Core Missing Features (Week 3-6)

**Booking Enhancements:**
- [ ] Mid-stay tariff/room change UI
- [ ] Service session management UI
- [ ] Enhanced check-in/check-out workflow
- [ ] Booking audit trail

**Patient Management:**
- [ ] Advanced patient search
- [ ] Patient access logging (compliance)
- [ ] Patient merge functionality

**Room Management:**
- [ ] Room maintenance scheduling
- [ ] Room capacity enforcement
- [ ] Maintenance status display

**Estimated Time:** 80 hours

---

### Priority 3: Operational Improvements (Week 7-10)

**Reservations:**
- [ ] Advance reservation system
- [ ] Deposit tracking
- [ ] Reservation expiration
- [ ] Waitlist management

**Reporting:**
- [ ] Occupancy reports
- [ ] Revenue reports
- [ ] Cancellation analysis
- [ ] Patient demographics

**Document Generation:**
- [ ] Booking confirmation PDF
- [ ] Welcome packet
- [ ] Check-out summary
- [ ] Treatment schedule

**Integration:**
- [ ] Quick payment in booking detail
- [ ] Service appointment scheduling
- [ ] Doctor assignment workflow

**Estimated Time:** 100 hours

---

### Priority 4: UX Enhancements (Week 11-12)

**UI Improvements:**
- [ ] Inline patient creation modal
- [ ] Breadcrumb navigation
- [ ] Keyboard shortcuts
- [ ] Toast notifications
- [ ] Calendar view

**Multi-Patient Booking:**
- [ ] Improved wizard workflow
- [ ] Per-room patient assignment
- [ ] Family/group booking handling

**Estimated Time:** 40 hours

---

### Priority 5: Performance & Scalability (Week 13-14)

**Database:**
- [ ] Add indexes
- [ ] Fix N+1 queries
- [ ] Optimize pagination

**Caching:**
- [ ] Cache room availability
- [ ] Cache dashboard stats
- [ ] Cache patient search

**Frontend:**
- [ ] Lazy loading
- [ ] Asset optimization
- [ ] Infinite scroll

**Estimated Time:** 30 hours

---

### Priority 6: Nice-to-Have (Week 15+)

**Notifications:**
- [ ] SMS notifications
- [ ] Email notifications
- [ ] Reminder system

**API:**
- [ ] REST API endpoints
- [ ] API documentation
- [ ] Authentication tokens

**Mobile:**
- [ ] Mobile-optimized UI
- [ ] Touch-friendly forms

**Multi-Language:**
- [ ] Full i18n implementation
- [ ] Language switcher
- [ ] Translate all strings

**Estimated Time:** 60 hours

---

## TOTAL EFFORT ESTIMATE

| Priority | Hours | Weeks |
|----------|-------|-------|
| P1: Critical Fixes | 40 | 2 |
| P2: Core Features | 80 | 4 |
| P3: Operational | 100 | 4 |
| P4: UX Enhancements | 40 | 2 |
| P5: Performance | 30 | 2 |
| P6: Nice-to-Have | 60 | 3+ |
| **TOTAL** | **350** | **17** |

---

## CONCLUSION

The Hayat Medical CRM Reception Module is a **solid foundation** with comprehensive core functionality. The booking wizard, patient management, and room availability system work well.

**Key Strengths:**
- Well-designed 3-step booking wizard
- Comprehensive data models
- Good separation of concerns
- Flexible tariff system
- Integration with medical records

**Critical Gaps:**
- Security vulnerabilities (CSRF exempt)
- Duplicate code and forms
- Missing UI for existing features (tariff changes, service tracking)
- No advance reservation system
- Limited search and reporting

**Recommendation:**
Focus on **Priority 1** (critical fixes) immediately, then implement **Priority 2** (core features) to complete the existing functionality before adding new features.

The module has excellent potential and with the recommended improvements will provide a robust, user-friendly reception management system.

---

**END OF ANALYSIS**
