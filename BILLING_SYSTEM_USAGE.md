# Tariff Change & Billing System - Usage Guide

## Overview

This system handles tariff and room changes during a patient's stay, with accurate billing based on which tariff was active when services were performed.

## Key Concepts

1. **BookingDetail** - Represents a tariff/room period. Each change creates a new BookingDetail.
2. **ServiceSessionTracking** - Tracks service usage per BookingDetail period.
3. **IndividualProcedureSessionModel** - Individual service sessions with billing information.
4. **BookingBillingBreakdown** - Complete billing calculation across all periods.

## Example Usage

### 1. Changing a Patient's Tariff Mid-Stay

```python
from django.utils import timezone
from datetime import timedelta
from core.models.booking import Booking, BookingDetail
from core.models.tariffs import Tariff
from core.models.rooms import Room
from core.models.clients import PatientModel

# Get the booking and patient
booking = Booking.objects.get(booking_number="BK-20250126-1234")
patient = PatientModel.objects.get(id=1)

# Get the new tariff
new_tariff = Tariff.objects.get(name="VIP Package")

# Optional: Change room as well
new_room = Room.objects.get(name="Room 301")

# Change tariff (and optionally room) effective immediately
new_detail = BookingDetail.change_tariff(
    booking=booking,
    client=patient,
    new_tariff=new_tariff,
    new_room=new_room,  # Optional
    change_datetime=None  # None = now, or specify a datetime
)

print(f"Tariff changed successfully!")
print(f"Old Detail: {booking.details.filter(is_current=False).first()}")
print(f"New Detail: {new_detail}")
```

### 2. Changing Tariff at a Specific Date/Time

```python
from django.utils import timezone
from datetime import timedelta

# Change tariff to be effective from 3 days ago
change_date = timezone.now() - timedelta(days=3)

new_detail = BookingDetail.change_tariff(
    booking=booking,
    client=patient,
    new_tariff=new_tariff,
    change_datetime=change_date
)

# The system will automatically:
# 1. Close the previous BookingDetail at change_date
# 2. Create new BookingDetail starting from change_date
# 3. Initialize tracking for services in the new tariff
```

### 3. Completing a Service Session (Automatic Billing)

```python
from core.models.sanatorium.prescriptions.procedures import (
    ProcedureServiceModel,
    IndividualProcedureSessionModel
)
from django.utils import timezone

# Get a pending session
session = IndividualProcedureSessionModel.objects.get(id=123)

# Complete the session
session.status = 'completed'
session.completed_at = timezone.now()
session.save()

# The system automatically:
# 1. Finds the BookingDetail that was active at completed_at time
# 2. Checks if service is included in that tariff
# 3. Counts sessions used in that period
# 4. Determines if this session should be billed
# 5. Sets is_billable and billed_amount accordingly

print(f"Session #{session.session_number}")
print(f"Tariff at time: {session.booking_detail_at_time.tariff.name}")
print(f"Billable: {session.is_billable}")
print(f"Amount: {session.billed_amount} UZS")
```

### 4. Calculating Final Billing for a Booking

```python
from core.billing import calculate_booking_billing, update_booking_billing_record

# Calculate detailed billing breakdown
breakdown = calculate_booking_billing(booking)

# Print detailed breakdown
print(breakdown)

# Output will show:
# - Each tariff period with dates and days
# - Services used in each period (included vs. billed)
# - Prorated tariff charges
# - Total charges per period
# - Grand total

# Update the BookingBilling record in database
billing = update_booking_billing_record(booking)
print(f"Billing Status: {billing.billing_status}")
print(f"Total Amount: {billing.total_amount} UZS")
```

### 5. Viewing Billing Breakdown Programmatically

