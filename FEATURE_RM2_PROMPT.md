# Feature Request: RM2 - Room Availability V2

## Executive Summary

Implement a comprehensive Room Availability Matrix (RM2) feature that provides a visual, interactive matrix view for managing room bookings. This system will replace the current linear availability checking with a powerful matrix interface showing room availability across time periods, with detailed occupancy information and direct booking capabilities.

---

## Current System Analysis

### Existing Availability Features

**Current Implementation:**
- **Available Rooms View** ([application/templates/logus/available_rooms.html](application/templates/logus/available_rooms.html))
  - Shows daily grid per room type
  - Color-coded availability (green/red)
  - Basic pricing display

- **Availability Matrix** ([application/templates/logus/availability_matrix.html](application/templates/logus/availability_matrix.html))
  - Room type × tariff matrix
  - Binary available/occupied status
  - Filter buttons for viewing

- **Check Availability** ([application/templates/logus/check_availability.html](application/templates/logus/check_availability.html))
  - AJAX-based date range search
  - Dynamic results loading

**Key Services:**
- `get_availability_matrix()` - [application/logus/services/rooms.py](application/logus/services/rooms.py)
- `get_room_availability_details()` - [application/logus/utils/room_capacity.py](application/logus/utils/room_capacity.py)
- `check_room_availability_ajax()` - [application/logus/views/booking.py](application/logus/views/booking.py)

### Limitations of Current System

1. **No Timeline Visualization**: Can't see booking patterns over multiple days in a single view
2. **Limited Detail**: Binary available/unavailable without occupant information
3. **No Partial Availability**: Doesn't show which specific days are occupied in a period
4. **Manual Navigation**: Can't click directly on availability cells to create bookings
5. **No Occupant Info**: Can't see who is occupying rooms without drilling down
6. **Type-Level Only**: Must select type first, then see individual rooms

---

## Feature Requirements: RM2

### 1. Period Selection Interface

**Requirements:**
- Date range selector with start and end date pickers
  - Format: DD.MM.YYYY (consistent with [BookingInitialForm](application/logus/forms/booking.py:25))
  - Minimum period: 1 day
  - Maximum period: 90 days (configurable)
  - Default: Today + 14 days

- Quick period shortcuts:
  - Today only
  - This week (Monday-Sunday)
  - Next 7 days
  - Next 14 days
  - Next 30 days
  - Custom range

- Validation:
  - Start date cannot be in the past
  - End date must be after start date
  - Period cannot exceed maximum allowed days
  - Display warning if period > 30 days (performance consideration)

**UI Component:**
```html
<div class="period-selector">
    <div class="date-inputs">
        <input type="text" id="period_start" placeholder="DD.MM.YYYY">
        <span>to</span>
        <input type="text" id="period_end" placeholder="DD.MM.YYYY">
        <button id="search-availability">Search</button>
    </div>
    <div class="quick-periods">
        <button data-days="0">Today</button>
        <button data-days="7">Next 7 Days</button>
        <button data-days="14">Next 14 Days</button>
        <button data-days="30">Next 30 Days</button>
    </div>
</div>
```

---

### 2. Primary Matrix View: Period × Room Types

**Matrix Structure:**
```
┌─────────────┬──────────┬──────────┬──────────┬──────────┐
│ Room Type   │ Day 1    │ Day 2    │ Day 3    │ ...      │
├─────────────┼──────────┼──────────┼──────────┼──────────┤
│ Standard    │ 5/10     │ 3/10     │ 8/10     │ ...      │
│ Deluxe      │ 2/5      │ 2/5      │ 4/5      │ ...      │
│ Suite       │ 1/3      │ 0/3      │ 2/3      │ ...      │
└─────────────┴──────────┴──────────┴──────────┴──────────┘
```

**Cell Display Format:**
- **Primary:** `{occupied}/{total}` (e.g., "5/10" means 5 occupied, 10 total rooms)
- **Color Coding:**
  - Green: 0-40% occupancy (high availability)
  - Yellow: 41-75% occupancy (moderate availability)
  - Orange: 76-99% occupancy (low availability)
  - Red: 100% occupancy (fully booked)
  - Gray: Room type not active

- **Hover Tooltip:**
  - Available rooms: {count}
  - Occupied rooms: {count}
  - Under maintenance: {count}
  - Average price range: {min} - {max}

- **Cell Click Action:**
  - Expand to show individual rooms dropdown (see Section 3)
  - Highlight selected cell
  - Maintain selection state

**Data Source:**
```python
# View: application/logus/views/rooms.py - room_availability_matrix_v2()
# Returns structure:
{
    'period': {
        'start': date,
        'end': date,
        'days': [date1, date2, ...]
    },
    'room_types': [
        {
            'id': int,
            'name': str,
            'total_rooms': int,
            'daily_availability': [
                {
                    'date': date,
                    'total': int,
                    'occupied': int,
                    'available': int,
                    'under_maintenance': int,
                    'occupancy_percentage': float
                }
            ]
        }
    ]
}
```

**Filtering Options:**
- Show all room types / only available types
- Include/exclude maintenance periods
- Filter by minimum availability (e.g., show only if ≥2 rooms available)

**Additional Features:**
- Horizontal scroll for long periods (>14 days)
- Sticky header and room type column
- Export to Excel/CSV option
- Print-friendly view
- Refresh button with last updated timestamp

---

### 3. Secondary View: Individual Rooms Dropdown

**Triggered By:** Clicking a cell in the primary matrix

**Dropdown Content:**
- Appears below the clicked row
- Shows all rooms of the selected type
- Displays detailed availability timeline for each room

**Room List Structure:**
```html
<div class="room-details-dropdown">
    <div class="room-header">
        <h4>Standard Rooms - March 15 to March 30</h4>
        <button class="close-dropdown">×</button>
    </div>

    <div class="rooms-list">
        <!-- For each room -->
        <div class="room-item" data-room-id="123">
            <div class="room-info">
                <strong>Room 101</strong>
                <span class="capacity">Capacity: 2</span>
                <span class="price">₸15,000/day</span>
            </div>

            <div class="room-timeline">
                <!-- Timeline grid showing day-by-day status -->
                <!-- See Section 4 for detailed timeline specification -->
            </div>

            <div class="room-actions">
                <button class="btn-book-room" data-room-id="123">
                    Book This Room
                </button>
                <button class="btn-view-details" data-room-id="123">
                    View Details
                </button>
            </div>
        </div>
    </div>
</div>
```

**Room Sorting:**
- Default: Room number (ascending)
- Options:
  - By availability (most available first)
  - By price (low to high / high to low)
  - By capacity (ascending / descending)

---

### 4. Detailed Room Timeline Visualization

**Timeline Grid for Individual Room:**

Each room shows a horizontal timeline for the selected period with day-by-day status.

**Visual Structure:**
```
Room 101: [====][FREE][====][====][FREE][FREE][====][====]...
          Mar15  16   17    18    19    20    21    22
```

**Day Cell States:**

1. **AVAILABLE (Free)** - Green background
   - Room is free for the entire day
   - No bookings, no maintenance
   - Shows: "Free"
   - Click action: Start booking for this day

2. **OCCUPIED (Taken)** - Red background
   - Room is booked by one or more guests
   - Shows occupancy info (see below)
   - Click action: View booking details

3. **PARTIALLY AVAILABLE** - Yellow/Striped background
   - Room has capacity but not fully occupied
   - Shows: "{occupied}/{capacity} occupied"
   - Click action: View occupancy + offer to add guest

4. **MAINTENANCE** - Gray background with wrench icon
   - Room under maintenance (see [RoomMaintenance model](core/models/rooms.py:50))
   - Shows: "Maintenance"
   - Click action: View maintenance details
   - Not bookable

5. **CHECK-OUT DAY** - Light blue background
   - Guest checking out this day
   - May become available later in day
   - Shows: "Check-out"

6. **CHECK-IN DAY** - Light green background
   - New guest arriving this day
   - Shows: "Check-in"

**Occupant Information Display (for OCCUPIED cells):**

When hovering or clicking on occupied day cells, show detailed modal or tooltip:

```
╔════════════════════════════════════╗
║ Room 101 - March 17-20, 2025       ║
╠════════════════════════════════════╣
║ Guest 1:                           ║
║   • Name: Айгуль Смагулова         ║
║   • Gender: Female                 ║
║   • Age: 42 years                  ║
║   • Period: Mar 17 - Mar 25        ║
║   • Booking: BK-20250315-0042      ║
║   • Tariff: Standard Care Package  ║
║                                    ║
║ Guest 2:                           ║
║   • Name: [Same format]            ║
║                                    ║
║ Room Status: 2/2 occupied          ║
╚════════════════════════════════════╝
```

**Data Required per Day:**
```python
{
    'date': date,
    'status': 'available|occupied|partial|maintenance|checkout|checkin',
    'occupancy': {
        'current': int,  # Number of guests
        'capacity': int,  # Room capacity
        'percentage': float
    },
    'guests': [
        {
            'id': int,
            'full_name': str,  # From PatientModel
            'gender': str,     # From PatientModel.gender
            'age': int,        # Calculated from date_of_birth
            'booking_number': str,
            'booking_id': int,
            'start_date': date,
            'end_date': date,
            'tariff_name': str
        }
    ],
    'maintenance': {  # If applicable
        'type': str,
        'status': str,
        'description': str
    },
    'is_bookable': bool,
    'conflicts': []  # Overlapping bookings if any
}
```

**Color Highlighting for Booking Periods:**

Within occupied cells, use color bands to distinguish different bookings:

```
Day: [██Guest1██|██Guest2██]
     └─ Blue   └─ Orange
```

Each guest/booking gets a consistent color throughout the timeline for easy visual tracking.

**Special Visual Indicators:**

- **Check-in day**: Small arrow icon pointing right (→)
- **Check-out day**: Small arrow icon pointing left (←)
- **Maintenance**: Wrench/tools icon (🔧)
- **High capacity**: Warning icon if occupancy > 90% (⚠️)
- **Multi-guest**: People icon showing count (👥 ×2)

---

### 5. Direct Booking from Matrix

**Booking Initiation:**

When clicking "Book This Room" or clicking on an available cell, initiate booking flow:

**Option A: Quick Booking Modal**
```html
<div class="quick-booking-modal">
    <h3>Quick Booking - Room 101</h3>
    <form>
        <div class="booking-period">
            <label>Period:</label>
            <input type="text" id="quick_start" value="15.03.2025">
            <input type="text" id="quick_end" value="20.03.2025">
        </div>

        <div class="patient-select">
            <label>Patient:</label>
            <select id="quick_patient">
                <option value="">Search patient...</option>
                <!-- AJAX patient search -->
            </select>
            <button type="button" id="btn-new-patient">+ New Patient</button>
        </div>

        <div class="tariff-select">
            <label>Tariff Package:</label>
            <select id="quick_tariff">
                <option value="1">Standard Care - ₸15,000/day</option>
                <option value="2">Deluxe Care - ₸25,000/day</option>
            </select>
        </div>

        <div class="guest-count">
            <label>Additional Guests:</label>
            <input type="number" min="0" max="1" value="0">
            <small>Room capacity: 2</small>
        </div>

        <div class="actions">
            <button type="submit" class="btn-primary">Create Booking</button>
            <button type="button" class="btn-secondary">Full Booking Form</button>
            <button type="button" class="btn-close">Cancel</button>
        </div>
    </form>
</div>
```

