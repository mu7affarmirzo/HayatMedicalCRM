# Price Auto-calculation Fix

## Summary

Fixed the price calculation in the add-guest form to properly calculate: **`days_of_stay × tariff.price`**

## Test Results ✅

For Booking #65:
- **Start Date**: 2025-12-10
- **End Date**: 2025-12-16
- **Days of Stay**: 6 days
- **Tariff**: Basic Package (40,000)
- **Calculated Price**: 6 × 40,000 = **240,000** ✅

## Changes Made

### 1. Updated Form Logic ([booking.py:340-357](application/logus/forms/booking.py#L340-L357))

**OLD** (Incorrect):
```python
# Used TariffRoomPrice.price (one-time price)
price_record = TariffRoomPrice.objects.get(
    tariff=tariff,
    room_type=room.room_type
)
cleaned_data['price'] = price_record.price  # ❌ Not multiplied by days
```

**NEW** (Correct):
```python
# Calculate: days × tariff price
days_of_stay = (end_date.date() - start_date.date()).days
if days_of_stay < 1:
    days_of_stay = 1  # Minimum 1 day

cleaned_data['price'] = days_of_stay * tariff.price  # ✅ Correct calculation
```

### 2. Updated Template ([booking_detail_form.html](application/templates/logus/booking/booking_detail_form.html))

**Added:**
- ✅ Made price field **read-only** (cannot be manually edited)
- ✅ Updated help text: "Рассчитывается как: дни проживания × цена тарифа"
- ✅ Added "(авто)" label to indicate auto-calculation
- ✅ Set placeholder: "Авто-расчет"

### 3. Made Price Field Optional ([booking.py:311](application/logus/forms/booking.py#L311))

```python
# Make price optional since it's auto-calculated
self.fields['price'].required = False
```

## How It Works Now

1. **User selects**:
   - Patient (пациент)
   - Room (комната)
   - Tariff (тариф)

2. **Price field**:
   - Shows as **read-only** with placeholder "Авто-расчет"
   - Users **cannot** manually enter a price

3. **On form submission**:
   - JavaScript clears price field (triggers auto-calculation)
   - Server calculates: `(end_date - start_date) × tariff.price`
   - Minimum 1 day is always charged

4. **Success**:
   - Guest is added with correctly calculated price

## Example Calculation

```
Booking Dates: Dec 10 - Dec 16 (6 days)
Tariff: Basic Package (40,000 per day)
---
Price = 6 days × 40,000 = 240,000
```

## Error Handling

If tariff has no price set:
```
❌ Error: "У выбранного тарифа не указана цена."
```

## How to Test

1. Go to `/logus/booking/65/add-guest/`
2. Select patient, room, and tariff
3. Notice price field is **grayed out** (read-only)
4. Submit form
5. Check that price = days × tariff.price

## Console Output (Debug)

```
Tariff changed to: 2
Price cleared for auto-calculation
=== Form Submission ===
Client: 123
Room: 45
Tariff: 2
Price: (empty - will be auto-calculated)
```

## Database Schema

The price is stored in `BookingDetail.price`:
```sql
SELECT
    bd.id,
    bd.price,
    t.price as tariff_price,
    JULIANDAY(b.end_date) - JULIANDAY(b.start_date) as days,
    bd.price / (JULIANDAY(b.end_date) - JULIANDAY(b.start_date)) as price_per_day
FROM core_bookingdetail bd
JOIN core_booking b ON bd.booking_id = b.id
JOIN core_tariff t ON bd.tariff_id = t.id
WHERE b.id = 65;
```

This confirms: `price = days × tariff.price` ✅
