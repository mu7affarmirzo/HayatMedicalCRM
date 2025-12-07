# Cashbox Module - Workflow Diagrams

**Visual Guide to Billing Processes**

---

## 1. Complete Billing Workflow

```
┌─────────────────────────────────────────────────────────────────────┐
│                     BOOKING LIFECYCLE → BILLING                      │
└─────────────────────────────────────────────────────────────────────┘

STEP 1: Booking Creation
┌──────────────────┐
│ Create Booking   │
│ - Add patients   │
│ - Assign rooms   │
│ - Set tariffs    │
│ Status: PENDING  │
└────────┬─────────┘
         │
         ▼
STEP 2: Check-in
┌──────────────────────────┐
│ Update status:           │
│ PENDING → CHECKED_IN     │
│                          │
│ Signal triggers:         │
│ ✓ Create IllnessHistory  │
│   for each patient       │
└────────┬─────────────────┘
         │
         ▼
STEP 3: Active Stay
┌──────────────────────────┐
│ During stay:             │
│ - Provide services       │
│ - Prescribe medications  │
│ - Order lab tests        │
│ - Can change tariffs     │
│ Status: IN_PROGRESS      │
└────────┬─────────────────┘
         │
         ▼
STEP 4: Discharge
┌──────────────────────────┐
│ Update status:           │
│ IN_PROGRESS → DISCHARGED │
│                          │
│ Booking now billable     │
└────────┬─────────────────┘
         │
         ▼
STEP 5: Cashbox Processing
┌──────────────────────────────────────────┐
│ Cashbox Dashboard                        │
│                                          │
│ ┌──────────────────────────────────────┐ │
│ │ Billing List View                    │ │
│ │ - Shows all billable bookings        │ │
│ │ - Filter by status, date, patient    │ │
│ │ - Shows billing status badge         │ │
│ └──────────────────────────────────────┘ │
└────────┬─────────────────────────────────┘
         │
         ▼
STEP 6: View Billing Detail
┌──────────────────────────────────────────┐
│ Billing Detail View                      │
│                                          │
│ Auto-creates BookingBilling if missing:  │
│ ┌──────────────────────────────────────┐ │
│ │ BookingBilling                       │ │
│ │ Status: PENDING                      │ │
│ │ Tariff Base: 0                       │ │
│ │ Services: 0                          │ │
│ │ Medications: 0                       │ │
│ │ Labs: 0                              │ │
│ │ Total: 0                             │ │
│ └──────────────────────────────────────┘ │
│                                          │
│ Shows:                                   │
│ - Booking information                    │
│ - All patients & rooms                   │
│ - All tariff periods (if changed)        │
│ - Additional services                    │
│ - Medications                            │
│ - Lab tests                              │
│ - Procedures                             │
│                                          │
│ Available action: [Calculate Billing]    │
└────────┬─────────────────────────────────┘
         │
         ▼
STEP 7: Calculate Billing
┌──────────────────────────────────────────┐
│ calculate_billing_amounts()              │
│                                          │
│ Calculates:                              │
│ 1. Tariff Base Amount                    │
│    = Sum of all BookingDetail prices     │
│                                          │
│ 2. Additional Services                   │
│    = Sum of ServiceUsage prices          │
│                                          │
│ 3. Medications (⚠️ TODO)                 │
│    = Sum of (quantity × unit_price)      │
│                                          │
│ 4. Lab Research (⚠️ TODO)                │
│    = Sum of lab test prices              │
│                                          │
│ 5. Total = (1) + (2) + (3) + (4)         │
│                                          │
│ Updates BookingBilling:                  │
│ Status: PENDING → CALCULATED             │
└────────┬─────────────────────────────────┘
         │
         ▼
STEP 8: Review & Invoice
┌──────────────────────────────────────────┐
│ Billing Detail View (refreshed)         │
│                                          │
│ ┌──────────────────────────────────────┐ │
│ │ BookingBilling                       │ │
│ │ Status: CALCULATED                   │ │
│ │ Tariff Base: 1,500,000 UZS           │ │
│ │ Services: 250,000 UZS                │ │
│ │ Medications: 80,000 UZS              │ │
│ │ Labs: 120,000 UZS                    │ │
│ │ Total: 1,950,000 UZS                 │ │
│ └──────────────────────────────────────┘ │
│                                          │
│ Available actions:                       │
│ [Recalculate] [Mark as Invoiced]         │
└────────┬─────────────────────────────────┘
         │
         ▼
STEP 9: Mark as Invoiced
┌──────────────────────────────────────────┐
│ Updates BookingBilling:                  │
│ Status: CALCULATED → INVOICED            │
│                                          │
│ Invoice generated (future feature)       │
└────────┬─────────────────────────────────┘
         │
         ▼
STEP 10: Accept Payment (⚠️ TODO - Backend)
┌──────────────────────────────────────────┐
│ Payment Acceptance (Not Implemented)     │
│                                          │
│ Planned features:                        │
│ 1. Validate amount matches total         │
│ 2. Select payment method                 │
│    - Cash                                │
│    - Card (Humo/Uzcard)                  │
│    - Online (PayMe/Click)                │
│ 3. Create TransactionsModel record       │
│ 4. Update status: INVOICED → PAID        │
│ 5. Generate receipt                      │
└────────┬─────────────────────────────────┘
         │
         ▼
┌──────────────────┐
│ ✓ COMPLETED      │
│ Billing cycle    │
│ finished         │
└──────────────────┘
```