**Option B: Redirect to Existing Multi-Step Booking**

Pre-fill booking form ([booking_start view](application/logus/views/booking.py:134)) with:
- Selected room ID
- Selected dates from matrix
- Room type pre-selected

**Requirements:**
- Validate room still available before confirming
- Check capacity using [check_room_capacity()](application/logus/utils/room_capacity.py:35)
- Check maintenance conflicts using [is_room_under_maintenance()](core/models/rooms.py:94)
- Create [Booking](core/models/booking.py:13) and [BookingDetail](core/models/booking.py:130) records
- Initialize [ServiceSessionTracking](core/models/tariffs.py:75)
- Log action in [BookingHistory](core/models/booking.py:259)
- Refresh matrix after successful booking

**Pre-fill Parameters:**
```python
# URL: /booking/start/?room_id=101&start_date=15.03.2025&end_date=20.03.2025
# Pre-populates:
- patient_id (if coming from patient detail page)
- start_date
- end_date
- selected_rooms list
- room_type filter
```

---

### 6. Additional Information Panels

**Statistics Panel (Top of Page):**
```html
<div class="availability-statistics">
    <div class="stat-card">
        <h4>Total Occupancy</h4>
        <div class="stat-value">68%</div>
        <small>for selected period</small>
    </div>

    <div class="stat-card">
        <h4>Available Rooms</h4>
        <div class="stat-value">32/100</div>
        <small>on average per day</small>
    </div>

    <div class="stat-card">
        <h4>Upcoming Check-ins</h4>
        <div class="stat-value">12</div>
        <small>in next 24 hours</small>
    </div>

    <div class="stat-card">
        <h4>Upcoming Check-outs</h4>
        <div class="stat-value">8</div>
        <small>in next 24 hours</small>
    </div>

    <div class="stat-card">
        <h4>Under Maintenance</h4>
        <div class="stat-value">3</div>
        <small>rooms currently</small>
    </div>
</div>
```

**Legend Panel:**
```html
<div class="availability-legend">
    <h5>Status Legend:</h5>
    <div class="legend-items">
        <span class="legend-item available">Available</span>
        <span class="legend-item occupied">Occupied</span>
        <span class="legend-item partial">Partially Available</span>
        <span class="legend-item maintenance">Maintenance</span>
        <span class="legend-item checkin">Check-in Day</span>
        <span class="legend-item checkout">Check-out Day</span>
    </div>
</div>
```

---

## Technical Implementation Specifications

### 7. Backend Implementation

#### Models (No changes needed to existing models)

**Existing Models Used:**
- [Room](core/models/rooms.py:20) - Room information
- [RoomType](core/models/rooms.py:10) - Room categorization
- [Booking](core/models/booking.py:13) - Booking records
- [BookingDetail](core/models/booking.py:130) - Individual guest bookings
- [RoomMaintenance](core/models/rooms.py:50) - Maintenance schedules
- [Tariff](core/models/tariffs.py:10) - Tariff packages
- [PatientModel](core/models/patients.py) - Guest information

#### New Service Layer Function

**File:** `application/logus/services/room_availability_v2.py` (NEW)

```python
from datetime import date, timedelta
from typing import Dict, List, Any
from django.db.models import Q, Count, Case, When, IntegerField
from core.models.rooms import Room, RoomType, RoomMaintenance
from core.models.booking import Booking, BookingDetail
from core.models.patients import PatientModel

def get_availability_matrix_v2(
    start_date: date,
    end_date: date,
    room_type_id: int = None,
    include_inactive: bool = False
) -> Dict[str, Any]:
    """
    Generate comprehensive availability matrix for RM2 feature.

    Args:
        start_date: Period start date
        end_date: Period end date
        room_type_id: Optional filter for specific room type
        include_inactive: Include inactive rooms in results

    Returns:
        Dictionary with structure:
        {
            'period': {
                'start': date,
                'end': date,
                'days': [date1, date2, ...],
                'total_days': int
            },
            'statistics': {
                'total_rooms': int,
                'average_occupancy': float,
                'upcoming_checkins': int,
                'upcoming_checkouts': int,
                'maintenance_count': int
            },
            'room_types': [
                {
                    'id': int,
                    'name': str,
                    'total_rooms': int,
                    'active_rooms': int,
                    'daily_availability': [
                        {
                            'date': date,
                            'total': int,
                            'occupied': int,
                            'available': int,
                            'under_maintenance': int,
                            'occupancy_percentage': float
                        }
                    ],
                    'rooms': [
                        {
                            'id': int,
                            'name': str,
                            'capacity': int,
                            'price': int,
                            'is_active': bool,
                            'daily_status': [
                                {
                                    'date': date,
                                    'status': str,  # available|occupied|partial|maintenance|checkout|checkin
                                    'occupancy': {
                                        'current': int,
                                        'capacity': int,
                                        'percentage': float
                                    },
                                    'guests': [
                                        {
                                            'id': int,
                                            'full_name': str,
                                            'gender': str,
                                            'age': int,
                                            'booking_number': str,
                                            'booking_id': int,
                                            'booking_detail_id': int,
                                            'start_date': date,
                                            'end_date': date,
                                            'tariff_name': str,
                                            'is_checkin_day': bool,
                                            'is_checkout_day': bool
                                        }
                                    ],
                                    'maintenance': dict or None,
                                    'is_bookable': bool,
                                    'booking_conflicts': []
                                }
                            ]
                        }
                    ]
                }
            ]
        }
    """

    # Implementation steps:

    # 1. Generate date range
    days = []
    current_date = start_date
    while current_date <= end_date:
        days.append(current_date)
        current_date += timedelta(days=1)
    total_days = len(days)

    # 2. Get room types with filters
    room_types_query = RoomType.objects.all()
    if room_type_id:
        room_types_query = room_types_query.filter(id=room_type_id)

    # 3. For each room type, get rooms
    room_types_data = []
    for room_type in room_types_query:
        rooms_query = room_type.rooms.all()
        if not include_inactive:
            rooms_query = rooms_query.filter(is_active=True)

        # 4. For each room, calculate daily status
        rooms_data = []
        for room in rooms_query:
            daily_status = []

            for day in days:
                # Get bookings for this room on this day
                bookings = BookingDetail.objects.filter(
                    room=room,
                    booking__status__in=['pending', 'confirmed', 'checked_in', 'in_progress'],
                    start_date__lte=day,
                    end_date__gt=day
                ).select_related('booking', 'client', 'tariff')

                # Get maintenance records
                maintenance = RoomMaintenance.objects.filter(
                    room=room,
                    start_date__lte=day,
                    end_date__gt=day,
                    status__in=['scheduled', 'in_progress']
                ).first()

                # Calculate status
                current_occupancy = bookings.count()
                status = 'available'
                is_bookable = True

                if maintenance:
                    status = 'maintenance'
                    is_bookable = False
                elif current_occupancy == 0:
                    status = 'available'
                elif current_occupancy >= room.capacity:
                    status = 'occupied'
                    is_bookable = False
                else:
                    status = 'partial'

                # Check for check-in/check-out
                for booking in bookings:
                    if booking.start_date == day:
                        status = 'checkin'
                    elif booking.end_date == day:
                        status = 'checkout'

                # Build guest information
                guests = []
                for booking_detail in bookings:
                    patient = booking_detail.client
                    age = None
                    if patient.date_of_birth:
                        age = (day - patient.date_of_birth).days // 365

                    guests.append({
                        'id': patient.id,
                        'full_name': patient.get_full_name(),
                        'gender': patient.gender,
                        'age': age,
                        'booking_number': booking_detail.booking.booking_number,
                        'booking_id': booking_detail.booking.id,
                        'booking_detail_id': booking_detail.id,
                        'start_date': booking_detail.start_date,
                        'end_date': booking_detail.end_date,
                        'tariff_name': booking_detail.tariff.name if booking_detail.tariff else 'N/A',
                        'is_checkin_day': booking_detail.start_date == day,
                        'is_checkout_day': booking_detail.end_date == day
                    })

                daily_status.append({
                    'date': day,
                    'status': status,
                    'occupancy': {
                        'current': current_occupancy,
                        'capacity': room.capacity,
                        'percentage': (current_occupancy / room.capacity * 100) if room.capacity > 0 else 0
                    },
                    'guests': guests,
                    'maintenance': {
                        'type': maintenance.get_maintenance_type_display(),
                        'status': maintenance.get_status_display(),
                        'description': maintenance.description
                    } if maintenance else None,
                    'is_bookable': is_bookable,
                    'booking_conflicts': []  # Add conflict detection logic if needed
                })

            rooms_data.append({
                'id': room.id,
                'name': room.name,
                'capacity': room.capacity,
                'price': room.price,
                'is_active': room.is_active,
                'daily_status': daily_status
            })

        # 5. Aggregate daily availability for room type
        daily_availability = []
        for day in days:
            total = len(rooms_data)
            occupied = 0
            under_maintenance = 0

            for room_data in rooms_data:
                day_status = next((d for d in room_data['daily_status'] if d['date'] == day), None)
                if day_status:
                    if day_status['status'] == 'maintenance':
                        under_maintenance += 1
                    elif day_status['status'] in ['occupied', 'checkin']:
                        occupied += 1
                    elif day_status['status'] == 'partial':
                        # Count as partially occupied
                        occupied += 0.5

            available = total - occupied - under_maintenance
            occupancy_pct = (occupied / total * 100) if total > 0 else 0

            daily_availability.append({
                'date': day,
                'total': total,
                'occupied': int(occupied),
                'available': int(available),
                'under_maintenance': under_maintenance,
                'occupancy_percentage': occupancy_pct
            })

        room_types_data.append({
            'id': room_type.id,
            'name': room_type.name,
            'total_rooms': len(rooms_data),
            'active_rooms': len([r for r in rooms_data if r['is_active']]),
            'daily_availability': daily_availability,
            'rooms': rooms_data
        })

    # 6. Calculate overall statistics
    total_rooms = sum(rt['total_rooms'] for rt in room_types_data)

    # Calculate average occupancy
    total_occupancy = 0
    for rt in room_types_data:
        for day_data in rt['daily_availability']:
            total_occupancy += day_data['occupancy_percentage']
    avg_occupancy = total_occupancy / (len(room_types_data) * total_days) if room_types_data else 0

    # Upcoming check-ins/check-outs (next 24 hours)
    tomorrow = date.today() + timedelta(days=1)
    upcoming_checkins = BookingDetail.objects.filter(
        start_date__gte=date.today(),
        start_date__lt=tomorrow,
        booking__status__in=['confirmed', 'pending']
    ).count()

    upcoming_checkouts = BookingDetail.objects.filter(
        end_date__gte=date.today(),
        end_date__lt=tomorrow,
        booking__status__in=['checked_in', 'in_progress']
    ).count()

    # Current maintenance count
    maintenance_count = RoomMaintenance.objects.filter(
        start_date__lte=date.today(),
        end_date__gt=date.today(),
        status__in=['scheduled', 'in_progress']
    ).count()

    return {
        'period': {
            'start': start_date,
            'end': end_date,
            'days': days,
            'total_days': total_days
        },
        'statistics': {
            'total_rooms': total_rooms,
            'average_occupancy': round(avg_occupancy, 2),
            'upcoming_checkins': upcoming_checkins,
            'upcoming_checkouts': upcoming_checkouts,
            'maintenance_count': maintenance_count
        },
        'room_types': room_types_data
    }


def get_room_booking_timeline(
    room_id: int,
    start_date: date,
    end_date: date
) -> Dict[str, Any]:
    """
    Get detailed booking timeline for a specific room.
    Used for room detail modal/tooltip.

    Returns:
        {
            'room': {room info},
            'bookings': [list of bookings in period],
            'maintenance_periods': [list of maintenance],
            'daily_details': [day-by-day status]
        }
    """
    # Implementation similar to daily_status calculation above
    pass


def validate_booking_from_matrix(
    room_id: int,
    start_date: date,
    end_date: date,
    patient_id: int,
    tariff_id: int
) -> tuple[bool, str]:
    """
    Validate if a booking can be created from matrix selection.

    Returns:
        (is_valid, error_message)
    """
    from application.logus.utils.room_capacity import check_room_capacity

    # Check room exists and is active
    try:
        room = Room.objects.get(id=room_id, is_active=True)
    except Room.DoesNotExist:
        return False, "Room not found or inactive"

    # Check capacity
    has_capacity, current, available, msg = check_room_capacity(
        room=room,
        start_date=start_date,
        end_date=end_date,
        guests_to_add=1
    )

    if not has_capacity:
        return False, msg

    # Check maintenance conflicts
    from core.models.rooms import RoomMaintenance
    if RoomMaintenance.is_room_under_maintenance(room, start_date, end_date):
        return False, "Room is under maintenance during selected period"

    # Check patient exists
    try:
        PatientModel.objects.get(id=patient_id)
    except PatientModel.DoesNotExist:
        return False, "Patient not found"

    # Check tariff exists and is active
    from core.models.tariffs import Tariff
    try:
        Tariff.objects.get(id=tariff_id, is_active=True)
    except Tariff.DoesNotExist:
        return False, "Tariff not found or inactive"

    return True, "Validation successful"
```

