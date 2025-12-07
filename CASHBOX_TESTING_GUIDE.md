# Cashbox Module - Testing Guide

**Date:** December 7, 2025
**Status:** Ready for Manual Testing
**Module:** Payment Processing & Refunds

---

## Overview

This document provides comprehensive manual testing procedures for the Cashbox module, including:
- Payment processing (cash and card)
- Partial payments
- Full payments
- Payment refunds (full and partial)
- Receipt generation
- Billing calculations

---

## Prerequisites

Before testing, ensure:
1. Database migrations are applied: `python manage.py migrate`
2. Test data is created: `python manage.py create_billing_test_data`
3. User with cashbox role exists
4. Server is running: `python manage.py runserver`

---

## Test Scenarios

### 1. Payment Processing Tests

#### Test 1.1: Accept Full Cash Payment

**Objective:** Verify that a full cash payment can be accepted and billing status updates correctly.

**Steps:**
1. Log in as cashbox user
2. Navigate to Cashbox → Billing List
3. Select a booking with `calculated` status
4. Click "Calculate Billing" if not already calculated
5. Note the total amount (e.g., 1,217,000 сум)
6. Click "Accept Payment" button
7. Enter payment details:
   - Amount: Full amount (1,217,000)
   - Payment Method: Cash
   - Notes: "Test full cash payment"
8. Submit the form

**Expected Results:**
- ✅ Payment transaction created successfully
- ✅ Billing status changes to "paid"
- ✅ Success message displayed
- ✅ Transaction appears in payment history
- ✅ Receipt link available

---

#### Test 1.2: Accept Partial Payment

**Objective:** Verify partial payment processing.

**Steps:**
1. Navigate to a booking with `calculated` billing
2. Click "Accept Payment"
3. Enter partial amount (e.g., 500,000 out of 1,217,000)
4. Payment Method: Cash
5. Submit

**Expected Results:**
- ✅ Payment accepted
- ✅ Billing status changes to "partially_paid"
- ✅ Remaining balance shown correctly
- ✅ Can make additional payments

---

#### Test 1.3: Multiple Partial Payments

**Objective:** Test multiple payments until fully paid.

**Steps:**
1. Start with partially paid billing (Test 1.2)
2. Make second payment: 400,000 сум
3. Make third payment: remaining amount (317,000)

**Expected Results:**
- ✅ All payments recorded
- ✅ Billing status updates to "paid" after final payment
- ✅ Total paid equals billing total
- ✅ Multiple transactions visible in history

---

#### Test 1.4: Card Payment with Reference Number

**Objective:** Verify card payment requires reference number.

**Steps:**
1. Navigate to unpaid billing
2. Click "Accept Payment"
3. Amount: Any valid amount
4. Payment Method: "Банковская карта"
5. **Leave reference number empty**
6. Try to submit

**Expected Results:**
- ❌ Form validation error
- ✅ Error message: "Номер транзакции обязателен для безналичных платежей"
- ✅ Payment not created

**Then:**
7. Enter reference number: "CARD-12345"
8. Submit

**Expected Results:**
- ✅ Payment accepted with reference number

---

#### Test 1.5: Prevent Overpayment

**Objective:** Verify system prevents overpayment.

**Steps:**
1. Navigate to billing with total 1,217,000 сум
2. Click "Accept Payment"
3. Enter amount: 2,000,000 (more than total)
4. Try to submit

**Expected Results:**
- ❌ Validation error
- ✅ Error message indicating amount exceeds balance
- ✅ Payment not created

---

### 2. Refund Processing Tests

#### Test 2.1: Full Refund

**Objective:** Test full payment refund.

**Steps:**
1. Find a COMPLETED payment transaction
2. Click "Refund" button (if available in UI, otherwise use refund endpoint)
3. Enter refund details:
   - Refund Amount: Full payment amount
   - Reason: "Customer cancellation"
   - Check confirmation box
4. Submit

**Expected Results:**
- ✅ Refund transaction created with negative amount
- ✅ Original payment status changes to "REFUNDED"
- ✅ Billing status recalculated (back to "calculated" if full refund)
- ✅ Refund reference: "REFUND-{original_payment_id}"
- ✅ Success message with refund ID

---

#### Test 2.2: Partial Refund

**Objective:** Test partial payment refund.

**Steps:**
1. Find a COMPLETED payment of 500,000 сум
2. Click "Refund"
3. Enter partial refund amount: 200,000
4. Reason: "Partial service cancellation"
5. Confirm and submit

**Expected Results:**
- ✅ Refund transaction created: -200,000
- ✅ Original payment remains "COMPLETED" (not REFUNDED)
- ✅ Billing status recalculated to "partially_paid"
- ✅ Notes added to original payment about partial refund

---

#### Test 2.3: Prevent Double Refund

