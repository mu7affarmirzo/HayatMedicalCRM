# Implementation Prompts for Critical Missing Features

**Project:** Hayat Medical CRM - Cashbox Module
**Date:** December 7, 2025
**Priority:** CRITICAL

---

## 🔴 PROMPT 1: Implement Medication Billing Calculation

### Context
The cashbox billing system currently returns 0 for all medication costs. Patients receive medications during their stay but are not billed for them, resulting in significant revenue loss.

**Current State:**
- Location: `core/billing/calculator.py` lines 194-197
- Status: TODO comment with placeholder code
- Impact: ~100,000 UZS per patient revenue loss

**Expected Behavior:**
Calculate total medication costs by querying MedicationSession records, multiplying quantity by unit_price, and summing the results.

### Task Requirements

#### 1. Implementation Location
File: `/Users/muzaffarmirzo/devProjects/HayatMedicalCRM/core/billing/calculator.py`

Function: `calculate_booking_billing(booking, include_medications=True, include_lab_research=True)`

Lines to replace: 194-197

#### 2. Data Model Understanding

**MedicationSession Model:**
- Location: `core/models/sanatorium/prescriptions/medication_session.py`
- Relationship: `prescribed_medication` → `PrescribedMedication`
- Key fields:
  - `quantity` (IntegerField) - number of medication units given
  - `prescribed_medication.medication` (FK to MedicationModel)
  - `prescribed_medication.illness_history.booking` (FK chain to Booking)

**MedicationModel:**
- Key field: `unit_price` (BigIntegerField) - price per unit
- May be null or 0, needs handling

**Query Path:**
```
Booking
  → IllnessHistory (via booking FK)
    → PrescribedMedication (via illness_history FK)
      → MedicationSession (via prescribed_medication FK)
        → medication.unit_price
```

#### 3. Implementation Requirements

**Must Handle:**
- ✅ Null unit prices (treat as 0)
- ✅ Zero quantities (skip)
- ✅ Multiple illness histories per booking (multiple patients)
- ✅ Multiple medications per patient
- ✅ Multiple sessions per prescribed medication
- ✅ Database query optimization (use select_related)

**Business Rules:**
- Only count administered medications (MedicationSession exists)
- Cost = quantity × unit_price for each session
- Sum all medication costs across all patients in booking
- Return integer (UZS currency, no decimals)

#### 4. Detailed Implementation

```python
# REPLACE THIS CODE (lines 194-197):
if include_medications:
    # TODO: Implement medication billing calculation
    # This would query prescribed medications and sum their costs
    breakdown.medications_amount = 0

# WITH THIS IMPLEMENTATION:
if include_medications:
    try:
        # Query all medication sessions for this booking
        medications = MedicationSession.objects.filter(
            prescribed_medication__illness_history__booking=booking
        ).select_related(
            'prescribed_medication__medication'
        )

        # Calculate total cost
        total = 0
        for med_session in medications:
            # Get unit price, default to 0 if None
            medication = med_session.prescribed_medication.medication
            unit_price = getattr(medication, 'unit_price', 0) or 0

            # Calculate session cost
            session_cost = med_session.quantity * unit_price
            total += session_cost

        breakdown.medications_amount = int(total)

    except Exception as e:
        # Log error but don't break billing calculation
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error calculating medication billing for booking {booking.id}: {e}")
        breakdown.medications_amount = 0
```

#### 5. Validation Steps

**After Implementation:**

1. **Unit Test:**
```python
def test_medication_billing_calculation(self):
    """Test medication costs are correctly calculated"""
    # Create booking with patient
    booking = create_test_booking()

    # Create illness history
    illness_history = IllnessHistory.objects.create(
        booking=booking,
        patient=self.patient1
    )

    # Prescribe medication with known price
    medication = MedicationModel.objects.create(
        name='Test Med',
        unit_price=5000  # 5,000 UZS per unit
    )

    prescribed = PrescribedMedication.objects.create(
        illness_history=illness_history,
        medication=medication
    )

    # Create medication session: 10 units × 5,000 = 50,000
    MedicationSession.objects.create(
        prescribed_medication=prescribed,
        quantity=10
    )

    # Calculate billing
    breakdown = calculate_booking_billing(booking)

    # Assert
    self.assertEqual(breakdown.medications_amount, 50000)
```

2. **Integration Test:**
   - Create real booking in test database
   - Add medication sessions
   - Verify billing detail view shows correct amount

3. **Manual Verification:**
   - Check billing_detail view displays medications_amount
   - Verify grand total includes medications
   - Test with null/zero prices

#### 6. Edge Cases to Handle

| Case | Expected Behavior | Implementation |
|------|------------------|----------------|
| No medications | Return 0 | Empty queryset = 0 |
| Null unit_price | Treat as 0 | `or 0` in calculation |
| Zero quantity | Session cost = 0 | Multiplied by 0 |
| Multiple patients | Sum all | Loop through all sessions |
| Negative price | Use absolute? | Decide on business rule |

#### 7. Performance Considerations

**Query Optimization:**
- Use `select_related()` for FK lookups
- Single query for all sessions
- Avoid N+1 queries

**Before:**
```python
# BAD - N+1 queries
for session in sessions:
    price = session.prescribed_medication.medication.unit_price  # DB query each time
```