---

## 2. Tariff Change Workflow

```
┌─────────────────────────────────────────────────────────────────────┐
│                    TARIFF CHANGE DURING STAY                         │
└─────────────────────────────────────────────────────────────────────┘

Initial State
┌────────────────────────────────────────┐
│ Booking #BK-20251207-1234              │
│ Patient: Ivan Ivanov                   │
│ Period: Dec 1 - Dec 10 (10 days)       │
│                                        │
│ BookingDetail #1:                      │
│ - Tariff: Basic (500,000 UZS)          │
│ - Room: 101 (Standard)                 │
│ - effective_from: Dec 1                │
│ - effective_to: NULL                   │
│ - is_current: TRUE                     │
└────────────────────────────────────────┘
         │
         │ Patient requests upgrade on Dec 5
         ▼
Call BookingDetail.change_tariff()
┌────────────────────────────────────────┐
│ Input:                                 │
│ - booking: BK-20251207-1234            │
│ - client: Ivan Ivanov                  │
│ - new_tariff: Premium                  │
│ - new_room: 102 (Deluxe)               │
│ - change_datetime: Dec 5, 00:00        │
└────────┬───────────────────────────────┘
         │
         ▼
Step 1: Close Current Detail
┌────────────────────────────────────────┐
│ Update BookingDetail #1:               │
│ - effective_to: Dec 5, 00:00           │
│ - is_current: FALSE                    │
│                                        │
│ Period 1: Dec 1 - Dec 5 (5 days)       │
│ Tariff: Basic                          │
└────────┬───────────────────────────────┘
         │
         ▼
Step 2: Create New Detail
┌────────────────────────────────────────┐
│ Create BookingDetail #2:               │
│ - Tariff: Premium (1,000,000 UZS)      │
│ - Room: 102 (Deluxe)                   │
│ - effective_from: Dec 5, 00:00         │
│ - effective_to: NULL                   │
│ - is_current: TRUE                     │
│ - start_date: Dec 1 (preserved)        │
│ - end_date: Dec 10 (preserved)         │
│                                        │
│ Period 2: Dec 5 - Dec 10 (6 days)      │
│ Tariff: Premium                        │
└────────┬───────────────────────────────┘
         │
         ▼
Final State: Two Periods
┌────────────────────────────────────────┐
│ Booking #BK-20251207-1234              │
│ Patient: Ivan Ivanov                   │
│ Total: 10 days                         │
│                                        │
│ ┌────────────────────────────────────┐ │
│ │ Period 1 (BookingDetail #1)       │ │
│ │ Dec 1 - Dec 5 (5 days)             │ │
│ │ Tariff: Basic                      │ │
│ │ Room: 101 (Standard)               │ │
│ │ is_current: FALSE                  │ │
│ └────────────────────────────────────┘ │
│                                        │
│ ┌────────────────────────────────────┐ │
│ │ Period 2 (BookingDetail #2)       │ │
│ │ Dec 5 - Dec 10 (6 days)            │ │
│ │ Tariff: Premium                    │ │
│ │ Room: 102 (Deluxe)                 │ │
│ │ is_current: TRUE                   │ │
│ └────────────────────────────────────┘ │
└────────────────────────────────────────┘
         │
         ▼
Billing Calculation
┌────────────────────────────────────────┐
│ calculate_booking_billing()            │
│                                        │
│ Period 1: 5 days                       │
│ Price: 500,000 UZS                     │
│ Prorated: (500,000 / 10) × 5           │
│         = 250,000 UZS                  │
│                                        │
│ Period 2: 6 days                       │
│ Price: 1,000,000 UZS                   │
│ Prorated: (1,000,000 / 10) × 6         │
│         = 600,000 UZS                  │
│                                        │
│ Total Tariff Charges: 850,000 UZS      │
└────────────────────────────────────────┘
```