**Objective:** Verify already refunded payment cannot be refunded again.

**Steps:**
1. Use a payment that was fully refunded (Test 2.1)
2. Try to refund it again

**Expected Results:**
- ❌ Error message: "Этот платеж уже возвращен"
- ✅ No new refund transaction created

---

#### Test 2.4: Refund Amount Validation

**Objective:** Test refund amount validation.

**Steps:**
1. Payment amount: 500,000 сум
2. Try to refund: 600,000 сум (more than payment)

**Expected Results:**
- ❌ Validation error
- ✅ Error message: "Сумма возврата не может превышать сумму платежа"

---

#### Test 2.5: Refund Requires Reason

**Objective:** Verify refund reason is mandatory.

**Steps:**
1. Attempt refund without entering reason
2. Try to submit

**Expected Results:**
- ❌ Validation error
- ✅ Refund not processed

---

### 3. Receipt Generation Tests

#### Test 3.1: View Payment Receipt

**Objective:** Verify receipt displays correctly.

**Steps:**
1. Complete a payment (Test 1.1)
2. Click on receipt link or navigate to payment receipt URL
3. Review receipt content

**Expected Results:**
- ✅ Receipt header with "КВИТАНЦИЯ ОБ ОПЛАТЕ"
- ✅ Receipt number and date displayed
- ✅ Patient information correct
- ✅ Booking details shown
- ✅ Payment method displayed
- ✅ Amount prominently displayed
- ✅ Billing summary included
- ✅ Cashier name shown
- ✅ Professional layout

---

#### Test 3.2: Print Receipt

**Objective:** Test receipt printing.

**Steps:**
1. Open receipt (Test 3.1)
2. Click "Печать квитанции" button
3. Review print preview

**Expected Results:**
- ✅ Print dialog opens
- ✅ No-print elements hidden (buttons, etc.)
- ✅ Receipt formatted for printing
- ✅ Print timestamp added

---

#### Test 3.3: Refund Receipt

**Objective:** Verify refund appears correctly on receipt.

**Steps:**
1. Process a refund (Test 2.1 or 2.2)
2. View refund transaction receipt

**Expected Results:**
- ✅ Amount shows as negative or with "ВОЗВРАТ" badge
- ✅ Status shows "REFUNDED"
- ✅ Refund reference number displayed
- ✅ Distinct visual indication of refund

---

### 4. Billing Calculation Tests

#### Test 4.1: Medication Billing

**Objective:** Verify medications are billed correctly.

**Steps:**
1. Create or use booking with medication sessions
2. Calculate billing
3. Review medication breakdown

**Expected Results:**
- ✅ Each medication listed with quantity and unit price
- ✅ Total = quantity × unit_price
- ✅ Medication amount added to billing total

---

#### Test 4.2: Lab Research Billing

**Objective:** Verify only billable labs are charged.

**Steps:**
1. Create booking with:
   - Lab in "dispatched" state (billable)
   - Lab in "results" state (billable)
   - Lab in "recommended" state (NOT billable)
   - Lab in "cancelled" state (NOT billable)
2. Calculate billing
3. Review lab breakdown

**Expected Results:**
- ✅ Only "dispatched" and "results" labs billed
- ✅ Recommended/cancelled labs show "не оплачивается"
- ✅ Lab total = sum of billable labs only
- ✅ Visual indicators show billable status

---

#### Test 4.3: Combined Billing

**Objective:** Test complete billing with all components.

**Steps:**
1. Use booking with:
   - Base tariff: 500,000
   - Extra services: 410,000
   - Medications: 212,000
   - Labs: 95,000
2. Calculate billing

**Expected Results:**
- ✅ Tariff base amount: 500,000
- ✅ Additional services: 410,000
- ✅ Medications: 212,000
- ✅ Lab research: 95,000
- ✅ Total: 1,217,000
- ✅ All breakdowns visible per patient

---

### 5. Edge Cases & Error Handling

#### Test 5.1: Payment on Non-Calculated Billing

**Objective:** Verify payment requires calculated billing.

**Steps:**
1. Try to accept payment on billing with "pending" status

**Expected Results:**
- ❌ Error: "Невозможно принять оплату. Счет должен быть рассчитан."

---

#### Test 5.2: Concurrent Payments

**Objective:** Test payment atomicity.

**Steps:**
1. Open billing in two browser tabs
2. Simultaneously accept payments in both tabs
3. Check transaction integrity

**Expected Results:**
- ✅ Both payments may succeed if total doesn't exceed billing
- ✅ If total would exceed, one should fail
- ✅ Database consistency maintained

---

#### Test 5.3: Zero Amount Payment

**Objective:** Verify zero payments rejected.

**Steps:**
1. Try to accept payment with amount: 0

**Expected Results:**
- ❌ Validation error
- ✅ Payment not created

---

## Test Data

