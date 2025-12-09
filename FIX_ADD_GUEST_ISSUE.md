# Fix for Add Guest Form Issue

## Problem

When trying to add a guest to booking #65 at `/logus/booking/65/add-guest/`, the form was not submitting even though patient, tariff, and room were selected.

## Root Causes

1. **Select2 values not submitting properly** - Similar issue to patient assignment page
2. **Price field was required but being cleared** - The JavaScript cleared the price field for auto-calculation, but the field was marked as required, causing validation to fail

## Changes Made

### 1. Updated Template: [booking_detail_form.html](application/templates/logus/booking/booking_detail_form.html)

**Added:**
- ✅ `allowClear: false` to prevent clearing required Select2 fields
- ✅ Debug logging to console for form submission
- ✅ Error highlighting for Select2 fields with validation errors
- ✅ Improved price auto-clear logic (only clears if both tariff and room are selected)

### 2. Updated Form: [booking.py:311](application/logus/forms/booking.py#L311)

**Added:**
```python
# Make price optional since it's auto-calculated
self.fields['price'].required = False
```

Now the price field is optional and will be auto-calculated server-side based on tariff and room type.

## How to Test

1. **Clear browser cache** (Ctrl+F5 or Cmd+Shift+R)
2. Navigate to: `/logus/booking/65/add-guest/`
3. **Open browser console** (F12 → Console tab) to see debug logs
4. Fill in the form:
   - Select a **Patient** (пациент)
   - Select a **Room** (комната)
   - Select a **Tariff** (тариф)
   - Leave **Price** empty (it will auto-calculate)
5. Click **Сохранить** (Save)

## Expected Behavior

### Before Fix ❌
- Form validation fails even with all fields selected
- Price field required error
- No clear error messages

### After Fix ✅
- Form submits successfully
- Price auto-calculates based on tariff and room type
- Clear console logging shows:
  ```
  === Form Submission ===
  Client: 123
  Room: 45
  Tariff: 2
  Price: (empty - will be calculated)
  ```

## Debug Information

If the form still doesn't work, check the browser console for:

```javascript
// These logs will appear on form submission
=== Form Submission ===
Client: <patient_id>
Room: <room_id>
Tariff: <tariff_id>
Price: <empty or value>

// If fields are missing:
Missing required fields!
  - Client is empty
  - Room is empty
  - Tariff is empty
```

## Form Validation Flow

1. **Client-side**: Select2 ensures values are selected
2. **Server-side** ([booking.py:337-347](application/logus/forms/booking.py#L337-L347)):
   - Validates room availability
   - Auto-calculates price from `TariffRoomPrice` table
   - If no price found, raises error: "Нет цены для данного сочетания тарифа и типа комнаты"

## Testing Server-side Auto-calculation

```bash
source .venv/bin/activate
python manage.py shell
```

```python
from core.models import Tariff, Room, TariffRoomPrice

# Check if price exists for your tariff/room combination
tariff = Tariff.objects.get(id=YOUR_TARIFF_ID)
room = Room.objects.get(id=YOUR_ROOM_ID)

try:
    price = TariffRoomPrice.objects.get(
        tariff=tariff,
        room_type=room.room_type
    )
    print(f"Price found: {price.price}")
except TariffRoomPrice.DoesNotExist:
    print(f"ERROR: No price for {tariff.name} + {room.room_type.name}")
```

## Additional Notes

- The view also validates **room capacity** ([booking_detail.py:189-195](application/logus/views/booking_detail.py#L189-L195))
- If room is at full capacity, you'll see: "Пожалуйста, выберите другую комнату или измените даты бронирования"