---

## 3. Service Session Billing

```
┌─────────────────────────────────────────────────────────────────────┐
│              SERVICE SESSION TRACKING & BILLING                      │
└─────────────────────────────────────────────────────────────────────┘

Setup: Tariff with Included Services
┌────────────────────────────────────────┐
│ Tariff: Basic (500,000 UZS)            │
│                                        │
│ Included Services:                     │
│ - Massage: 5 sessions                  │
│ - Physiotherapy: 10 sessions           │
└────────────────────────────────────────┘
         │
         ▼
BookingDetail Created
┌────────────────────────────────────────┐
│ BookingDetail.save()                   │
│                                        │
│ Signal triggers:                       │
│ _initialize_service_tracking()         │
│                                        │
│ Creates ServiceSessionTracking:        │
│                                        │
│ ┌────────────────────────────────────┐ │
│ │ Service: Massage                   │ │
│ │ sessions_included: 5               │ │
│ │ sessions_used: 0                   │ │
│ │ sessions_billed: 0                 │ │
│ └────────────────────────────────────┘ │
│                                        │
│ ┌────────────────────────────────────┐ │
│ │ Service: Physiotherapy             │ │
│ │ sessions_included: 10              │ │
│ │ sessions_used: 0                   │ │
│ │ sessions_billed: 0                 │ │
│ └────────────────────────────────────┘ │
└────────────────────────────────────────┘
         │
         ▼
During Stay: Service Sessions Completed
┌────────────────────────────────────────┐
│ IndividualProcedureSessionModel        │
│                                        │
│ Day 1: Massage session completed       │
│ Day 2: Massage session completed       │
│ Day 3: Massage session completed       │
│ Day 4: Massage session completed       │
│ Day 5: Massage session completed       │
│ Day 6: Massage session completed ✗     │
│       (exceeds included)               │
│ Day 7: Massage session completed ✗     │
│       (exceeds included)               │
│                                        │
│ Updates ServiceSessionTracking:        │
│ ┌────────────────────────────────────┐ │
│ │ Service: Massage                   │ │
│ │ sessions_included: 5               │ │
│ │ sessions_used: 7                   │ │
│ │ sessions_billed: 2                 │ │
│ │ sessions_exceeded: 2 (property)    │ │
│ └────────────────────────────────────┘ │
└────────────────────────────────────────┘
         │
         ▼
Billing Calculation
┌────────────────────────────────────────┐
│ For each ServiceSessionTracking:       │
│                                        │
│ Query IndividualProcedureSessionModel: │
│ - Filter by booking_detail             │
│ - Filter by service                    │
│ - Filter is_billable = TRUE            │
│                                        │
│ Sum billed_amount:                     │
│ Session 6: 50,000 UZS                  │
│ Session 7: 50,000 UZS                  │
│ Total: 100,000 UZS                     │
│                                        │
│ Add to period.total_service_charges    │
└────────────────────────────────────────┘
```

---

## 4. Multiple Patient Billing