### Using Test Data Command

```bash
python manage.py create_billing_test_data
```

This creates:
- Test booking with ID (check console output)
- Patient with complete data
- Medications with sessions
- Lab tests in various states
- Services with usage
- Billing total: 1,217,000 сум

### Manual Test Data Creation

If needed, create test data via Django admin:
1. Create Patient
2. Create Booking
3. Create IllnessHistory linked to booking
4. Add PrescribedMedications with MedicationSessions
5. Add AssignedLabs with different states
6. Navigate to Cashbox to test

---

## Automated Test Execution

### Running Unit Tests

While comprehensive integration tests require extensive setup, you can verify core functionality:

```bash
# Test all cashbox tests
python manage.py test application.cashbox.tests

# Test specific module
python manage.py test application.cashbox.tests.test_payment

# Test with verbosity
python manage.py test application.cashbox.tests --verbosity=2
```

### Test Coverage

Key areas covered by tests:
- Payment form validation
- Refund form validation
- Transaction creation
- Billing status updates
- Receipt rendering

---

## Common Issues & Solutions

### Issue 1: "User does not have cashbox role"

**Solution:** Ensure logged-in user has cashbox role assigned:
```python
from core.models import RolesModel
user.roles.add(RolesModel.objects.get(name='cashbox'))
```

### Issue 2: "Billing not found"

**Solution:** Calculate billing first before accepting payment.

### Issue 3: "Reference number required"

**Solution:** For card/online payments, reference number is mandatory.

### Issue 4: "Cannot refund this payment"

**Solution:** Only COMPLETED payments can be refunded, not PENDING or FAILED.

---

## Performance Testing

### Load Test Scenarios

1. **Concurrent Payments:** 10 users accepting payments simultaneously
2. **Large Billing:** Booking with 100+ medication sessions
3. **Multiple Refunds:** Process 50 refunds in quick succession

### Performance Benchmarks

- Payment acceptance: < 500ms
- Billing calculation: < 1s for typical booking
- Receipt generation: < 200ms
- Refund processing: < 500ms

---

## Security Testing

### Security Checklist

- [ ] Only cashbox role can access payment functions
- [ ] SQL injection protection (Django ORM)
- [ ] CSRF protection on all POST requests
- [ ] XSS protection on receipt display
- [ ] Transaction atomicity (no partial updates)
- [ ] Audit trail (created_by, modified_by)

---

## Reporting Test Results

### Test Result Template

```
Test ID: [e.g., Test 1.1]
Test Name: [e.g., Accept Full Cash Payment]
Date: [YYYY-MM-DD]
Tester: [Name]
Status: [PASS/FAIL]
Notes: [Any observations]
Screenshots: [If applicable]
```

### Bug Report Template

```
Bug ID: CASHBOX-XXX
Severity: [Critical/High/Medium/Low]
Summary: [Brief description]
Steps to Reproduce:
1. ...
2. ...
Expected: ...
Actual: ...
Screenshots: ...
Environment: [Browser, OS]
```

---

## Acceptance Criteria

### Payment Processing
- ✅ Cash payments accepted
- ✅ Card payments with reference
- ✅ Partial payments supported
- ✅ Overpayment prevented
- ✅ Status updates correctly

### Refund Processing
- ✅ Full refunds work
- ✅ Partial refunds work
- ✅ Double refund prevented
- ✅ Refund validation works
- ✅ Billing status recalculated

### Receipt Generation
- ✅ Professional layout
- ✅ All details present
- ✅ Print-friendly
- ✅ Refunds indicated

### Billing Calculations
- ✅ Medications billed correctly
- ✅ Only billable labs charged
- ✅ Totals accurate
- ✅ Per-patient breakdown

---

## Sign-Off

Once all tests pass:

**Tested By:** ________________
**Date:** ________________
**Status:** [ ] PASS [ ] FAIL
**Ready for Production:** [ ] YES [ ] NO

**Notes:**
```
[Any final observations or recommendations]
```

---

## Appendix

### A. URL Endpoints

- Billing List: `/cashbox/billing/`
- Billing Detail: `/cashbox/billing/<booking_id>/`
- Accept Payment: `/cashbox/billing/<booking_id>/accept-payment/`
- Refund Payment: `/cashbox/payment/<transaction_id>/refund/`
- Payment Receipt: `/cashbox/payment/<transaction_id>/receipt/`

### B. Database Tables

- `booking_billing`: Billing records
- `transactions`: Payment/refund transactions
- `medication_session`: Medication usage
- `assigned_labs`: Lab test assignments

### C. Key Files

- Views: `application/cashbox/views/payment.py`
- Forms: `application/cashbox/forms/payment_forms.py`
- Template: `application/templates/cashbox/payment/receipt.html`
- Models: `core/models/transactions.py`

---

**End of Testing Guide**