**After:**
```python
# GOOD - Single query with joins
sessions = MedicationSession.objects.filter(...).select_related(
    'prescribed_medication__medication'
)
for session in sessions:
    price = session.prescribed_medication.medication.unit_price  # No DB query
```

#### 8. Acceptance Criteria

- [ ] Medication billing calculates correct total
- [ ] Handles null/zero prices gracefully
- [ ] Works with multiple patients per booking
- [ ] Optimized queries (1-2 queries max)
- [ ] Error handling doesn't break billing
- [ ] Unit tests pass
- [ ] Integration test passes
- [ ] Code reviewed
- [ ] Deployed to staging
- [ ] Verified in production

---

## 🔴 PROMPT 2: Implement Lab Research Billing Calculation

### Context
The cashbox billing system currently returns 0 for all laboratory test costs. Lab tests are performed and recorded but patients are not charged, resulting in revenue loss.

**Current State:**
- Location: `core/billing/calculator.py` lines 200-203
- Status: TODO comment with placeholder code
- Impact: ~100,000 UZS per patient revenue loss

**Expected Behavior:**
Calculate total lab costs by querying AssignedLabs records, extracting the lab research price, and summing the results.

### Task Requirements

#### 1. Implementation Location
File: `/Users/muzaffarmirzo/devProjects/HayatMedicalCRM/core/billing/calculator.py`

Function: `calculate_booking_billing(booking, include_medications=True, include_lab_research=True)`

Lines to replace: 200-203

#### 2. Data Model Understanding

**AssignedLabs Model:**
- Location: `core/models/sanatorium/prescriptions/assigned_labs.py`
- Key fields:
  - `illness_history` (FK to IllnessHistory)
  - `lab` (FK to LabResearchModel)
  - `state` (CharField) - lab status

**LabResearchModel:**
- Key field: `price` (IntegerField) - cost of lab test
- May be null, needs handling

**Query Path:**
```
Booking
  → IllnessHistory (via booking FK)
    → AssignedLabs (via illness_history FK)
      → lab.price
```

#### 3. Implementation Requirements

**Must Handle:**
- ✅ Null lab prices (treat as 0)
- ✅ Multiple illness histories per booking (multiple patients)
- ✅ Multiple lab tests per patient
- ✅ Lab test states (only bill completed/dispatched?)
- ✅ Database query optimization (use select_related)

**Business Rules to Clarify:**
- ❓ Bill all assigned labs or only completed ones?
- ❓ Different prices for different lab states?
- ❓ Cancelled labs should be excluded?

**Recommended Business Rules:**
- Only bill labs with state in: `['dispatched', 'results']`
- Exclude: `['recommended', 'assigned', 'cancelled', 'stopped']`
- This ensures only performed labs are billed

#### 4. Detailed Implementation

```python
# REPLACE THIS CODE (lines 200-203):
if include_lab_research:
    # TODO: Implement lab research billing calculation
    # This would query lab orders and sum their costs
    breakdown.lab_research_amount = 0

# WITH THIS IMPLEMENTATION:
if include_lab_research:
    try:
        # Define billable lab states
        BILLABLE_LAB_STATES = ['dispatched', 'results']

        # Query all assigned labs for this booking
        assigned_labs = AssignedLabs.objects.filter(
            illness_history__booking=booking,
            state__in=BILLABLE_LAB_STATES  # Only bill performed labs
        ).select_related('lab')

        # Calculate total cost
        total = 0
        for assigned_lab in assigned_labs:
            # Get lab price, default to 0 if None
            if assigned_lab.lab:
                lab_price = getattr(assigned_lab.lab, 'price', 0) or 0
                total += lab_price

        breakdown.lab_research_amount = int(total)

    except Exception as e:
        # Log error but don't break billing calculation
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error calculating lab billing for booking {booking.id}: {e}")
        breakdown.lab_research_amount = 0
```

#### 5. Alternative Implementation (Bill All Labs)

If business requires billing ALL assigned labs regardless of state:

```python
if include_lab_research:
    try:
        # Query all assigned labs for this booking (no state filter)
        assigned_labs = AssignedLabs.objects.filter(
            illness_history__booking=booking
        ).select_related('lab')

        # Calculate total cost
        total = sum(
            getattr(assigned_lab.lab, 'price', 0) or 0
            for assigned_lab in assigned_labs
            if assigned_lab.lab  # Ensure lab FK is not null
        )

        breakdown.lab_research_amount = int(total)

    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error calculating lab billing for booking {booking.id}: {e}")
        breakdown.lab_research_amount = 0
```

#### 6. Validation Steps

**After Implementation:**

1. **Unit Test:**
```python
def test_lab_billing_calculation(self):
    """Test lab costs are correctly calculated"""
    # Create booking with patient
    booking = create_test_booking()

    # Create illness history
    illness_history = IllnessHistory.objects.create(
        booking=booking,
        patient=self.patient1
    )

    # Create lab research with known price
    lab1 = LabResearchModel.objects.create(
        name='Blood Test',
        price=30000  # 30,000 UZS
    )

    lab2 = LabResearchModel.objects.create(
        name='X-Ray',
        price=50000  # 50,000 UZS
    )

    # Assign labs
    AssignedLabs.objects.create(
        illness_history=illness_history,
        lab=lab1,
        state='dispatched'
    )

    AssignedLabs.objects.create(
        illness_history=illness_history,
        lab=lab2,
        state='results'
    )

    # Calculate billing
    breakdown = calculate_booking_billing(booking)

    # Assert: 30,000 + 50,000 = 80,000
    self.assertEqual(breakdown.lab_research_amount, 80000)
```