```
┌─────────────────────────────────────────────────────────────────────┐
│                 MULTI-PATIENT BOOKING BILLING                        │
└─────────────────────────────────────────────────────────────────────┘

Booking Setup
┌────────────────────────────────────────────────────────────────────┐
│ Booking #BK-20251207-5678                                          │
│ Period: Dec 1 - Dec 7 (7 days)                                     │
│                                                                    │
│ Patient 1: Ivan Ivanov                                             │
│ ┌────────────────────────────────────────────────────────────────┐ │
│ │ BookingDetail #1                                               │ │
│ │ Tariff: Basic (500,000 UZS)                                    │ │
│ │ Room: 101 (Standard)                                           │ │
│ │ Price: 500,000 UZS                                             │ │
│ └────────────────────────────────────────────────────────────────┘ │
│                                                                    │
│ Patient 2: Maria Petrova                                           │
│ ┌────────────────────────────────────────────────────────────────┐ │
│ │ BookingDetail #2                                               │ │
│ │ Tariff: Premium (1,000,000 UZS)                                │ │
│ │ Room: 102 (Deluxe)                                             │ │
│ │ Price: 1,000,000 UZS                                           │ │
│ └────────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────┘
         │
         ▼
During Stay: Individual Services
┌────────────────────────────────────────────────────────────────────┐
│ Patient 1 Services:                                                │
│ - Basic tariff includes 5 massage                                  │
│ - Used 8 massage (3 extra)                                         │
│ - Extra cost: 3 × 50,000 = 150,000 UZS                             │
│                                                                    │
│ Patient 2 Services:                                                │
│ - Premium tariff includes 10 massage                               │
│ - Used 12 massage (2 extra)                                        │
│ - Extra cost: 2 × 50,000 = 100,000 UZS                             │
│                                                                    │
│ Total Additional Services: 250,000 UZS                             │
└────────────────────────────────────────────────────────────────────┘
         │
         ▼
Billing Calculation
┌────────────────────────────────────────────────────────────────────┐
│ calculate_booking_billing()                                        │
│                                                                    │
│ Processes BookingDetails sequentially:                             │
│                                                                    │
│ Period 1 (Patient 1):                                              │
│ ┌────────────────────────────────────────────────────────────────┐ │
│ │ Tariff: Basic                                                  │ │
│ │ Room: 101 (Standard)                                           │ │
│ │ Days: 7                                                        │ │
│ │ Tariff Base: 500,000 UZS                                       │ │
│ │ Service Charges: 150,000 UZS (3 extra massage)                 │ │
│ │ Period Total: 650,000 UZS                                      │ │
│ └────────────────────────────────────────────────────────────────┘ │
│                                                                    │
│ Period 2 (Patient 2):                                              │
│ ┌────────────────────────────────────────────────────────────────┐ │
│ │ Tariff: Premium                                                │ │
│ │ Room: 102 (Deluxe)                                             │ │
│ │ Days: 7                                                        │ │
│ │ Tariff Base: 1,000,000 UZS                                     │ │
│ │ Service Charges: 100,000 UZS (2 extra massage)                 │ │
│ │ Period Total: 1,100,000 UZS                                    │ │
│ └────────────────────────────────────────────────────────────────┘ │
│                                                                    │
│ ┌────────────────────────────────────────────────────────────────┐ │
│ │ TOTAL BREAKDOWN                                                │ │
│ │ Total Tariff Charges: 1,500,000 UZS                            │ │
│ │ Total Service Charges: 250,000 UZS                             │ │
│ │ Medications: 0 UZS (TODO)                                      │ │
│ │ Lab Research: 0 UZS (TODO)                                     │ │
│ │ ─────────────────────────────────────                          │ │
│ │ GRAND TOTAL: 1,750,000 UZS                                     │ │
│ └────────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────┘
         │
         ▼
Update BookingBilling
┌────────────────────────────────────────┐
│ BookingBilling record:                 │
│ tariff_base_amount: 1,500,000          │
│ additional_services_amount: 250,000    │
│ medications_amount: 0                  │
│ lab_research_amount: 0                 │
│ total_amount: 1,750,000                │
│ billing_status: CALCULATED             │
└────────────────────────────────────────┘
```

---

## 5. Database Query Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                    BILLING DETAIL VIEW QUERIES                       │
└─────────────────────────────────────────────────────────────────────┘

Request: GET /application/cashbox/billing/123/
         │
         ▼