```python
from core.billing import calculate_booking_billing

breakdown = calculate_booking_billing(booking)

# Access individual periods
for period in breakdown.periods:
    print(f"Period: {period.tariff_name}")
    print(f"  Dates: {period.effective_from} to {period.effective_to}")
    print(f"  Days: {period.days_in_period}")
    print(f"  Tariff Base: {period.tariff_base_charge} UZS")

    # Access service details
    for service in period.service_sessions:
        print(f"  - {service['service_name']}")
        print(f"    Used: {service['sessions_used']}/{service['sessions_included']}")
        print(f"    Billed: {service['sessions_billed']} sessions")
        print(f"    Amount: {service['amount']} UZS")

    print(f"  Period Total: {period.total_period_charge} UZS\n")

# Access totals
print(f"Total Tariff Charges: {breakdown.total_tariff_charges} UZS")
print(f"Total Service Charges: {breakdown.total_service_charges} UZS")
print(f"Grand Total: {breakdown.grand_total} UZS")
```

### 6. Recalculating Billing After Tariff Change

```python
from core.billing import recalculate_all_sessions_for_booking

# If you changed a tariff retroactively, recalculate all sessions
count = recalculate_all_sessions_for_booking(booking)
print(f"Recalculated {count} sessions")

# Then update the billing record
billing = update_booking_billing_record(booking)
```

### 7. Checking Service Tracking for a Period

```python
from core.models.tariffs import ServiceSessionTracking

# Get current BookingDetail
current_detail = BookingDetail.objects.get(
    booking=booking,
    client=patient,
    is_current=True
)

# View service tracking
for tracking in current_detail.service_tracking.all():
    print(f"Service: {tracking.service.name}")
    print(f"  Included: {tracking.sessions_included}")
    print(f"  Used: {tracking.sessions_used}")
    print(f"  Billed: {tracking.sessions_billed}")
    print(f"  Remaining: {tracking.sessions_remaining}")
    print(f"  Exceeded: {tracking.sessions_exceeded}\n")
```

## Complete Example: Patient Journey with Two Tariff Changes

```python
from django.utils import timezone
from datetime import timedelta
from core.models.booking import Booking, BookingDetail
from core.models.tariffs import Tariff
from core.models.services import Service
from core.models.sanatorium.prescriptions.procedures import (
    ProcedureServiceModel,
    IndividualProcedureSessionModel
)
from core.billing import calculate_booking_billing

# Initial setup
booking = Booking.objects.get(booking_number="BK-20250126-1234")
patient = booking.details.first().client

# Get tariffs and service
tariff_a = Tariff.objects.get(name="Basic Package")  # Includes 5 massage sessions
tariff_b = Tariff.objects.get(name="Premium Package")  # Includes 10 massage sessions
massage_service = Service.objects.get(name="Massage")

print("=== Day 1: Patient checks in with Tariff A ===")
# Patient starts with Tariff A (already created during booking)

# Complete 3 massage sessions (Days 1-3)
print("\n=== Days 1-3: Complete 3 massage sessions under Tariff A ===")
for i in range(1, 4):
    session = IndividualProcedureSessionModel.objects.filter(
        assigned_procedure__illness_history__booking=booking,
        session_number=i
    ).first()

    session.status = 'completed'
    session.completed_at = timezone.now() - timedelta(days=7-i)
    session.save()

    print(f"Session {i}: Billable={session.is_billable}, Amount={session.billed_amount}")
    # All 3 are free (within 5 included sessions)

# Day 4: Change to Tariff B
print("\n=== Day 4: Change to Tariff B ===")
change_date = timezone.now() - timedelta(days=4)
new_detail = BookingDetail.change_tariff(
    booking=booking,
    client=patient,
    new_tariff=tariff_b,
    change_datetime=change_date
)
print(f"Changed to {new_detail.tariff.name}")

# Complete 8 more massage sessions under Tariff B (Days 4-11)
print("\n=== Days 4-11: Complete 8 massage sessions under Tariff B ===")
for i in range(4, 12):
    session = IndividualProcedureSessionModel.objects.filter(
        assigned_procedure__illness_history__booking=booking,
        session_number=i
    ).first()

    session.status = 'completed'
    session.completed_at = timezone.now() - timedelta(days=11-i)
    session.save()

    print(f"Session {i}: Billable={session.is_billable}, Amount={session.billed_amount}")
    # First 10 are free (within Tariff B's 10 included sessions)
    # BUT we're still in the new period, so we have a fresh count

# Calculate final billing
print("\n=== Final Billing Calculation ===")
breakdown = calculate_booking_billing(booking)
print(breakdown)

# Result:
# Period 1 (Tariff A): 3 massages used, 0 billed
# Period 2 (Tariff B): 8 massages used, 0 billed
# Total service charges: 0 UZS (all within included amounts)
```