2. **Test Lab States:**
```python
def test_lab_billing_only_billable_states(self):
    """Test only performed labs are billed"""
    # ... setup ...

    # Create labs with different states
    AssignedLabs.objects.create(
        illness_history=illness_history,
        lab=lab1,
        state='cancelled'  # Should NOT be billed
    )

    AssignedLabs.objects.create(
        illness_history=illness_history,
        lab=lab2,
        state='dispatched'  # Should be billed
    )

    breakdown = calculate_booking_billing(booking)

    # Only lab2 should be billed
    self.assertEqual(breakdown.lab_research_amount, lab2.price)
```

#### 7. Edge Cases to Handle

| Case | Expected Behavior | Implementation |
|------|------------------|----------------|
| No labs assigned | Return 0 | Empty queryset = 0 |
| Null lab price | Treat as 0 | `or 0` in calculation |
| Cancelled labs | Exclude | Filter by state |
| Null lab FK | Skip | Check `if assigned_lab.lab` |
| Multiple patients | Sum all | Loop through all labs |

#### 8. Business Rule Decision Required

**IMPORTANT:** Before implementing, confirm with stakeholders:

**Question:** Which lab states should be billed?

**Option A (Recommended):** Bill only performed labs
```python
BILLABLE_LAB_STATES = ['dispatched', 'results']
```
- ✅ Fair to patient (only pay for performed tests)
- ✅ Matches medical billing standards
- ❌ May miss cancelled-but-started labs

**Option B:** Bill all assigned labs
```python
# No state filter
```
- ✅ Simple logic
- ❌ Patient charged for cancelled tests
- ❌ May cause disputes

**Option C:** Custom business rule
```python
# Bill all except explicitly cancelled
BILLABLE_LAB_STATES = ['recommended', 'assigned', 'dispatched', 'results']
```

**Recommendation:** Use Option A (only dispatched/results)

#### 9. Integration with Views

The view `billing_detail` in `application/cashbox/views/billing.py` already queries labs:

```python
# Line 162-164
lab_tests = AssignedLabs.objects.filter(
    illness_history__booking=booking
)
```

**Action Required:** Update view to show which labs are billable

```python
# Enhanced query
lab_tests = AssignedLabs.objects.filter(
    illness_history__booking=booking
).select_related('lab')

# Add computed field in template context
for lab in lab_tests:
    lab.is_billable = lab.state in ['dispatched', 'results']
    lab.cost = getattr(lab.lab, 'price', 0) if lab.is_billable else 0
```

#### 10. Acceptance Criteria

- [ ] Lab billing calculates correct total
- [ ] Only bills labs in correct states (if applicable)
- [ ] Handles null prices gracefully
- [ ] Works with multiple patients per booking
- [ ] Optimized queries (1-2 queries max)
- [ ] Error handling doesn't break billing
- [ ] Unit tests pass (all states tested)
- [ ] Business rules documented
- [ ] Code reviewed
- [ ] Deployed to staging
- [ ] Verified in production

---

## 🔴 PROMPT 3: Implement Payment Processing Backend

### Context
The cashbox billing system can calculate what patients owe but has NO WAY to record that money was received. The UI has an "Accept Payment" button that does nothing. This is the most critical gap - without payment processing, the entire billing system is unusable for its primary purpose: collecting money.

**Current State:**
- Location: No backend implementation exists
- UI: Button in `billing_detail.html` (non-functional)
- Status: Complete gap in functionality
- Impact: CRITICAL - Cannot collect any payments

**Expected Behavior:**
Complete payment acceptance workflow including validation, transaction recording, status updates, and receipt generation.

### Task Requirements

#### 1. New Files to Create

```
application/cashbox/views/payment.py          # Payment views
application/cashbox/forms/payment_forms.py    # Payment forms
application/cashbox/urls/payment_urls.py      # Payment URLs (optional)
core/models/transactions.py                   # Update TransactionsModel
application/templates/cashbox/payment/        # Payment templates
    payment_modal.html                        # Payment form modal
    receipt.html                              # Receipt template
```

#### 2. Database Model Updates

**Extend BookingBilling Model:**

File: `core/models/booking.py`

Add new status to BillingStatus choices:

```python
class BookingBilling(BaseAuditModel):
    class BillingStatus(models.TextChoices):
        PENDING = 'pending', 'Pending'
        CALCULATED = 'calculated', 'Calculated'
        INVOICED = 'invoiced', 'Invoiced'
        PAID = 'paid', 'Paid'  # NEW STATUS
        PARTIALLY_PAID = 'partially_paid', 'Partially Paid'  # NEW STATUS
```

**Verify TransactionsModel:**

File: `core/models/transactions.py`

Ensure model has these fields:

```python
class TransactionsModel(BaseAuditModel):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE)
    patient = models.ForeignKey(PatientModel, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=12, decimal_places=2)

    transaction_type = models.CharField(
        max_length=20,
        choices=[
            ('CASH', 'Наличные'),
            ('CARD', 'Карта'),
            ('PAYME', 'PayMe'),
            ('CLICK', 'Click'),
            ('TRANSFER', 'Перевод'),
            ('HUMO', 'Humo'),
            ('UZCARD', 'UzCard'),
        ]
    )

    # NEW FIELDS NEEDED:
    billing = models.ForeignKey(
        'BookingBilling',
        on_delete=models.CASCADE,
        related_name='transactions',
        null=True,
        blank=True
    )

    reference_number = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="External transaction reference (card, PayMe, etc.)"
    )

    notes = models.TextField(blank=True, null=True)

    status = models.CharField(
        max_length=20,
        choices=[
            ('PENDING', 'В обработке'),
            ('COMPLETED', 'Завершено'),
            ('FAILED', 'Ошибка'),
            ('REFUNDED', 'Возвращено'),
        ],
        default='COMPLETED'
    )
```

#### 3. Create Payment Form

**File:** `application/cashbox/forms/payment_forms.py`

```python
from django import forms
from decimal import Decimal
from core.models import TransactionsModel, BookingBilling


class PaymentAcceptanceForm(forms.Form):
    """Form for accepting payment for a booking"""

    PAYMENT_METHOD_CHOICES = [
        ('CASH', 'Наличные (Cash)'),
        ('CARD', 'Банковская карта (Card)'),
        ('UZCARD', 'UzCard'),
        ('HUMO', 'Humo'),
        ('PAYME', 'PayMe'),
        ('CLICK', 'Click'),
        ('TRANSFER', 'Банковский перевод (Transfer)'),
    ]

    amount = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        label='Сумма оплаты',
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите сумму',
            'step': '0.01',
            'min': '0'
        })
    )

    payment_method = forms.ChoiceField(
        choices=PAYMENT_METHOD_CHOICES,
        label='Способ оплаты',
        widget=forms.Select(attrs={
            'class': 'form-control select2'
        })
    )

    reference_number = forms.CharField(
        max_length=100,
        required=False,
        label='Номер транзакции (необязательно)',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Номер чека, карты и т.д.'
        }),
        help_text='Для карт/онлайн платежей укажите номер транзакции'
    )

    notes = forms.CharField(
        required=False,
        label='Примечания',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Дополнительная информация'
        })
    )

    def __init__(self, *args, billing=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.billing = billing

        if billing:
            # Pre-fill amount with remaining balance
            remaining = self.calculate_remaining_balance(billing)
            self.fields['amount'].initial = remaining
            self.fields['amount'].widget.attrs['max'] = str(remaining)

    def calculate_remaining_balance(self, billing):
        """Calculate how much is still owed"""
        total_paid = billing.transactions.filter(
            status='COMPLETED'
        ).aggregate(
            total=models.Sum('amount')
        )['total'] or Decimal('0')

        remaining = billing.total_amount - total_paid
        return max(remaining, Decimal('0'))

    def clean_amount(self):
        """Validate payment amount"""
        amount = self.cleaned_data.get('amount')

        if amount <= 0:
            raise forms.ValidationError('Сумма должна быть больше нуля')

        if self.billing:
            remaining = self.calculate_remaining_balance(self.billing)
            if amount > remaining:
                raise forms.ValidationError(
                    f'Сумма превышает остаток: {remaining:,.2f} сум'
                )

        return amount

    def clean(self):
        """Validate form data"""
        cleaned_data = super().clean()
        payment_method = cleaned_data.get('payment_method')
        reference_number = cleaned_data.get('reference_number')

        # Require reference number for non-cash payments
        if payment_method in ['CARD', 'PAYME', 'CLICK', 'UZCARD', 'HUMO']:
            if not reference_number:
                self.add_error(
                    'reference_number',
                    'Номер транзакции обязателен для безналичных платежей'
                )

        return cleaned_data
```

#### 4. Create Payment View

**File:** `application/cashbox/views/payment.py`