┌────────────────────────────────────────┐
│ Query 1: Get Booking                   │
│                                        │
│ SELECT * FROM booking                  │
│ WHERE id = 123                         │
│                                        │
│ Result: 1 row                          │
└────────┬───────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────┐
│ Query 2: Get/Create BookingBilling     │
│                                        │
│ SELECT * FROM booking_billing          │
│ WHERE booking_id = 123                 │
│                                        │
│ If not exists:                         │
│ INSERT INTO booking_billing (...)      │
│                                        │
│ Result: 1 row                          │
└────────┬───────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────┐
│ Query 3: Get BookingDetails            │
│                                        │
│ SELECT bd.*, c.*, r.*, rt.*, t.*       │
│ FROM booking_detail bd                 │
│ JOIN patient c ON bd.client_id = c.id  │
│ JOIN room r ON bd.room_id = r.id       │
│ JOIN room_type rt ON r.room_type = rt.id │
│ JOIN tariff t ON bd.tariff_id = t.id   │
│ WHERE bd.booking_id = 123              │
│                                        │
│ Result: N rows (1 per patient period)  │
└────────┬───────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────┐
│ Query 4: Get TariffServices            │
│                                        │
│ SELECT ts.*, s.*                       │
│ FROM tariff_service ts                 │
│ JOIN service s ON ts.service_id = s.id │
│ WHERE ts.tariff_id IN (...)            │
│                                        │
│ Result: M rows per tariff              │
└────────┬───────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────┐
│ Query 5: Get ServiceUsage              │
│                                        │
│ SELECT su.*, s.*, bd.*, c.*            │
│ FROM service_usage su                  │
│ JOIN service s ON su.service_id = s.id │
│ JOIN booking_detail bd ON ...          │
│ JOIN patient c ON bd.client_id = c.id  │
│ WHERE su.booking_id = 123              │
│                                        │
│ Result: K rows                         │
└────────┬───────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────┐
│ Query 6: Get MedicationSessions        │
│                                        │
│ SELECT ms.*, pm.*, m.*, ih.*, p.*      │
│ FROM medication_session ms             │
│ JOIN prescribed_medication pm ON ...   │
│ JOIN medication m ON ...               │
│ JOIN illness_history ih ON ...         │
│ JOIN patient p ON ih.patient_id = p.id │
│ WHERE ih.booking_id = 123              │
│                                        │
│ Result: L rows                         │
└────────┬───────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────┐
│ Query 7: Get AssignedLabs              │
│                                        │
│ SELECT al.*                            │
│ FROM assigned_lab al                   │
│ JOIN illness_history ih ON ...         │
│ WHERE ih.booking_id = 123              │
│                                        │
│ Result: J rows                         │
└────────┬───────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────┐
│ Query 8: Get Procedures                │
│                                        │
│ SELECT ips.*, ap.*, s.*, ih.*, p.*     │
│ FROM individual_procedure_session ips  │
│ JOIN assigned_procedure ap ON ...      │
│ JOIN service s ON ap.service_id = s.id │
│ JOIN illness_history ih ON ...         │
│ JOIN patient p ON ih.patient_id = p.id │
│ WHERE ih.booking_id = 123              │
│                                        │
│ Result: I rows                         │
└────────┬───────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────┐
│ Render Template                        │
│                                        │
│ Total Queries: ~8-10                   │
│ With prefetching: Good performance     │
│                                        │
│ Template shows all data                │
└────────────────────────────────────────┘
```

---

## 6. Status State Machine

```
┌─────────────────────────────────────────────────────────────────────┐
│                  BOOKING & BILLING STATUS FLOW                       │
└─────────────────────────────────────────────────────────────────────┘

BOOKING STATUS
┌──────────┐       ┌──────────┐       ┌────────────┐
│ PENDING  │──────>│CONFIRMED │──────>│ CHECKED_IN │
└──────────┘       └──────────┘       └──────┬─────┘
                                              │
                                              ▼
                                     ┌────────────────┐
                                     │  IN_PROGRESS   │
                                     └────────┬───────┘
                                              │
                         ┌────────────────────┼────────────────────┐
                         ▼                    ▼                    ▼
                  ┌──────────┐        ┌───────────┐       ┌──────────┐
                  │COMPLETED │        │ DISCHARGED│       │CANCELLED │
                  └──────────┘        └───────────┘       └──────────┘
                         │                    │
                         └────────┬───────────┘
                                  ▼
                         ┌─────────────────┐
                         │ BILLABLE        │
                         │ States:         │
                         │ - CHECKED_IN    │
                         │ - IN_PROGRESS   │
                         │ - COMPLETED     │
                         │ - DISCHARGED    │
                         └────────┬────────┘
                                  │
                                  ▼
                         ┌─────────────────┐
                         │ Appears in      │
                         │ Cashbox List    │
                         └─────────────────┘