##migrations and Data Migration

After making model changes, create and apply migrations:

```bash
# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# If you have existing BookingDetail records, run a data migration:
python manage.py shell
```

```python
# In Django shell - Update existing BookingDetails
from core.models.booking import BookingDetail
from django.utils import timezone

for detail in BookingDetail.objects.all():
    if not detail.effective_from:
        # Set effective_from to booking start date or creation date
        detail.effective_from = detail.start_date or detail.booking.start_date or detail.created_at
        detail.effective_to = None
        detail.is_current = True
        detail.save()
        print(f"Updated {detail.id}")
```

## Business Logic Summary

1. **Tariff Change** - Creates new BookingDetail, closes previous one
2. **Service Completion** - Looks up active BookingDetail at completion time
3. **Billing Calculation** - Counts sessions per period, bills excess
4. **Prorated Charges** - Tariff base charges prorated by days in period
5. **Period Isolation** - Each tariff period has its own session counters

## Testing Scenarios

### Scenario 1: Service Moves from Not-Included to Included

```python
# Patient has Tariff A (no massage included)
# Uses massage 3 times -> pays for 3

# Changes to Tariff B (includes 10 massages)
# Uses massage 5 more times -> pays for 0

# Result: Pays for 3 sessions total
```

### Scenario 2: Service Moves from Included to Not-Included

```python
# Patient has Tariff A (includes 5 massages)
# Uses massage 3 times -> pays for 0

# Changes to Tariff C (no massage included)
# Uses massage 2 more times -> pays for 2

# Result: Pays for 2 sessions total
```

### Scenario 3: Multiple Tariff Changes

```python
# Tariff A (0 massages) -> Use 2 -> Pay 2
# Change to Tariff B (10 massages) -> Use 5 -> Pay 0
# Change to Tariff C (3 massages) -> Use 5 -> Pay 2 (exceeded by 2)

# Result: Pays for 4 sessions total (2 + 0 + 2)
```

## API Integration (Optional)

For REST API integration:

```python
# views.py
from rest_framework.decorators import api_view
from rest_framework.response import Response
from core.billing import calculate_booking_billing

@api_view(['POST'])
def change_patient_tariff(request, booking_id):
    """API endpoint to change patient tariff"""
    booking = Booking.objects.get(id=booking_id)
    patient = PatientModel.objects.get(id=request.data['patient_id'])
    new_tariff = Tariff.objects.get(id=request.data['tariff_id'])

    new_detail = BookingDetail.change_tariff(
        booking=booking,
        client=patient,
        new_tariff=new_tariff
    )

    return Response({
        'success': True,
        'new_detail_id': new_detail.id,
        'tariff_name': new_detail.tariff.name
    })

@api_view(['GET'])
def get_billing_breakdown(request, booking_id):
    """API endpoint to get billing breakdown"""
    booking = Booking.objects.get(id=booking_id)
    breakdown = calculate_booking_billing(booking)

    return Response(breakdown.to_dict())
```

## Notes

- All datetime operations use Django's timezone-aware datetimes
- Session billing is calculated automatically on completion
- Tariff changes are retroactive-safe (can change effective dates in the past)
- Database indexes optimize period queries
- Backward compatible with existing bookings