```python
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.db import transaction
from django.urls import reverse
from decimal import Decimal

from HayatMedicalCRM.auth.decorators import cashbox_required
from core.models import Booking, BookingBilling, TransactionsModel
from application.cashbox.forms.payment_forms import PaymentAcceptanceForm


@cashbox_required
@require_POST
def accept_payment(request, booking_id):
    """
    Accept payment for a booking

    POST parameters:
        - amount: Decimal amount being paid
        - payment_method: Payment method code
        - reference_number: External transaction reference (optional)
        - notes: Payment notes (optional)
    """
    booking = get_object_or_404(Booking, id=booking_id)
    billing = get_object_or_404(
        BookingBilling,
        booking=booking
    )

    # Validate billing status
    if billing.billing_status not in ['calculated', 'invoiced', 'partially_paid']:
        messages.error(
            request,
            'Невозможно принять оплату. Счет должен быть рассчитан.'
        )
        return redirect('cashbox:billing_detail', booking_id=booking.id)

    # Process form
    form = PaymentAcceptanceForm(request.POST, billing=billing)

    if form.is_valid():
        try:
            with transaction.atomic():
                # Create transaction record
                payment = TransactionsModel.objects.create(
                    booking=booking,
                    billing=billing,
                    patient=booking.details.first().client,  # Primary patient
                    amount=form.cleaned_data['amount'],
                    transaction_type=form.cleaned_data['payment_method'],
                    reference_number=form.cleaned_data.get('reference_number', ''),
                    notes=form.cleaned_data.get('notes', ''),
                    status='COMPLETED',
                    created_by=request.user,
                    modified_by=request.user
                )

                # Update billing status
                total_paid = billing.transactions.filter(
                    status='COMPLETED'
                ).aggregate(
                    total=models.Sum('amount')
                )['total'] or Decimal('0')

                if total_paid >= billing.total_amount:
                    billing.billing_status = 'paid'
                elif total_paid > 0:
                    billing.billing_status = 'partially_paid'

                billing.modified_by = request.user
                billing.save()

                messages.success(
                    request,
                    f'Оплата {form.cleaned_data["amount"]:,.2f} сум принята успешно. '
                    f'Способ: {form.cleaned_data["payment_method"]}'
                )

                # Return JSON for AJAX requests
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': True,
                        'transaction_id': payment.id,
                        'amount': float(payment.amount),
                        'billing_status': billing.billing_status,
                        'message': 'Оплата принята успешно'
                    })

                # Redirect to receipt or billing detail
                return redirect('cashbox:billing_detail', booking_id=booking.id)

        except Exception as e:
            messages.error(
                request,
                f'Ошибка при обработке оплаты: {str(e)}'
            )

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': str(e)
                }, status=500)

    else:
        # Form validation failed
        error_messages = []
        for field, errors in form.errors.items():
            for error in errors:
                error_messages.append(f"{field}: {error}")

        messages.error(request, 'Ошибка валидации: ' + '; '.join(error_messages))

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'errors': form.errors
            }, status=400)

    return redirect('cashbox:billing_detail', booking_id=booking.id)


@cashbox_required
def payment_receipt(request, transaction_id):
    """
    Display payment receipt
    """
    payment = get_object_or_404(
        TransactionsModel,
        id=transaction_id
    )

    context = {
        'payment': payment,
        'booking': payment.booking,
        'billing': payment.billing,
        'patient': payment.patient,
    }

    return render(request, 'cashbox/payment/receipt.html', context)


@cashbox_required
def refund_payment(request, transaction_id):
    """
    Refund a payment (future feature)
    """
    # TODO: Implement refund logic
    messages.warning(request, 'Функция возврата в разработке')
    payment = get_object_or_404(TransactionsModel, id=transaction_id)
    return redirect('cashbox:billing_detail', booking_id=payment.booking.id)
```

#### 5. Update URL Configuration

**Option A:** Add to existing `application/cashbox/urls/billing.py`:

```python
from application.cashbox.views import payment

urlpatterns = [
    # ... existing patterns ...

    # Payment endpoints
    path('billing/<int:booking_id>/accept-payment/',
         payment.accept_payment,
         name='accept_payment'),

    path('payment/<int:transaction_id>/receipt/',
         payment.payment_receipt,
         name='payment_receipt'),

    path('payment/<int:transaction_id>/refund/',
         payment.refund_payment,
         name='refund_payment'),
]
```

**Option B:** Create separate `application/cashbox/urls/payment_urls.py`:

```python
from django.urls import path
from application.cashbox.views import payment

urlpatterns = [
    path('accept/<int:booking_id>/', payment.accept_payment, name='accept_payment'),
    path('receipt/<int:transaction_id>/', payment.payment_receipt, name='payment_receipt'),
    path('refund/<int:transaction_id>/', payment.refund_payment, name='refund_payment'),
]
```

Then include in `application/cashbox/router.py`:

```python
urlpatterns = [
    path('', include('application.cashbox.urls.billing')),
    path('payment/', include('application.cashbox.urls.payment_urls')),
]
```

#### 6. Update Billing Detail Template

**File:** `application/templates/cashbox/billing/billing_detail.html`

Add payment modal and update action buttons:

```html
<!-- Add after line 240 (end of billing breakdown section) -->

<!-- Payment Modal -->
{% if billing.billing_status in 'calculated,invoiced,partially_paid' %}
<div class="modal fade" id="paymentModal" tabindex="-1" role="dialog">
    <div class="modal-dialog" role="document">
        <div class="modal-content">
            <div class="modal-header bg-success">
                <h5 class="modal-title text-white">
                    <i class="fas fa-money-bill-wave"></i> Принять оплату
                </h5>
                <button type="button" class="close text-white" data-dismiss="modal">
                    <span>&times;</span>
                </button>
            </div>

            <form id="paymentForm" method="POST"
                  action="{% url 'cashbox:accept_payment' booking.id %}">
                {% csrf_token %}

                <div class="modal-body">
                    <!-- Billing Summary -->
                    <div class="alert alert-info">
                        <h6 class="mb-2"><strong>Сводка счета:</strong></h6>
                        <div class="d-flex justify-content-between">
                            <span>Итого к оплате:</span>
                            <strong>{{ billing.total_amount|intcomma }} сум</strong>
                        </div>
                        {% if billing.billing_status == 'partially_paid' %}
                        <div class="d-flex justify-content-between text-success">
                            <span>Уже оплачено:</span>
                            <strong id="totalPaid">{{ total_paid|intcomma }} сум</strong>
                        </div>
                        <hr class="my-2">
                        <div class="d-flex justify-content-between">
                            <span>Остаток:</span>
                            <strong id="remaining">{{ remaining|intcomma }} сум</strong>
                        </div>
                        {% endif %}
                    </div>

                    <!-- Payment Amount -->
                    <div class="form-group">
                        <label for="payment_amount">
                            Сумма оплаты <span class="text-danger">*</span>
                        </label>
                        <input type="number"
                               class="form-control"
                               id="payment_amount"
                               name="amount"
                               value="{{ remaining|default:billing.total_amount }}"
                               min="0"
                               step="0.01"
                               max="{{ remaining|default:billing.total_amount }}"
                               required>
                    </div>

                    <!-- Payment Method -->
                    <div class="form-group">
                        <label for="payment_method">
                            Способ оплаты <span class="text-danger">*</span>
                        </label>
                        <select class="form-control select2"
                                id="payment_method"
                                name="payment_method"
                                required>
                            <option value="">Выберите способ...</option>
                            <option value="CASH">💵 Наличные (Cash)</option>
                            <option value="CARD">💳 Банковская карта (Card)</option>
                            <option value="UZCARD">💳 UzCard</option>
                            <option value="HUMO">💳 Humo</option>
                            <option value="PAYME">📱 PayMe</option>
                            <option value="CLICK">📱 Click</option>
                            <option value="TRANSFER">🏦 Банковский перевод</option>
                        </select>
                    </div>

                    <!-- Reference Number -->
                    <div class="form-group" id="referenceGroup" style="display:none;">
                        <label for="reference_number">
                            Номер транзакции <span class="text-danger">*</span>
                        </label>
                        <input type="text"
                               class="form-control"
                               id="reference_number"
                               name="reference_number"
                               placeholder="Номер чека, карты и т.д.">
                        <small class="form-text text-muted">
                            Обязательно для безналичных платежей
                        </small>
                    </div>

                    <!-- Notes -->
                    <div class="form-group">
                        <label for="payment_notes">Примечания</label>
                        <textarea class="form-control"
                                  id="payment_notes"
                                  name="notes"
                                  rows="2"
                                  placeholder="Дополнительная информация (необязательно)"></textarea>
                    </div>
                </div>

                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-dismiss="modal">
                        Отмена
                    </button>
                    <button type="submit" class="btn btn-success">
                        <i class="fas fa-check"></i> Принять оплату
                    </button>
                </div>
            </form>
        </div>
    </div>
</div>
{% endif %}

<!-- Add payment history section before existing services -->
{% if billing.transactions.exists %}
<div class="card mt-3">
    <div class="card-header">
        <h3 class="card-title">
            <i class="fas fa-receipt"></i> История платежей
        </h3>
    </div>
    <div class="card-body p-0">
        <table class="table table-sm table-hover mb-0">
            <thead>
                <tr>
                    <th>Дата</th>
                    <th>Сумма</th>
                    <th>Способ</th>
                    <th>Номер</th>
                    <th>Статус</th>
                    <th>Кассир</th>
                    <th>Действия</th>
                </tr>
            </thead>
            <tbody>
                {% for payment in billing.transactions.all %}
                <tr>
                    <td>{{ payment.created_at|date:"d.m.Y H:i" }}</td>
                    <td><strong>{{ payment.amount|intcomma }} сум</strong></td>
                    <td>{{ payment.get_transaction_type_display }}</td>
                    <td>{{ payment.reference_number|default:"-" }}</td>
                    <td>
                        <span class="badge badge-success">
                            {{ payment.get_status_display }}
                        </span>
                    </td>
                    <td>{{ payment.created_by.full_name }}</td>
                    <td>
                        <a href="{% url 'cashbox:payment_receipt' payment.id %}"
                           class="btn btn-xs btn-info"
                           target="_blank">
                            <i class="fas fa-receipt"></i> Чек
                        </a>
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
</div>
{% endif %}
```

Update the action buttons section (around line 187):

```html
{% if 'calculate_billing' in available_actions %}
<button type="submit" name="action" value="calculate_billing"
        class="btn btn-primary">
    <i class="fas fa-calculator"></i> Рассчитать счет
</button>
{% endif %}

{% if 'mark_invoiced' in available_actions %}
<button type="submit" name="action" value="mark_invoiced"
        class="btn btn-info">
    <i class="fas fa-file-invoice"></i> Выставить счет
</button>
{% endif %}

<!-- NEW: Accept Payment Button -->
{% if billing.billing_status in 'calculated,invoiced,partially_paid' %}
<button type="button" class="btn btn-success" data-toggle="modal" data-target="#paymentModal">
    <i class="fas fa-money-bill-wave"></i> Принять оплату
</button>
{% endif %}

<!-- Show payment status if paid -->
{% if billing.billing_status == 'paid' %}
<div class="alert alert-success mt-3">
    <i class="fas fa-check-circle"></i>
    <strong>Оплачено полностью</strong>
</div>
{% elif billing.billing_status == 'partially_paid' %}
<div class="alert alert-warning mt-3">
    <i class="fas fa-exclamation-circle"></i>
    <strong>Частично оплачено:</strong> {{ total_paid|intcomma }} из {{ billing.total_amount|intcomma }} сум
</div>
{% endif %}
```

Add JavaScript at the end of the template:

```html
{% block extra_js %}
{{ block.super }}
<script>
$(document).ready(function() {
    // Show/hide reference number based on payment method
    $('#payment_method').on('change', function() {
        var method = $(this).val();
        var nonCashMethods = ['CARD', 'UZCARD', 'HUMO', 'PAYME', 'CLICK', 'TRANSFER'];

        if (nonCashMethods.includes(method)) {
            $('#referenceGroup').show();
            $('#reference_number').prop('required', true);
        } else {
            $('#referenceGroup').hide();
            $('#reference_number').prop('required', false);
        }
    });

    // Form submission with AJAX (optional)
    $('#paymentForm').on('submit', function(e) {
        // Optional: Implement AJAX submission for better UX
        // For now, let it submit normally
    });
});
</script>
{% endblock %}
```