BILLING STATUS
┌──────────┐       ┌────────────┐      ┌──────────┐      ┌──────┐
│ PENDING  │──────>│ CALCULATED │─────>│ INVOICED │─────>│ PAID │
└──────────┘       └────────────┘      └──────────┘      └──────┘
     │                    │                   │               │
     │                    │                   │               │
  [Create]          [Calculate]          [Invoice]      [Payment]
  Billing           Billing              Generated      Received
  Record            Amounts
                                                        (TODO)

STATUS TRANSITIONS & PERMISSIONS

PENDING → CALCULATED
├─ Trigger: User clicks "Calculate Billing"
├─ Permission: @cashbox_required
├─ Function: calculate_billing_amounts()
├─ Updates: All amount fields
└─ Validation: ✓ Booking must be billable status

CALCULATED → INVOICED
├─ Trigger: User clicks "Mark as Invoiced"
├─ Permission: @cashbox_required
├─ Function: billing_detail() POST handler
├─ Updates: billing_status only
└─ Validation: ✓ Must be CALCULATED first

CALCULATED → CALCULATED (Recalculate)
├─ Trigger: User clicks "Recalculate"
├─ Permission: @cashbox_required
├─ Function: calculate_billing_amounts()
├─ Updates: Recalculates all amounts
└─ Use case: After adding services/medications

INVOICED → PAID (TODO)
├─ Trigger: User clicks "Accept Payment"
├─ Permission: @cashbox_required
├─ Function: accept_payment() (not implemented)
├─ Creates: TransactionsModel record
└─ Validation: ✓ Amount matches total
```

---

## 7. Error Handling Flow (Recommendations)

```
┌─────────────────────────────────────────────────────────────────────┐
│              RECOMMENDED ERROR HANDLING FLOW                         │
└─────────────────────────────────────────────────────────────────────┘

Calculate Billing Request
         │
         ▼
┌────────────────────────────────────────┐
│ Validation Layer                       │
│                                        │
│ ✓ Booking exists?                      │
│   ├─ No: Return 404                    │
│   └─ Yes: Continue                     │
│                                        │
│ ✓ User has permission?                 │
│   ├─ No: Return 403                    │
│   └─ Yes: Continue                     │
│                                        │
│ ✓ Booking is billable status?          │
│   ├─ No: Return error message          │
│   └─ Yes: Continue                     │
│                                        │
│ ✓ BookingDetails exist?                │
│   ├─ No: Return error "No patients"    │
│   └─ Yes: Continue                     │
└────────┬───────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────┐
│ Calculation Layer                      │
│                                        │
│ try:                                   │
│   tariff_base = calculate_tariff()    │
│   ├─ Check: prices not None            │
│   ├─ Check: positive values            │
│   └─ Log: tariff calculation           │
│                                        │
│   services = calculate_services()      │
│   ├─ Check: no division by zero        │
│   ├─ Check: sessions >= 0              │
│   └─ Log: service calculation          │
│                                        │
│   medications = calculate_meds()       │
│   ├─ Check: quantities valid           │
│   ├─ Check: unit prices exist          │
│   └─ Log: medication calculation       │
│                                        │
│   labs = calculate_labs()              │
│   ├─ Check: lab prices exist           │
│   └─ Log: lab calculation              │
│                                        │
│ except ValueError as e:                │
│   ├─ Log error with details            │
│   ├─ Return user-friendly message      │
│   └─ Don't update billing record       │
│                                        │
│ except Exception as e:                 │
│   ├─ Log full traceback                │
│   ├─ Alert admin                       │
│   └─ Return generic error              │
└────────┬───────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────┐
│ Update Layer                           │
│                                        │
│ try:                                   │
│   billing = get_or_create_billing()   │
│   billing.tariff_base = tariff_base   │
│   billing.additional_services = ...    │
│   billing.medications = medications    │
│   billing.lab_research = labs         │
│   billing.billing_status = CALCULATED  │
│   billing.save()                       │
│                                        │
│ except IntegrityError as e:            │
│   ├─ Log: Database constraint error    │
│   └─ Return: "Data integrity issue"    │
│                                        │
│ except Exception as e:                 │
│   ├─ Log: Database save error          │
│   └─ Return: "Failed to save billing"  │
└────────┬───────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────┐
│ Success Response                       │
│                                        │
│ messages.success(request,              │
│   "Billing calculated successfully")   │
│                                        │
│ return redirect(billing_detail)        │
└────────────────────────────────────────┘
```

---

*End of Workflow Diagrams*