#### New Views

**File:** `application/logus/views/room_availability_v2.py` (NEW)

```python
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from datetime import datetime, date, timedelta
from application.logus.services.room_availability_v2 import (
    get_availability_matrix_v2,
    get_room_booking_timeline,
    validate_booking_from_matrix
)

@login_required
def room_availability_matrix_v2_view(request):
    """
    Main view for RM2 feature.
    Renders the period x room types matrix interface.
    """
    # Get period from request or use defaults
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    room_type_id = request.GET.get('room_type_id')

    # Default period: today + 14 days
    if start_date_str and end_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%d.%m.%Y').date()
            end_date = datetime.strptime(end_date_str, '%d.%m.%Y').date()
        except ValueError:
            start_date = date.today()
            end_date = date.today() + timedelta(days=14)
    else:
        start_date = date.today()
        end_date = date.today() + timedelta(days=14)

    # Validate period
    if end_date <= start_date:
        end_date = start_date + timedelta(days=1)

    if (end_date - start_date).days > 90:
        # Limit to 90 days
        end_date = start_date + timedelta(days=90)

    # Get matrix data
    matrix_data = get_availability_matrix_v2(
        start_date=start_date,
        end_date=end_date,
        room_type_id=int(room_type_id) if room_type_id else None,
        include_inactive=False
    )

    # Get all room types for filter dropdown
    from core.models.rooms import RoomType
    all_room_types = RoomType.objects.all()

    context = {
        'matrix_data': matrix_data,
        'all_room_types': all_room_types,
        'selected_room_type_id': int(room_type_id) if room_type_id else None,
        'start_date': start_date,
        'end_date': end_date,
        'start_date_str': start_date.strftime('%d.%m.%Y'),
        'end_date_str': end_date.strftime('%d.%m.%Y'),
    }

    return render(request, 'logus/room_availability_v2/matrix.html', context)


@login_required
@require_http_methods(["GET"])
def get_room_details_ajax(request):
    """
    AJAX endpoint to get detailed room information for dropdown.
    Called when user clicks on a matrix cell.
    """
    room_type_id = request.GET.get('room_type_id')
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    selected_date_str = request.GET.get('selected_date')

    try:
        start_date = datetime.strptime(start_date_str, '%d.%m.%Y').date()
        end_date = datetime.strptime(end_date_str, '%d.%m.%Y').date()
        room_type_id = int(room_type_id)
    except (ValueError, TypeError):
        return JsonResponse({'error': 'Invalid parameters'}, status=400)

    # Get detailed data for all rooms of this type
    matrix_data = get_availability_matrix_v2(
        start_date=start_date,
        end_date=end_date,
        room_type_id=room_type_id,
        include_inactive=False
    )

    # Extract rooms data
    if matrix_data['room_types']:
        rooms_data = matrix_data['room_types'][0]['rooms']
    else:
        rooms_data = []

    return JsonResponse({
        'success': True,
        'rooms': rooms_data,
        'room_type_name': matrix_data['room_types'][0]['name'] if matrix_data['room_types'] else ''
    })


@login_required
@require_http_methods(["GET"])
def get_guest_details_ajax(request):
    """
    AJAX endpoint to get detailed guest information for tooltip.
    Called when user hovers over occupied cell.
    """
    booking_detail_id = request.GET.get('booking_detail_id')

    try:
        from core.models.booking import BookingDetail
        booking_detail = BookingDetail.objects.select_related(
            'booking', 'client', 'room', 'tariff'
        ).get(id=booking_detail_id)

        patient = booking_detail.client
        age = None
        if patient.date_of_birth:
            from datetime import date
            today = date.today()
            age = today.year - patient.date_of_birth.year
            if today.month < patient.date_of_birth.month or \
               (today.month == patient.date_of_birth.month and today.day < patient.date_of_birth.day):
                age -= 1

        return JsonResponse({
            'success': True,
            'guest': {
                'full_name': patient.get_full_name(),
                'gender': patient.get_gender_display(),
                'age': age,
                'booking_number': booking_detail.booking.booking_number,
                'booking_status': booking_detail.booking.get_status_display(),
                'start_date': booking_detail.start_date.strftime('%d.%m.%Y'),
                'end_date': booking_detail.end_date.strftime('%d.%m.%Y'),
                'tariff_name': booking_detail.tariff.name if booking_detail.tariff else 'N/A',
                'room_name': booking_detail.room.name,
                'room_type': booking_detail.room.room_type.name
            }
        })
    except BookingDetail.DoesNotExist:
        return JsonResponse({'error': 'Booking detail not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def quick_book_from_matrix(request):
    """
    Create a quick booking directly from matrix.
    """
    import json
    from django.db import transaction
    from core.models.booking import Booking, BookingDetail
    from core.models.rooms import Room
    from core.models.tariffs import Tariff
    from core.models.patients import PatientModel

    try:
        data = json.loads(request.body)
        room_id = data.get('room_id')
        start_date_str = data.get('start_date')
        end_date_str = data.get('end_date')
        patient_id = data.get('patient_id')
        tariff_id = data.get('tariff_id')

        # Parse dates
        start_date = datetime.strptime(start_date_str, '%d.%m.%Y').date()
        end_date = datetime.strptime(end_date_str, '%d.%m.%Y').date()

        # Validate
        is_valid, message = validate_booking_from_matrix(
            room_id=int(room_id),
            start_date=start_date,
            end_date=end_date,
            patient_id=int(patient_id),
            tariff_id=int(tariff_id)
        )

        if not is_valid:
            return JsonResponse({'error': message}, status=400)

        # Create booking
        with transaction.atomic():
            # Get objects
            room = Room.objects.get(id=room_id)
            patient = PatientModel.objects.get(id=patient_id)
            tariff = Tariff.objects.get(id=tariff_id)

            # Create Booking
            booking = Booking.objects.create(
                staff=request.user,
                start_date=datetime.combine(start_date, datetime.min.time()),
                end_date=datetime.combine(end_date, datetime.min.time()),
                status='confirmed',
                notes=f'Quick booking created from RM2 matrix'
            )

            # Create BookingDetail
            booking_detail = BookingDetail.objects.create(
                booking=booking,
                client=patient,
                room=room,
                tariff=tariff,
                price=tariff.price,
                start_date=start_date,
                end_date=end_date,
                is_current=True
            )

            # Initialize service session tracking
            from core.models.tariffs import TariffService, ServiceSessionTracking
            tariff_services = TariffService.objects.filter(tariff=tariff)
            for ts in tariff_services:
                ServiceSessionTracking.objects.create(
                    booking_detail=booking_detail,
                    service=ts.service,
                    tariff_service=ts,
                    sessions_included=ts.sessions_included,
                    sessions_used=0,
                    sessions_billed=0
                )

            # Log in history
            from core.models.booking import BookingHistory
            BookingHistory.log_change(
                booking=booking,
                action='CREATED',
                description=f'Quick booking created from RM2 matrix for room {room.name}',
                changed_by=request.user
            )

            return JsonResponse({
                'success': True,
                'booking_id': booking.id,
                'booking_number': booking.booking_number,
                'redirect_url': f'/booking/{booking.id}/'
            })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["GET"])
def export_matrix_excel(request):
    """
    Export availability matrix to Excel file.
    """
    # Implementation using openpyxl or xlsxwriter
    # Similar to existing report exports
    pass
```

#### URL Configuration

**File:** `application/logus/urls.py`

```python
# Add to urlpatterns:
from application.logus.views import room_availability_v2

urlpatterns = [
    # ... existing patterns ...

    # RM2 - Room Availability V2
    path('rooms/availability-v2/',
         room_availability_v2.room_availability_matrix_v2_view,
         name='room_availability_v2'),

    path('rooms/availability-v2/room-details/',
         room_availability_v2.get_room_details_ajax,
         name='room_details_ajax_v2'),

    path('rooms/availability-v2/guest-details/',
         room_availability_v2.get_guest_details_ajax,
         name='guest_details_ajax_v2'),

    path('rooms/availability-v2/quick-book/',
         room_availability_v2.quick_book_from_matrix,
         name='quick_book_from_matrix'),

    path('rooms/availability-v2/export-excel/',
         room_availability_v2.export_matrix_excel,
         name='export_matrix_excel_v2'),
]
```