#### 7. Create Receipt Template

**File:** `application/templates/cashbox/payment/receipt.html`

```html
{% extends 'cashbox/snippets/base.html' %}
{% load static %}
{% load humanize %}

{% block title %}Чек оплаты - {{ payment.booking.booking_number }}{% endblock %}

{% block extra_css %}
<style>
    @media print {
        .no-print { display: none; }
        .receipt-container {
            width: 80mm;
            font-size: 12px;
        }
    }

    .receipt-container {
        max-width: 400px;
        margin: 20px auto;
        padding: 20px;
        border: 1px solid #ddd;
        font-family: 'Courier New', monospace;
    }

    .receipt-header {
        text-align: center;
        border-bottom: 2px dashed #000;
        padding-bottom: 10px;
        margin-bottom: 10px;
    }

    .receipt-line {
        display: flex;
        justify-content: space-between;
        margin: 5px 0;
    }

    .receipt-total {
        border-top: 2px dashed #000;
        margin-top: 10px;
        padding-top: 10px;
        font-weight: bold;
        font-size: 1.2em;
    }
</style>
{% endblock %}

{% block content %}
<div class="content-header no-print">
    <div class="container-fluid">
        <div class="row mb-2">
            <div class="col-sm-6">
                <h1 class="m-0">Чек оплаты</h1>
            </div>
            <div class="col-sm-6">
                <button onclick="window.print()" class="btn btn-primary float-right">
                    <i class="fas fa-print"></i> Печать
                </button>
            </div>
        </div>
    </div>
</div>

<section class="content">
    <div class="receipt-container">
        <!-- Header -->
        <div class="receipt-header">
            <h3>HAYAT MEDICAL CENTER</h3>
            <p class="mb-1">Чек оплаты</p>
            <p class="mb-0">№ {{ payment.id }}</p>
        </div>

        <!-- Details -->
        <div class="receipt-body">
            <div class="receipt-line">
                <span>Дата:</span>
                <span>{{ payment.created_at|date:"d.m.Y H:i" }}</span>
            </div>

            <div class="receipt-line">
                <span>Бронирование:</span>
                <span>{{ payment.booking.booking_number }}</span>
            </div>

            <div class="receipt-line">
                <span>Пациент:</span>
                <span>{{ payment.patient.full_name }}</span>
            </div>

            <div class="receipt-line">
                <span>Способ оплаты:</span>
                <span>{{ payment.get_transaction_type_display }}</span>
            </div>

            {% if payment.reference_number %}
            <div class="receipt-line">
                <span>Номер транзакции:</span>
                <span>{{ payment.reference_number }}</span>
            </div>
            {% endif %}

            <!-- Total -->
            <div class="receipt-total">
                <div class="receipt-line">
                    <span>ОПЛАЧЕНО:</span>
                    <span>{{ payment.amount|intcomma }} сум</span>
                </div>
            </div>

            {% if billing %}
            <div class="mt-3 pt-3" style="border-top: 1px solid #ddd;">
                <div class="receipt-line">
                    <span>Итого счет:</span>
                    <span>{{ billing.total_amount|intcomma }} сум</span>
                </div>
                <div class="receipt-line">
                    <span>Статус:</span>
                    <span>{{ billing.get_billing_status_display }}</span>
                </div>
            </div>
            {% endif %}
        </div>

        <!-- Footer -->
        <div class="text-center mt-4 pt-3" style="border-top: 2px dashed #000;">
            <p class="mb-1">Кассир: {{ payment.created_by.full_name }}</p>
            <p class="mb-0">Спасибо за оплату!</p>
        </div>
    </div>
</section>
{% endblock %}
```

#### 8. Update Billing Detail View

**File:** `application/cashbox/views/billing.py`

Add payment-related context to `billing_detail` view:

```python
# Add after line 186 (billing_breakdown)
# Calculate payment totals
total_paid = billing.transactions.filter(
    status='COMPLETED'
).aggregate(
    total=models.Sum('amount')
)['total'] or 0

remaining = billing.total_amount - total_paid

# Update available_actions to include payment
available_actions = []
if billing.billing_status == 'pending':
    available_actions = ['calculate_billing']
elif billing.billing_status == 'calculated':
    available_actions = ['calculate_billing', 'mark_invoiced']
elif billing.billing_status in ['invoiced', 'partially_paid']:
    available_actions = ['calculate_billing', 'accept_payment']

# Add to context
context = {
    # ... existing context ...
    'total_paid': total_paid,
    'remaining': remaining,
}
```

#### 9. Migration for Model Changes

Create migration:

```bash
python manage.py makemigrations core --name add_payment_fields_to_transactions
```

Expected migration content:

```python
# Generated migration
operations = [
    migrations.AddField(
        model_name='transactionsmodel',
        name='billing',
        field=models.ForeignKey(
            blank=True,
            null=True,
            on_delete=django.db.models.deletion.CASCADE,
            related_name='transactions',
            to='core.bookingbilling'
        ),
    ),
    migrations.AddField(
        model_name='transactionsmodel',
        name='reference_number',
        field=models.CharField(
            blank=True,
            help_text='External transaction reference',
            max_length=100,
            null=True
        ),
    ),
    migrations.AddField(
        model_name='transactionsmodel',
        name='notes',
        field=models.TextField(blank=True, null=True),
    ),
    migrations.AddField(
        model_name='transactionsmodel',
        name='status',
        field=models.CharField(
            choices=[
                ('PENDING', 'В обработке'),
                ('COMPLETED', 'Завершено'),
                ('FAILED', 'Ошибка'),
                ('REFUNDED', 'Возвращено')
            ],
            default='COMPLETED',
            max_length=20
        ),
    ),
    migrations.AlterField(
        model_name='bookingbilling',
        name='billing_status',
        field=models.CharField(
            choices=[
                ('pending', 'Pending'),
                ('calculated', 'Calculated'),
                ('invoiced', 'Invoiced'),
                ('paid', 'Paid'),
                ('partially_paid', 'Partially Paid')
            ],
            default='pending',
            max_length=20
        ),
    ),
]
```

#### 10. Testing Checklist

**Unit Tests:**
- [ ] Test payment form validation
- [ ] Test payment amount validation (not exceeding total)
- [ ] Test reference number required for non-cash
- [ ] Test billing status updates (paid, partially_paid)
- [ ] Test transaction creation

**Integration Tests:**
- [ ] Test full payment workflow end-to-end
- [ ] Test partial payment workflow
- [ ] Test multiple payments for one booking
- [ ] Test receipt generation

**Manual Testing:**
- [ ] Accept cash payment
- [ ] Accept card payment (with reference)
- [ ] Accept partial payment
- [ ] Complete payment with multiple transactions
- [ ] Print receipt
- [ ] Verify transaction history display

**Edge Cases:**
- [ ] Payment amount = 0
- [ ] Payment exceeding remaining balance
- [ ] Concurrent payments (race condition)
- [ ] Missing billing record
- [ ] Invalid booking ID

#### 11. Security Considerations

**CRITICAL SECURITY CHECKS:**

1. **Authorization:**
   - ✅ Only cashbox role can accept payments
   - ✅ Check user permissions before processing

2. **Validation:**
   - ✅ Validate amount > 0
   - ✅ Validate amount <= remaining balance
   - ✅ Validate payment method is in allowed list
   - ✅ CSRF token required

3. **Atomic Transactions:**
   - ✅ Use `transaction.atomic()` for payment processing
   - ✅ Rollback on error

4. **Audit Trail:**
   - ✅ Record created_by and modified_by
   - ✅ Timestamp all transactions
   - ✅ Cannot delete/modify completed transactions

5. **Concurrent Access:**
   - Consider using `select_for_update()` for billing record
   - Prevent double-payment race conditions

**Enhanced security (optional):**

```python
@cashbox_required
@require_POST
def accept_payment(request, booking_id):
    # ... existing code ...

    with transaction.atomic():
        # Lock billing record to prevent concurrent modifications
        billing = BookingBilling.objects.select_for_update().get(
            booking__id=booking_id
        )

        # Validate amount again within transaction
        current_remaining = form.calculate_remaining_balance(billing)
        if form.cleaned_data['amount'] > current_remaining:
            raise ValueError("Amount exceeds remaining balance")

        # ... create payment ...
```

#### 12. Acceptance Criteria

**Phase 1: Basic Payment (Week 1)**
- [ ] Payment form created and validates
- [ ] Accept payment view processes payments
- [ ] Transaction records created correctly
- [ ] Billing status updates (paid/partially_paid)
- [ ] Payment history displays in billing detail
- [ ] Receipt template created and prints
- [ ] URLs configured correctly
- [ ] Permissions enforced
- [ ] All unit tests pass
- [ ] Manual testing complete

**Phase 2: Enhancements (Week 2-3)**
- [ ] AJAX form submission (no page reload)
- [ ] Real-time balance update in modal
- [ ] Payment confirmation dialog
- [ ] Email receipt to patient (optional)
- [ ] SMS notification (optional)
- [ ] Refund functionality (basic)

**Phase 3: Advanced (Future)**
- [ ] Multi-currency support
- [ ] Payment gateway integration
- [ ] Installment plans
- [ ] Auto-reconciliation with bank statements

---

## 📋 Implementation Order Recommendation

### Step 1: Medication Billing (2-4 hours)
Start here because it's the simplest - just a calculation in one function.

### Step 2: Lab Billing (2-4 hours)
Similar to medication, requires business rule decision.

### Step 3: Payment Processing (1-2 days)
Most complex, but unlocks the entire system's value.

---

## 🎯 Success Metrics

After implementing all three features:

**Before:**
- ❌ Medication billing: 0 UZS collected
- ❌ Lab billing: 0 UZS collected
- ❌ Payments: Cannot process

**After:**
- ✅ Medication billing: ~100,000 UZS per patient
- ✅ Lab billing: ~100,000 UZS per patient
- ✅ Payments: Full collection capability
- ✅ **Total revenue impact: +200,000 UZS per patient**

With 100 patients/month = **+20,000,000 UZS/month** (~$1,700 USD/month)

---

## 📞 Support & Questions

If you encounter issues during implementation:

1. Check diagnostic report: `CASHBOX_DIAGNOSTIC_REPORT.md`
2. Review test scenarios: `core/tests/test_cashbox_billing.py`
3. Run diagnostics: `python cashbox_diagnostics.py`
4. Check implementation progress: `IMPLEMENTATION_PROGRESS.md`

**Ready to implement? Copy these prompts and start coding!** 🚀