---

### 8. Frontend Implementation

#### Main Template Structure

**File:** `application/templates/logus/room_availability_v2/matrix.html` (NEW)

```django
{% extends 'logus/base.html' %}
{% load static %}

{% block title %}Room Availability Matrix V2{% endblock %}

{% block extra_css %}
<link rel="stylesheet" href="{% static 'css/room_availability_v2.css' %}">
<style>
    /* Inline critical styles */
    .availability-matrix {
        overflow-x: auto;
        margin-top: 20px;
    }

    .matrix-table {
        width: 100%;
        border-collapse: collapse;
        white-space: nowrap;
    }

    .matrix-table th,
    .matrix-table td {
        padding: 10px;
        border: 1px solid #ddd;
        text-align: center;
    }

    .matrix-cell {
        cursor: pointer;
        transition: all 0.2s;
        min-width: 80px;
    }

    .matrix-cell:hover {
        transform: scale(1.05);
        box-shadow: 0 2px 8px rgba(0,0,0,0.2);
    }

    /* Occupancy color coding */
    .occupancy-high { background-color: #d4edda; } /* 0-40% - Green */
    .occupancy-medium { background-color: #fff3cd; } /* 41-75% - Yellow */
    .occupancy-low { background-color: #ffeaa7; } /* 76-99% - Orange */
    .occupancy-full { background-color: #f8d7da; } /* 100% - Red */
    .occupancy-inactive { background-color: #e9ecef; } /* Inactive - Gray */

    /* Room timeline styles */
    .room-timeline {
        display: flex;
        gap: 2px;
        margin: 10px 0;
    }

    .timeline-day {
        flex: 1;
        min-width: 30px;
        height: 40px;
        border: 1px solid #ccc;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 11px;
        cursor: pointer;
        position: relative;
    }

    .timeline-day.available { background-color: #28a745; color: white; }
    .timeline-day.occupied { background-color: #dc3545; color: white; }
    .timeline-day.partial {
        background: linear-gradient(135deg, #28a745 50%, #ffc107 50%);
        color: white;
    }
    .timeline-day.maintenance { background-color: #6c757d; color: white; }
    .timeline-day.checkin { background-color: #17a2b8; color: white; }
    .timeline-day.checkout { background-color: #20c997; color: white; }

    /* Dropdown styles */
    .room-details-dropdown {
        background: white;
        border: 1px solid #ddd;
        border-radius: 8px;
        padding: 20px;
        margin: 10px 0;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }

    .room-item {
        border: 1px solid #e0e0e0;
        border-radius: 6px;
        padding: 15px;
        margin-bottom: 15px;
        background: #fafafa;
    }

    /* Statistics cards */
    .availability-statistics {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 15px;
        margin-bottom: 20px;
    }

    .stat-card {
        background: white;
        padding: 20px;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        text-align: center;
    }

    .stat-value {
        font-size: 2em;
        font-weight: bold;
        color: #007bff;
        margin: 10px 0;
    }
</style>
{% endblock %}

{% block content %}
<div class="container-fluid">
    <div class="page-header">
        <h1>Room Availability Matrix V2 (RM2)</h1>
        <p class="text-muted">Visual room availability and occupancy management</p>
    </div>

    <!-- Period Selector -->
    <div class="period-selector card mb-3">
        <div class="card-body">
            <form method="GET" action="{% url 'room_availability_v2' %}" id="periodForm">
                <div class="row align-items-end">
                    <div class="col-md-3">
                        <label for="start_date">Start Date</label>
                        <input type="text"
                               class="form-control datepicker"
                               id="start_date"
                               name="start_date"
                               value="{{ start_date_str }}"
                               placeholder="DD.MM.YYYY"
                               required>
                    </div>

                    <div class="col-md-3">
                        <label for="end_date">End Date</label>
                        <input type="text"
                               class="form-control datepicker"
                               id="end_date"
                               name="end_date"
                               value="{{ end_date_str }}"
                               placeholder="DD.MM.YYYY"
                               required>
                    </div>

                    <div class="col-md-3">
                        <label for="room_type_id">Room Type (Optional)</label>
                        <select class="form-control" id="room_type_id" name="room_type_id">
                            <option value="">All Types</option>
                            {% for rt in all_room_types %}
                            <option value="{{ rt.id }}" {% if rt.id == selected_room_type_id %}selected{% endif %}>
                                {{ rt.name }}
                            </option>
                            {% endfor %}
                        </select>
                    </div>

                    <div class="col-md-3">
                        <button type="submit" class="btn btn-primary btn-block">
                            <i class="fas fa-search"></i> Search
                        </button>
                    </div>
                </div>

                <div class="quick-periods mt-3">
                    <label>Quick Select:</label>
                    <div class="btn-group" role="group">
                        <button type="button" class="btn btn-sm btn-outline-secondary" data-days="0">Today</button>
                        <button type="button" class="btn btn-sm btn-outline-secondary" data-days="7">7 Days</button>
                        <button type="button" class="btn btn-sm btn-outline-secondary" data-days="14">14 Days</button>
                        <button type="button" class="btn btn-sm btn-outline-secondary" data-days="30">30 Days</button>
                    </div>
                </div>
            </form>
        </div>
    </div>

    <!-- Statistics Panel -->
    <div class="availability-statistics">
        <div class="stat-card">
            <h5>Total Rooms</h5>
            <div class="stat-value">{{ matrix_data.statistics.total_rooms }}</div>
            <small>active rooms</small>
        </div>

        <div class="stat-card">
            <h5>Avg Occupancy</h5>
            <div class="stat-value">{{ matrix_data.statistics.average_occupancy }}%</div>
            <small>for selected period</small>
        </div>

        <div class="stat-card">
            <h5>Check-ins Today</h5>
            <div class="stat-value">{{ matrix_data.statistics.upcoming_checkins }}</div>
            <small>in next 24 hours</small>
        </div>

        <div class="stat-card">
            <h5>Check-outs Today</h5>
            <div class="stat-value">{{ matrix_data.statistics.upcoming_checkouts }}</div>
            <small>in next 24 hours</small>
        </div>

        <div class="stat-card">
            <h5>Maintenance</h5>
            <div class="stat-value">{{ matrix_data.statistics.maintenance_count }}</div>
            <small>rooms under maintenance</small>
        </div>
    </div>

    <!-- Legend -->
    <div class="availability-legend card mb-3">
        <div class="card-body">
            <h6>Status Legend:</h6>
            <div class="legend-items d-flex flex-wrap gap-3">
                <span class="badge badge-success">0-40% (High Availability)</span>
                <span class="badge badge-warning">41-75% (Moderate)</span>
                <span class="badge" style="background-color: #ffc107;">76-99% (Low Availability)</span>
                <span class="badge badge-danger">100% (Fully Booked)</span>
                <span class="badge badge-secondary">Under Maintenance</span>
            </div>
        </div>
    </div>

    <!-- Main Matrix -->
    <div class="availability-matrix card">
        <div class="card-body">
            <div class="d-flex justify-content-between align-items-center mb-3">
                <h5 class="mb-0">Availability Matrix</h5>
                <div>
                    <button class="btn btn-sm btn-success" onclick="location.reload();">
                        <i class="fas fa-sync"></i> Refresh
                    </button>
                    <a href="{% url 'logus:export_matrix_excel_v2' %}?start_date={{ start_date_str }}&end_date={{ end_date_str }}"
                       class="btn btn-sm btn-info">
                        <i class="fas fa-file-excel"></i> Export Excel
                    </a>
                </div>
            </div>

            <div class="table-responsive">
                <table class="matrix-table">
                    <thead>
                        <tr>
                            <th class="sticky-col">Room Type</th>
                            {% for day in matrix_data.period.days %}
                            <th>
                                {{ day|date:"d.m" }}<br>
                                <small>{{ day|date:"D" }}</small>
                            </th>
                            {% endfor %}
                        </tr>
                    </thead>
                    <tbody>
                        {% for room_type in matrix_data.room_types %}
                        <tr>
                            <td class="sticky-col">
                                <strong>{{ room_type.name }}</strong><br>
                                <small>{{ room_type.total_rooms }} rooms</small>
                            </td>

                            {% for day_data in room_type.daily_availability %}
                            <td class="matrix-cell
                                {% if day_data.occupancy_percentage <= 40 %}occupancy-high
                                {% elif day_data.occupancy_percentage <= 75 %}occupancy-medium
                                {% elif day_data.occupancy_percentage < 100 %}occupancy-low
                                {% elif day_data.occupancy_percentage == 100 %}occupancy-full
                                {% else %}occupancy-inactive{% endif %}"
                                data-room-type-id="{{ room_type.id }}"
                                data-date="{{ day_data.date|date:'d.m.Y' }}"
                                onclick="showRoomDetails({{ room_type.id }}, '{{ day_data.date|date:'d.m.Y' }}')">

                                <div class="occupancy-fraction">
                                    {{ day_data.occupied }}/{{ day_data.total }}
                                </div>

                                {% if day_data.under_maintenance > 0 %}
                                <div class="maintenance-badge">
                                    <i class="fas fa-wrench"></i> {{ day_data.under_maintenance }}
                                </div>
                                {% endif %}

                                <div class="occupancy-percent" style="font-size: 0.8em; color: #666;">
                                    {{ day_data.occupancy_percentage|floatformat:0 }}%
                                </div>
                            </td>
                            {% endfor %}
                        </tr>

                        <!-- Room Details Dropdown (initially hidden) -->
                        <tr id="room-details-{{ room_type.id }}" class="room-details-row" style="display: none;">
                            <td colspan="{{ matrix_data.period.total_days|add:1 }}">
                                <div class="room-details-dropdown">
                                    <div class="d-flex justify-content-between align-items-center mb-3">
                                        <h5>{{ room_type.name }} - Individual Rooms</h5>
                                        <button class="btn btn-sm btn-secondary" onclick="hideRoomDetails({{ room_type.id }})">
                                            <i class="fas fa-times"></i> Close
                                        </button>
                                    </div>

                                    <div id="room-details-content-{{ room_type.id }}">
                                        <!-- AJAX content loaded here -->
                                        <div class="text-center">
                                            <div class="spinner-border" role="status">
                                                <span class="sr-only">Loading...</span>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</div>

<!-- Guest Details Modal -->
<div class="modal fade" id="guestDetailsModal" tabindex="-1">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">Guest Details</h5>
                <button type="button" class="close" data-dismiss="modal">
                    <span>&times;</span>
                </button>
            </div>
            <div class="modal-body" id="guestDetailsContent">
                <!-- AJAX content loaded here -->
            </div>
        </div>
    </div>
</div>

<!-- Quick Booking Modal -->
<div class="modal fade" id="quickBookingModal" tabindex="-1">
    <div class="modal-dialog modal-lg">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">Quick Booking</h5>
                <button type="button" class="close" data-dismiss="modal">
                    <span>&times;</span>
                </button>
            </div>
            <div class="modal-body">
                <form id="quickBookingForm">
                    {% csrf_token %}
                    <input type="hidden" id="quick_room_id" name="room_id">

                    <div class="form-group">
                        <label>Period</label>
                        <div class="row">
                            <div class="col-md-6">
                                <input type="text" class="form-control datepicker"
                                       id="quick_start_date" name="start_date"
                                       placeholder="DD.MM.YYYY" required>
                            </div>
                            <div class="col-md-6">
                                <input type="text" class="form-control datepicker"
                                       id="quick_end_date" name="end_date"
                                       placeholder="DD.MM.YYYY" required>
                            </div>
                        </div>
                    </div>

                    <div class="form-group">
                        <label>Patient</label>
                        <select class="form-control select2" id="quick_patient_id"
                                name="patient_id" required>
                            <option value="">Search patient...</option>
                        </select>
                    </div>

                    <div class="form-group">
                        <label>Tariff Package</label>
                        <select class="form-control" id="quick_tariff_id"
                                name="tariff_id" required>
                            <option value="">Select tariff...</option>
                            <!-- Populated dynamically -->
                        </select>
                    </div>

                    <div class="form-group">
                        <label>Notes (Optional)</label>
                        <textarea class="form-control" name="notes" rows="3"></textarea>
                    </div>
                </form>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-dismiss="modal">Cancel</button>
                <button type="button" class="btn btn-primary" onclick="submitQuickBooking()">
                    Create Booking
                </button>
                <a href="#" id="fullBookingFormLink" class="btn btn-info">
                    Use Full Booking Form
                </a>
            </div>
        </div>
    </div>
</div>
{% endblock %}

{% block extra_js %}
<script src="{% static 'js/room_availability_v2.js' %}"></script>
<script>
    // Initialize datepickers
    $(document).ready(function() {
        $('.datepicker').datepicker({
            format: 'dd.mm.yyyy',
            autoclose: true,
            todayHighlight: true
        });

        // Quick period buttons
        $('.quick-periods button').click(function() {
            const days = parseInt($(this).data('days'));
            const today = new Date();
            const endDate = new Date();
            endDate.setDate(today.getDate() + days);

            $('#start_date').val(formatDate(today));
            $('#end_date').val(formatDate(endDate));
        });

        // Initialize Select2 for patient search
        $('#quick_patient_id').select2({
            ajax: {
                url: '/api/patients/search/',  // Existing patient search endpoint
                dataType: 'json',
                delay: 250,
                processResults: function(data) {
                    return {
                        results: data.results.map(p => ({
                            id: p.id,
                            text: `${p.full_name} (${p.id_number})`
                        }))
                    };
                }
            },
            minimumInputLength: 2
        });
    });

    function formatDate(date) {
        const day = String(date.getDate()).padStart(2, '0');
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const year = date.getFullYear();
        return `${day}.${month}.${year}`;
    }

    function showRoomDetails(roomTypeId, date) {
        const detailsRow = $(`#room-details-${roomTypeId}`);
        const contentDiv = $(`#room-details-content-${roomTypeId}`);

        // Toggle visibility
        if (detailsRow.is(':visible')) {
            detailsRow.hide();
            return;
        }

        // Hide other open dropdowns
        $('.room-details-row').hide();

        // Show this dropdown
        detailsRow.show();

        // Load room details via AJAX
        $.ajax({
            url: '{% url "room_details_ajax_v2" %}',
            data: {
                room_type_id: roomTypeId,
                start_date: '{{ start_date_str }}',
                end_date: '{{ end_date_str }}',
                selected_date: date
            },
            success: function(response) {
                if (response.success) {
                    renderRoomDetails(contentDiv, response.rooms, '{{ start_date_str }}', '{{ end_date_str }}');
                } else {
                    contentDiv.html(`<div class="alert alert-danger">${response.error}</div>`);
                }
            },
            error: function() {
                contentDiv.html('<div class="alert alert-danger">Error loading room details</div>');
            }
        });
    }

    function hideRoomDetails(roomTypeId) {
        $(`#room-details-${roomTypeId}`).hide();
    }

    function renderRoomDetails(container, rooms, startDate, endDate) {
        let html = '<div class="rooms-list">';

        rooms.forEach(room => {
            html += `
                <div class="room-item">
                    <div class="room-info mb-2">
                        <strong>${room.name}</strong>
                        <span class="badge badge-secondary ml-2">Capacity: ${room.capacity}</span>
                        <span class="badge badge-info ml-2">₸${room.price}/day</span>
                        ${!room.is_active ? '<span class="badge badge-danger ml-2">Inactive</span>' : ''}
                    </div>

                    <div class="room-timeline">
                        ${renderTimeline(room.daily_status)}
                    </div>

                    <div class="room-actions mt-2">
                        <button class="btn btn-sm btn-primary" onclick="openQuickBooking(${room.id}, '${startDate}', '${endDate}')">
                            <i class="fas fa-calendar-plus"></i> Book This Room
                        </button>
                        <button class="btn btn-sm btn-secondary" onclick="viewRoomDetails(${room.id})">
                            <i class="fas fa-info-circle"></i> View Details
                        </button>
                    </div>
                </div>
            `;
        });

        html += '</div>';
        container.html(html);
    }

    function renderTimeline(dailyStatus) {
        let html = '';

        dailyStatus.forEach(day => {
            const statusClass = day.status;
            const tooltipContent = getTooltipContent(day);

            html += `
                <div class="timeline-day ${statusClass}"
                     data-toggle="tooltip"
                     title="${tooltipContent}"
                     onclick="showDayDetails(${JSON.stringify(day).replace(/"/g, '&quot;')})">
                    ${day.date.split('-')[2]}
                </div>
            `;
        });

        return html;
    }

    function getTooltipContent(day) {
        let content = `${day.date}\n`;
        content += `Status: ${day.status}\n`;
        content += `Occupancy: ${day.occupancy.current}/${day.occupancy.capacity}\n`;

        if (day.guests.length > 0) {
            content += 'Guests:\n';
            day.guests.forEach(guest => {
                content += `- ${guest.full_name} (${guest.gender}, ${guest.age}y)\n`;
            });
        }

        if (day.maintenance) {
            content += `Maintenance: ${day.maintenance.type}\n`;
        }

        return content;
    }

    function showDayDetails(dayData) {
        // Show modal with detailed day information
        if (dayData.guests.length > 0) {
            const guestId = dayData.guests[0].booking_detail_id;
            showGuestDetails(guestId);
        } else if (dayData.maintenance) {
            alert(`Maintenance: ${dayData.maintenance.description}`);
        } else {
            // Available day - could trigger booking
            alert('This day is available for booking');
        }
    }

    function showGuestDetails(bookingDetailId) {
        $.ajax({
            url: '{% url "guest_details_ajax_v2" %}',
            data: { booking_detail_id: bookingDetailId },
            success: function(response) {
                if (response.success) {
                    const guest = response.guest;
                    const html = `
                        <table class="table table-bordered">
                            <tr><th>Name</th><td>${guest.full_name}</td></tr>
                            <tr><th>Gender</th><td>${guest.gender}</td></tr>
                            <tr><th>Age</th><td>${guest.age} years</td></tr>
                            <tr><th>Booking</th><td>${guest.booking_number}</td></tr>
                            <tr><th>Status</th><td>${guest.booking_status}</td></tr>
                            <tr><th>Period</th><td>${guest.start_date} - ${guest.end_date}</td></tr>
                            <tr><th>Tariff</th><td>${guest.tariff_name}</td></tr>
                            <tr><th>Room</th><td>${guest.room_name} (${guest.room_type})</td></tr>
                        </table>
                    `;
                    $('#guestDetailsContent').html(html);
                    $('#guestDetailsModal').modal('show');
                }
            }
        });
    }

    function openQuickBooking(roomId, startDate, endDate) {
        $('#quick_room_id').val(roomId);
        $('#quick_start_date').val(startDate);
        $('#quick_end_date').val(endDate);

        // Update full booking form link
        $('#fullBookingFormLink').attr('href',
            `/booking/start/?room_id=${roomId}&start_date=${startDate}&end_date=${endDate}`);

        // Load active tariffs
        $.ajax({
            url: '/api/tariffs/active/',
            success: function(tariffs) {
                const select = $('#quick_tariff_id');
                select.empty().append('<option value="">Select tariff...</option>');
                tariffs.forEach(t => {
                    select.append(`<option value="${t.id}">${t.name} - ₸${t.price}/day</option>`);
                });
            }
        });

        $('#quickBookingModal').modal('show');
    }

    function submitQuickBooking() {
        const formData = {
            room_id: $('#quick_room_id').val(),
            start_date: $('#quick_start_date').val(),
            end_date: $('#quick_end_date').val(),
            patient_id: $('#quick_patient_id').val(),
            tariff_id: $('#quick_tariff_id').val()
        };

        $.ajax({
            url: '{% url "quick_book_from_matrix" %}',
            method: 'POST',
            headers: {
                'X-CSRFToken': $('[name=csrfmiddlewaretoken]').val()
            },
            contentType: 'application/json',
            data: JSON.stringify(formData),
            success: function(response) {
                if (response.success) {
                    alert(`Booking created successfully: ${response.booking_number}`);
                    window.location.href = response.redirect_url;
                } else {
                    alert(`Error: ${response.error}`);
                }
            },
            error: function(xhr) {
                const error = xhr.responseJSON?.error || 'Unknown error occurred';
                alert(`Error: ${error}`);
            }
        });
    }

    function viewRoomDetails(roomId) {
        window.open(`/rooms/${roomId}/`, '_blank');
    }
</script>
{% endblock %}
```

---

### 9. CSS Styling

**File:** `application/static/css/room_availability_v2.css` (NEW)

```css
/* Room Availability V2 Styles */

/* Period Selector */
.period-selector {
    background: #f8f9fa;
    border-radius: 8px;
    padding: 20px;
}

.quick-periods {
    margin-top: 15px;
}

/* Statistics Panel */
.availability-statistics {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 20px;
    margin-bottom: 30px;
}

.stat-card {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 25px;
    border-radius: 12px;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    text-align: center;
    transition: transform 0.2s;
}

.stat-card:hover {
    transform: translateY(-5px);
}

.stat-card h5 {
    font-size: 0.9em;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 10px;
    opacity: 0.9;
}

.stat-value {
    font-size: 3em;
    font-weight: bold;
    margin: 15px 0;
    text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
}

.stat-card small {
    font-size: 0.85em;
    opacity: 0.8;
}

/* Different color schemes for stat cards */
.stat-card:nth-child(1) { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
.stat-card:nth-child(2) { background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); }
.stat-card:nth-child(3) { background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); }
.stat-card:nth-child(4) { background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); }
.stat-card:nth-child(5) { background: linear-gradient(135deg, #fa709a 0%, #fee140 100%); }

/* Legend */
.availability-legend {
    background: white;
    border-radius: 8px;
    padding: 15px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}

.legend-items {
    display: flex;
    flex-wrap: wrap;
    gap: 15px;
}

.legend-items .badge {
    padding: 8px 15px;
    font-size: 0.9em;
}

/* Matrix Table */
.availability-matrix {
    background: white;
    border-radius: 12px;
    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    overflow: hidden;
}

.table-responsive {
    overflow-x: auto;
    max-height: 70vh;
}

.matrix-table {
    width: 100%;
    border-collapse: separate;
    border-spacing: 0;
}

.matrix-table thead {
    position: sticky;
    top: 0;
    background: #343a40;
    color: white;
    z-index: 10;
}

.matrix-table th {
    padding: 15px 10px;
    text-align: center;
    font-weight: 600;
    border: 1px solid #454d55;
    white-space: nowrap;
}

.matrix-table td {
    padding: 12px 8px;
    text-align: center;
    border: 1px solid #dee2e6;
    min-width: 90px;
}

.sticky-col {
    position: sticky;
    left: 0;
    background: white;
    z-index: 5;
    font-weight: 600;
}

.matrix-table thead .sticky-col {
    background: #343a40;
    z-index: 15;
}

.matrix-cell {
    cursor: pointer;
    transition: all 0.3s ease;
    position: relative;
}

.matrix-cell:hover {
    transform: scale(1.08);
    box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    z-index: 3;
}

/* Occupancy Colors */
.occupancy-high {
    background-color: #d4edda;
    color: #155724;
}

.occupancy-medium {
    background-color: #fff3cd;
    color: #856404;
}

.occupancy-low {
    background-color: #ffe5a1;
    color: #664d03;
}

.occupancy-full {
    background-color: #f8d7da;
    color: #721c24;
}

.occupancy-inactive {
    background-color: #e9ecef;
    color: #6c757d;
}

.occupancy-fraction {
    font-size: 1.1em;
    font-weight: bold;
}

.occupancy-percent {
    font-size: 0.75em;
    color: #6c757d;
    margin-top: 2px;
}

.maintenance-badge {
    position: absolute;
    top: 2px;
    right: 2px;
    background: #6c757d;
    color: white;
    border-radius: 50%;
    width: 20px;
    height: 20px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.7em;
}

/* Room Details Dropdown */
.room-details-row {
    background: #f8f9fa;
}

.room-details-dropdown {
    background: white;
    border: 2px solid #007bff;
    border-radius: 12px;
    padding: 25px;
    margin: 15px;
    box-shadow: 0 6px 16px rgba(0,0,0,0.15);
    animation: slideDown 0.3s ease;
}

@keyframes slideDown {
    from {
        opacity: 0;
        transform: translateY(-20px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

.rooms-list {
    max-height: 500px;
    overflow-y: auto;
}

.room-item {
    background: #fafafa;
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    padding: 20px;
    margin-bottom: 20px;
    transition: all 0.2s;
}

.room-item:hover {
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    transform: translateX(5px);
}

.room-info {
    display: flex;
    align-items: center;
    gap: 15px;
    margin-bottom: 15px;
}

.room-info strong {
    font-size: 1.2em;
    color: #343a40;
}

/* Room Timeline */
.room-timeline {
    display: flex;
    gap: 3px;
    margin: 15px 0;
    padding: 10px;
    background: #f0f0f0;
    border-radius: 6px;
    overflow-x: auto;
}

.timeline-day {
    flex: 1;
    min-width: 35px;
    height: 50px;
    border: 2px solid #fff;
    border-radius: 4px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    font-size: 0.75em;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s;
    position: relative;
}

.timeline-day:hover {
    transform: scale(1.1);
    z-index: 2;
    box-shadow: 0 3px 8px rgba(0,0,0,0.3);
}

/* Timeline Status Colors */
.timeline-day.available {
    background-color: #28a745;
    color: white;
}

.timeline-day.occupied {
    background-color: #dc3545;
    color: white;
}

.timeline-day.partial {
    background: linear-gradient(135deg, #28a745 50%, #ffc107 50%);
    color: white;
}

.timeline-day.maintenance {
    background-color: #6c757d;
    color: white;
}

.timeline-day.checkin {
    background-color: #17a2b8;
    color: white;
}

.timeline-day.checkin::before {
    content: '→';
    position: absolute;
    top: 2px;
    right: 2px;
    font-size: 0.8em;
}

.timeline-day.checkout {
    background-color: #20c997;
    color: white;
}

.timeline-day.checkout::before {
    content: '←';
    position: absolute;
    top: 2px;
    left: 2px;
    font-size: 0.8em;
}

/* Room Actions */
.room-actions {
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
}

/* Modal Styles */
.modal-dialog {
    max-width: 600px;
}

.modal-lg {
    max-width: 900px;
}

/* Quick Booking Form */
#quickBookingForm .form-group {
    margin-bottom: 20px;
}

/* Guest Details Table */
#guestDetailsContent table {
    margin-bottom: 0;
}

#guestDetailsContent th {
    width: 150px;
    background: #f8f9fa;
    font-weight: 600;
}

/* Responsive Adjustments */
@media (max-width: 768px) {
    .availability-statistics {
        grid-template-columns: 1fr;
    }

    .stat-card {
        padding: 15px;
    }

    .stat-value {
        font-size: 2em;
    }

    .matrix-table th,
    .matrix-table td {
        padding: 8px 5px;
        font-size: 0.85em;
        min-width: 70px;
    }

    .room-timeline {
        overflow-x: scroll;
    }

    .timeline-day {
        min-width: 30px;
        height: 40px;
        font-size: 0.7em;
    }
}

/* Print Styles */
@media print {
    .period-selector,
    .room-actions,
    .btn,
    .modal {
        display: none !important;
    }

    .availability-matrix {
        box-shadow: none;
    }

    .matrix-table {
        border: 1px solid #000;
    }

    .matrix-cell:hover {
        transform: none;
        box-shadow: none;
    }
}
```

---

### 10. JavaScript Implementation

**File:** `application/static/js/room_availability_v2.js` (NEW)

```javascript
/**
 * Room Availability V2 (RM2) JavaScript
 * Handles matrix interactions, AJAX calls, and UI updates
 */

class RoomAvailabilityMatrix {
    constructor() {
        this.currentRoomTypeExpanded = null;
        this.dateFormat = 'DD.MM.YYYY';
        this.init();
    }

    init() {
        console.log('Initializing Room Availability Matrix V2');
        this.setupEventListeners();
        this.initializeDatePickers();
        this.initializeTooltips();
    }

    setupEventListeners() {
        // Quick period buttons
        document.querySelectorAll('.quick-periods button').forEach(btn => {
            btn.addEventListener('click', (e) => this.handleQuickPeriod(e));
        });

        // Matrix cell clicks are handled inline via onclick
        // But we can add additional event delegation here if needed
    }

    initializeDatePickers() {
        if (typeof $.fn.datepicker !== 'undefined') {
            $('.datepicker').datepicker({
                format: 'dd.mm.yyyy',
                autoclose: true,
                todayHighlight: true,
                startDate: new Date()
            });
        }
    }

    initializeTooltips() {
        if (typeof $.fn.tooltip !== 'undefined') {
            $('[data-toggle="tooltip"]').tooltip({
                html: true,
                trigger: 'hover'
            });
        }
    }

    handleQuickPeriod(event) {
        const days = parseInt(event.target.dataset.days);
        const today = new Date();
        const endDate = new Date();

        if (days === 0) {
            // Today only
            endDate.setDate(today.getDate());
        } else {
            endDate.setDate(today.getDate() + days);
        }

        document.getElementById('start_date').value = this.formatDate(today);
        document.getElementById('end_date').value = this.formatDate(endDate);
    }

    formatDate(date) {
        const day = String(date.getDate()).padStart(2, '0');
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const year = date.getFullYear();
        return `${day}.${month}.${year}`;
    }

    showRoomDetails(roomTypeId, selectedDate) {
        const detailsRow = document.getElementById(`room-details-${roomTypeId}`);
        const contentDiv = document.getElementById(`room-details-content-${roomTypeId}`);

        // Toggle visibility
        if (detailsRow.style.display === 'table-row') {
            this.hideRoomDetails(roomTypeId);
            return;
        }

        // Hide other open dropdowns
        document.querySelectorAll('.room-details-row').forEach(row => {
            row.style.display = 'none';
        });

        // Show this dropdown
        detailsRow.style.display = 'table-row';
        this.currentRoomTypeExpanded = roomTypeId;

        // Load room details via AJAX
        this.loadRoomDetails(roomTypeId, selectedDate, contentDiv);
    }

    hideRoomDetails(roomTypeId) {
        const detailsRow = document.getElementById(`room-details-${roomTypeId}`);
        detailsRow.style.display = 'none';
        this.currentRoomTypeExpanded = null;
    }

    loadRoomDetails(roomTypeId, selectedDate, container) {
        const startDate = document.getElementById('start_date')?.value || '';
        const endDate = document.getElementById('end_date')?.value || '';

        // Show loading spinner
        container.innerHTML = `
            <div class="text-center py-4">
                <div class="spinner-border text-primary" role="status">
                    <span class="sr-only">Loading...</span>
                </div>
                <p class="mt-2">Loading room details...</p>
            </div>
        `;

        fetch(`/rooms/availability-v2/room-details/?room_type_id=${roomTypeId}&start_date=${startDate}&end_date=${endDate}&selected_date=${selectedDate}`)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    this.renderRoomDetails(container, data.rooms, data.room_type_name, startDate, endDate);
                } else {
                    container.innerHTML = `<div class="alert alert-danger">${data.error || 'Failed to load room details'}</div>`;
                }
            })
            .catch(error => {
                console.error('Error loading room details:', error);
                container.innerHTML = '<div class="alert alert-danger">Error loading room details. Please try again.</div>';
            });
    }

    renderRoomDetails(container, rooms, roomTypeName, startDate, endDate) {
        if (!rooms || rooms.length === 0) {
            container.innerHTML = '<div class="alert alert-info">No rooms found for this type.</div>';
            return;
        }

        let html = `
            <div class="rooms-list-header mb-3">
                <h6>${roomTypeName} - ${rooms.length} rooms</h6>
                <p class="text-muted">Period: ${startDate} to ${endDate}</p>
            </div>
            <div class="rooms-list">
        `;

        rooms.forEach(room => {
            html += this.renderRoomItem(room, startDate, endDate);
        });

        html += '</div>';
        container.innerHTML = html;

        // Reinitialize tooltips for new content
        this.initializeTooltips();
    }

    renderRoomItem(room, startDate, endDate) {
        const activeClass = room.is_active ? '' : 'opacity-50';
        const inactiveBadge = room.is_active ? '' : '<span class="badge badge-danger ml-2">Inactive</span>';

        return `
            <div class="room-item ${activeClass}">
                <div class="room-info mb-3">
                    <strong>${room.name}</strong>
                    <span class="badge badge-secondary ml-2">
                        <i class="fas fa-users"></i> ${room.capacity}
                    </span>
                    <span class="badge badge-info ml-2">
                        <i class="fas fa-money-bill-wave"></i> ₸${room.price.toLocaleString()}/day
                    </span>
                    ${inactiveBadge}
                </div>

                <div class="room-timeline-wrapper">
                    <div class="room-timeline">
                        ${this.renderTimeline(room.daily_status)}
                    </div>
                </div>

                <div class="room-actions mt-3">
                    ${room.is_active ? `
                        <button class="btn btn-sm btn-primary" onclick="roomMatrix.openQuickBooking(${room.id}, '${startDate}', '${endDate}', '${room.name}')">
                            <i class="fas fa-calendar-plus"></i> Book This Room
                        </button>
                    ` : ''}
                    <button class="btn btn-sm btn-secondary" onclick="roomMatrix.viewRoomDetails(${room.id})">
                        <i class="fas fa-info-circle"></i> View Details
                    </button>
                </div>
            </div>
        `;
    }

    renderTimeline(dailyStatus) {
        let html = '';

        dailyStatus.forEach(day => {
            const statusClass = day.status;
            const dateObj = new Date(day.date);
            const dayNumber = dateObj.getDate();
            const tooltipContent = this.getTooltipContent(day);
            const guestsInfo = day.guests.length > 0 ? `<span class="guest-count">${day.guests.length}</span>` : '';

            html += `
                <div class="timeline-day ${statusClass}"
                     data-toggle="tooltip"
                     data-placement="top"
                     data-html="true"
                     title="${this.escapeHtml(tooltipContent)}"
                     onclick='roomMatrix.showDayDetails(${JSON.stringify(day)})'>
                    <span class="day-number">${dayNumber}</span>
                    ${guestsInfo}
                </div>
            `;
        });

        return html;
    }

    getTooltipContent(day) {
        let content = `<strong>${day.date}</strong><br>`;
        content += `Status: ${this.getStatusLabel(day.status)}<br>`;
        content += `Occupancy: ${day.occupancy.current}/${day.occupancy.capacity} (${day.occupancy.percentage.toFixed(0)}%)<br>`;

        if (day.guests && day.guests.length > 0) {
            content += '<br><strong>Guests:</strong><br>';
            day.guests.forEach((guest, index) => {
                if (index < 3) { // Limit to 3 guests in tooltip
                    content += `• ${guest.full_name} (${guest.gender}, ${guest.age}y)<br>`;
                }
            });
            if (day.guests.length > 3) {
                content += `• ...and ${day.guests.length - 3} more<br>`;
            }
        }

        if (day.maintenance) {
            content += `<br><strong>Maintenance:</strong> ${day.maintenance.type}<br>`;
        }

        if (day.is_bookable) {
            content += '<br><em>Click to book</em>';
        }

        return content;
    }

    getStatusLabel(status) {
        const labels = {
            'available': 'Available',
            'occupied': 'Fully Occupied',
            'partial': 'Partially Available',
            'maintenance': 'Under Maintenance',
            'checkin': 'Check-in Day',
            'checkout': 'Check-out Day'
        };
        return labels[status] || status;
    }

    showDayDetails(dayData) {
        console.log('Day details:', dayData);

        if (dayData.guests && dayData.guests.length > 0) {
            // Show guest details modal
            this.showGuestDetails(dayData.guests[0].booking_detail_id);
        } else if (dayData.maintenance) {
            // Show maintenance alert
            this.showAlert('Maintenance', dayData.maintenance.description, 'info');
        } else if (dayData.is_bookable) {
            // Could trigger booking flow
            this.showAlert('Available', 'This room is available for this day. Click "Book This Room" button to create a booking.', 'success');
        }
    }

    showGuestDetails(bookingDetailId) {
        fetch(`/rooms/availability-v2/guest-details/?booking_detail_id=${bookingDetailId}`)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    const guest = data.guest;
                    const html = `
                        <table class="table table-bordered">
                            <tr><th>Name</th><td>${guest.full_name}</td></tr>
                            <tr><th>Gender</th><td>${guest.gender}</td></tr>
                            <tr><th>Age</th><td>${guest.age || 'N/A'} years</td></tr>
                            <tr><th>Booking</th><td>${guest.booking_number}</td></tr>
                            <tr><th>Status</th><td><span class="badge badge-info">${guest.booking_status}</span></td></tr>
                            <tr><th>Period</th><td>${guest.start_date} - ${guest.end_date}</td></tr>
                            <tr><th>Tariff</th><td>${guest.tariff_name}</td></tr>
                            <tr><th>Room</th><td>${guest.room_name} (${guest.room_type})</td></tr>
                        </table>
                        <div class="mt-3">
                            <a href="/booking/${data.guest.booking_number}/" class="btn btn-primary" target="_blank">
                                View Full Booking
                            </a>
                        </div>
                    `;
                    document.getElementById('guestDetailsContent').innerHTML = html;
                    $('#guestDetailsModal').modal('show');
                } else {
                    this.showAlert('Error', data.error || 'Failed to load guest details', 'danger');
                }
            })
            .catch(error => {
                console.error('Error loading guest details:', error);
                this.showAlert('Error', 'Failed to load guest details', 'danger');
            });
    }

    openQuickBooking(roomId, startDate, endDate, roomName) {
        document.getElementById('quick_room_id').value = roomId;
        document.getElementById('quick_start_date').value = startDate;
        document.getElementById('quick_end_date').value = endDate;
        document.querySelector('#quickBookingModal .modal-title').textContent = `Quick Booking - ${roomName}`;

        // Update full booking form link
        const fullFormLink = document.getElementById('fullBookingFormLink');
        fullFormLink.href = `/booking/start/?room_id=${roomId}&start_date=${startDate}&end_date=${endDate}`;

        // Load active tariffs
        this.loadActiveTariffs();

        // Show modal
        $('#quickBookingModal').modal('show');
    }

    loadActiveTariffs() {
        fetch('/api/tariffs/active/')
            .then(response => response.json())
            .then(tariffs => {
                const select = document.getElementById('quick_tariff_id');
                select.innerHTML = '<option value="">Select tariff...</option>';

                tariffs.forEach(tariff => {
                    const option = document.createElement('option');
                    option.value = tariff.id;
                    option.textContent = `${tariff.name} - ₸${tariff.price.toLocaleString()}/day`;
                    select.appendChild(option);
                });
            })
            .catch(error => {
                console.error('Error loading tariffs:', error);
                this.showAlert('Error', 'Failed to load tariffs', 'danger');
            });
    }

    submitQuickBooking() {
        const formData = {
            room_id: document.getElementById('quick_room_id').value,
            start_date: document.getElementById('quick_start_date').value,
            end_date: document.getElementById('quick_end_date').value,
            patient_id: document.getElementById('quick_patient_id').value,
            tariff_id: document.getElementById('quick_tariff_id').value
        };

        // Validate
        if (!formData.patient_id) {
            this.showAlert('Validation Error', 'Please select a patient', 'warning');
            return;
        }

        if (!formData.tariff_id) {
            this.showAlert('Validation Error', 'Please select a tariff', 'warning');
            return;
        }

        // Show loading
        const submitBtn = document.querySelector('#quickBookingModal .btn-primary');
        const originalText = submitBtn.innerHTML;
        submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm mr-2"></span>Creating...';
        submitBtn.disabled = true;

        // Get CSRF token
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

        fetch('/rooms/availability-v2/quick-book/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify(formData)
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                this.showAlert('Success', `Booking created successfully: ${data.booking_number}`, 'success');
                setTimeout(() => {
                    window.location.href = data.redirect_url;
                }, 1500);
            } else {
                throw new Error(data.error || 'Failed to create booking');
            }
        })
        .catch(error => {
            console.error('Error creating booking:', error);
            this.showAlert('Error', error.message, 'danger');
            submitBtn.innerHTML = originalText;
            submitBtn.disabled = false;
        });
    }

    viewRoomDetails(roomId) {
        window.open(`/rooms/${roomId}/`, '_blank');
    }

    showAlert(title, message, type = 'info') {
        // Use Bootstrap alerts or custom notification system
        alert(`${title}: ${message}`);
    }

    escapeHtml(text) {
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return text.replace(/[&<>"']/g, m => map[m]);
    }

    refreshMatrix() {
        location.reload();
    }
}

// Initialize on page load
let roomMatrix;
document.addEventListener('DOMContentLoaded', function() {
    roomMatrix = new RoomAvailabilityMatrix();
});

// Global functions for inline onclick handlers
function showRoomDetails(roomTypeId, date) {
    roomMatrix.showRoomDetails(roomTypeId, date);
}

function hideRoomDetails(roomTypeId) {
    roomMatrix.hideRoomDetails(roomTypeId);
}

function submitQuickBooking() {
    roomMatrix.submitQuickBooking();
}
```

---

## Testing Requirements

### 11. Test Cases

#### Unit Tests

**File:** `application/logus/tests/test_room_availability_v2.py` (NEW)

```python
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from datetime import date, timedelta
from core.models.rooms import Room, RoomType, RoomMaintenance
from core.models.booking import Booking, BookingDetail
from core.models.tariffs import Tariff
from core.models.patients import PatientModel
from application.logus.services.room_availability_v2 import (
    get_availability_matrix_v2,
    validate_booking_from_matrix
)

class RoomAvailabilityV2TestCase(TestCase):
    def setUp(self):
        # Create test data
        self.user = get_user_model().objects.create_user(
            username='testuser',
            password='testpass123'
        )

        self.room_type = RoomType.objects.create(
            name='Standard',
            description='Standard room'
        )

        self.room = Room.objects.create(
            name='101',
            room_type=self.room_type,
            capacity=2,
            price=15000,
            is_active=True
        )

        self.tariff = Tariff.objects.create(
            name='Basic Package',
            price=20000,
            is_active=True
        )

        self.patient = PatientModel.objects.create(
            first_name='Test',
            last_name='Patient',
            date_of_birth=date(1980, 1, 1),
            gender='M'
        )

    def test_availability_matrix_generation(self):
        """Test that availability matrix generates correctly"""
        start_date = date.today()
        end_date = start_date + timedelta(days=7)

        matrix = get_availability_matrix_v2(start_date, end_date)

        self.assertIn('period', matrix)
        self.assertIn('statistics', matrix)
        self.assertIn('room_types', matrix)
        self.assertEqual(len(matrix['period']['days']), 8)  # 7 days + start day

    def test_occupied_room_detection(self):
        """Test that occupied rooms are correctly identified"""
        start_date = date.today()
        end_date = start_date + timedelta(days=3)

        # Create a booking
        booking = Booking.objects.create(
            staff=self.user,
            start_date=start_date,
            end_date=end_date,
            status='confirmed'
        )

        BookingDetail.objects.create(
            booking=booking,
            client=self.patient,
            room=self.room,
            tariff=self.tariff,
            price=self.tariff.price,
            start_date=start_date,
            end_date=end_date,
            is_current=True
        )

        matrix = get_availability_matrix_v2(start_date, end_date)

        # Check that room is marked as occupied
        room_type_data = matrix['room_types'][0]
        self.assertEqual(room_type_data['daily_availability'][0]['occupied'], 1)

    def test_maintenance_blocking(self):
        """Test that maintenance periods block availability"""
        start_date = date.today()
        end_date = start_date + timedelta(days=3)

        RoomMaintenance.objects.create(
            room=self.room,
            maintenance_type='ROUTINE',
            status='scheduled',
            start_date=start_date,
            end_date=end_date,
            description='Test maintenance'
        )

        matrix = get_availability_matrix_v2(start_date, end_date)

        # Check that room is marked as under maintenance
        room_data = matrix['room_types'][0]['rooms'][0]
        self.assertEqual(room_data['daily_status'][0]['status'], 'maintenance')
        self.assertFalse(room_data['daily_status'][0]['is_bookable'])

    def test_capacity_tracking(self):
        """Test that partial occupancy is tracked correctly"""
        # Room has capacity 2
        start_date = date.today()
        end_date = start_date + timedelta(days=2)

        # Add one guest (room should be partial)
        booking = Booking.objects.create(
            staff=self.user,
            start_date=start_date,
            end_date=end_date,
            status='confirmed'
        )

        BookingDetail.objects.create(
            booking=booking,
            client=self.patient,
            room=self.room,
            tariff=self.tariff,
            price=self.tariff.price,
            start_date=start_date,
            end_date=end_date,
            is_current=True
        )

        matrix = get_availability_matrix_v2(start_date, end_date)

        room_data = matrix['room_types'][0]['rooms'][0]
        day_status = room_data['daily_status'][0]

        self.assertEqual(day_status['status'], 'partial')
        self.assertEqual(day_status['occupancy']['current'], 1)
        self.assertEqual(day_status['occupancy']['capacity'], 2)
        self.assertTrue(day_status['is_bookable'])

    def test_booking_validation(self):
        """Test booking validation from matrix"""
        start_date = date.today()
        end_date = start_date + timedelta(days=2)

        is_valid, message = validate_booking_from_matrix(
            room_id=self.room.id,
            start_date=start_date,
            end_date=end_date,
            patient_id=self.patient.id,
            tariff_id=self.tariff.id
        )

        self.assertTrue(is_valid)
        self.assertEqual(message, 'Validation successful')

    def test_view_access_requires_login(self):
        """Test that views require authentication"""
        client = Client()
        response = client.get('/rooms/availability-v2/')
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_ajax_room_details(self):
        """Test AJAX endpoint for room details"""
        client = Client()
        client.login(username='testuser', password='testpass123')

        start_date = date.today()
        end_date = start_date + timedelta(days=7)

        response = client.get('/rooms/availability-v2/room-details/', {
            'room_type_id': self.room_type.id,
            'start_date': start_date.strftime('%d.%m.%Y'),
            'end_date': end_date.strftime('%d.%m.%Y')
        })

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('rooms', data)

# Add more test cases as needed
```

#### Integration Tests

1. **Full booking flow from matrix**
   - Select period → Click cell → View rooms → Book room → Verify booking created

2. **Multi-guest booking**
   - Test partial occupancy scenarios
   - Verify capacity limits enforced

3. **Maintenance integration**
   - Create maintenance → Verify room blocked in matrix
   - Complete maintenance → Verify room available again

4. **Concurrent bookings**
   - Test race conditions when multiple users book simultaneously

#### Manual Testing Checklist

- [ ] Period selection with all quick shortcuts
- [ ] Matrix displays correctly for various date ranges
- [ ] Color coding matches occupancy levels
- [ ] Clicking cells expands room dropdown
- [ ] Timeline visualization shows all status types
- [ ] Hover tooltips display correct information
- [ ] Guest details modal shows complete information
- [ ] Quick booking form validates inputs
- [ ] Quick booking creates proper booking records
- [ ] Full booking form link pre-fills correctly
- [ ] Statistics panel shows accurate counts
- [ ] Export to Excel works
- [ ] Responsive design on mobile devices
- [ ] Print view is formatted correctly

---

## Migration and Deployment

### 12. Deployment Steps

#### Phase 1: Backend Development
1. Create service layer function `get_availability_matrix_v2()`
2. Create view functions in `room_availability_v2.py`
3. Add URL patterns
4. Write unit tests
5. Test in development environment

#### Phase 2: Frontend Development
1. Create HTML template `matrix.html`
2. Create CSS file `room_availability_v2.css`
3. Create JavaScript file `room_availability_v2.js`
4. Integrate with existing Bootstrap/jQuery
5. Test UI interactions

#### Phase 3: Integration
1. Link from existing menu/navigation
2. Test with real data
3. Performance testing with large datasets
4. Fix any bugs

#### Phase 4: User Training
1. Create user documentation
2. Record video tutorial
3. Train staff on new interface
4. Gather feedback

#### Phase 5: Go Live
1. Deploy to production
2. Monitor for issues
3. Collect user feedback
4. Iterate improvements

### Navigation Integration

**Add to main menu:**

```html
<!-- In application/templates/logus/base.html or navigation template -->
<li class="nav-item">
    <a class="nav-link" href="{% url 'room_availability_v2' %}">
        <i class="fas fa-th"></i>
        <span>Room Availability V2</span>
        <span class="badge badge-success ml-2">New</span>
    </a>
</li>
```

---

## Performance Considerations

### 13. Optimization Strategies

1. **Database Query Optimization**
   - Use `select_related()` and `prefetch_related()` for foreign keys
   - Add database indexes on frequently queried fields
   - Cache matrix data for short periods (5-10 minutes)

2. **Frontend Performance**
   - Lazy load room details (only when dropdown opened)
   - Paginate or virtualize long room lists
   - Debounce AJAX calls
   - Use CSS transitions instead of JavaScript animations

3. **Caching Strategy**
   ```python
   from django.core.cache import cache

   cache_key = f'room_matrix_{start_date}_{end_date}_{room_type_id}'
   matrix_data = cache.get(cache_key)

   if not matrix_data:
       matrix_data = get_availability_matrix_v2(...)
       cache.set(cache_key, matrix_data, 600)  # 10 minutes
   ```

4. **Limit Date Range**
   - Maximum 90 days to prevent excessive data loading
   - Warn users if selecting > 30 days
   - Suggest narrowing search for better performance

---

## Future Enhancements

### 14. Possible V3 Features

1. **Drag-and-Drop Booking**
   - Drag patient from list onto timeline to create booking
   - Drag booking between rooms to reassign

2. **Real-Time Updates**
   - WebSocket integration for live updates
   - Multiple users see changes instantly

3. **Advanced Filtering**
   - Filter by patient gender
   - Filter by tariff type
   - Filter by price range
   - Filter by room amenities

4. **Booking Templates**
   - Save common booking patterns
   - Quick-apply templates

5. **Waitlist Integration**
   - Show waitlist entries on matrix
   - Auto-suggest available slots for waitlist patients

6. **Mobile App**
   - Native iOS/Android app
   - Push notifications for changes

7. **AI-Powered Suggestions**
   - Recommend optimal room assignments
   - Predict occupancy patterns
   - Suggest pricing adjustments

---

## Acceptance Criteria

### 15. Definition of Done

The RM2 feature is considered complete when:

- ✅ User can select a date period (min 1 day, max 90 days)
- ✅ Matrix displays room types × daily availability
- ✅ Cells show occupancy fraction (e.g., "5/10")
- ✅ Color coding reflects occupancy percentage
- ✅ Clicking a cell expands dropdown showing individual rooms
- ✅ Each room shows timeline visualization for the period
- ✅ Timeline days are color-coded by status (available/occupied/partial/maintenance)
- ✅ Occupied days show guest information (name, gender, age)
- ✅ Partial occupancy is clearly indicated
- ✅ Maintenance periods block booking
- ✅ User can click "Book" to create booking from matrix
- ✅ Quick booking modal allows fast booking creation
- ✅ Alternative link to full booking form is provided
- ✅ All AJAX endpoints return proper error handling
- ✅ Unit tests achieve >80% code coverage
- ✅ Integration tests pass
- ✅ Manual testing checklist completed
- ✅ User documentation created
- ✅ Performance is acceptable (<3s page load, <1s AJAX responses)
- ✅ Responsive design works on tablets and mobile
- ✅ Accessibility standards met (WCAG 2.1 Level AA)
- ✅ Code reviewed and approved
- ✅ Deployed to production
- ✅ User training completed

---

## Support and Maintenance

### 16. Ongoing Tasks

1. **Monitor Performance**
   - Track page load times
   - Monitor database query counts
   - Optimize slow queries

2. **User Feedback**
   - Collect feedback from staff
   - Prioritize feature requests
   - Fix bugs promptly

3. **Data Cleanup**
   - Archive old bookings periodically
   - Clean up cancelled bookings
   - Maintain data integrity

4. **Documentation Updates**
   - Keep user guide current
   - Update technical documentation
   - Record known issues and workarounds

---

## Contact and Resources

**Developer:** [Your Name]
**Email:** [your.email@example.com]
**Project Repository:** [GitHub URL]
**Documentation:** [Wiki URL]
**Issue Tracker:** [Issues URL]

---

## Appendix

### File Reference Map

```
HayatMedicalCRM/
├── core/models/
│   ├── rooms.py                    # Room, RoomType, RoomMaintenance models
│   ├── booking.py                  # Booking, BookingDetail models
│   ├── tariffs.py                  # Tariff models
│   └── patients.py                 # PatientModel
│
├── application/logus/
│   ├── services/
│   │   └── room_availability_v2.py # NEW - Matrix service functions
│   ├── utils/
│   │   └── room_capacity.py        # Capacity validation utilities
│   ├── views/
│   │   └── room_availability_v2.py # NEW - Matrix views
│   ├── forms/
│   │   └── booking.py              # Existing booking forms
│   └── urls.py                     # URL routing (add RM2 patterns)
│
├── application/templates/logus/
│   └── room_availability_v2/
│       └── matrix.html             # NEW - Main matrix template
│
├── application/static/
│   ├── css/
│   │   └── room_availability_v2.css # NEW - RM2 styles
│   └── js/
│       └── room_availability_v2.js  # NEW - RM2 JavaScript
│
└── application/logus/tests/
    └── test_room_availability_v2.py # NEW - Test cases
```

### Related Documentation

- [Existing Booking Flow Documentation]
- [Room Management Guide]
- [Tariff Configuration Manual]
- [Database Schema Documentation]
- [API Endpoints Reference]

---

**END OF FEATURE SPECIFICATION: RM2 - ROOM AVAILABILITY V2**

*This document is a comprehensive guide for implementing the Room Availability Matrix V2 feature. Follow the specifications carefully and update this document as the implementation evolves.*
