# Cashbox Module Improvement Prompts

This document contains a comprehensive list of features and improvements for the Hayat Medical CRM Cashbox module.

## 🚨 Phase 1: Complete Core Billing (CRITICAL - Start Here)

### 1.1 Medication Billing Calculation
**Priority:** 🔴 Critical
**Status:** TODO - Currently returns 0
**Location:** `core/billing/calculator.py:195`

**Prompt:**
```
Implement medication billing calculation in the cashbox module. The function should:
- Query MedicationSession records linked to the booking
- Calculate costs based on medication prices and quantities
- Handle cases where medications are included in tariff vs. billable
- Update the breakdown.medications_amount field
- Add proper error handling for missing price data
```

**Related files:**
- [core/billing/calculator.py](core/billing/calculator.py#L195)
- [core/models/medication.py](core/models/medication.py)

---

### 1.2 Lab Research Billing Calculation
**Priority:** 🔴 Critical
**Status:** TODO - Currently returns 0
**Location:** `core/billing/calculator.py:201`

**Prompt:**
```
Implement lab research billing calculation in the cashbox module. The function should:
- Query AssignedLabs records for the booking
- Calculate costs based on lab test prices
- Handle multiple lab tests per booking
- Support tariff-included vs. additional lab tests
- Update the breakdown.lab_research_amount field
- Include proper validation and error handling
```

**Related files:**
- [core/billing/calculator.py](core/billing/calculator.py#L201)
- [core/models/laboratory.py](core/models/laboratory.py)

---

### 1.3 Individual Procedure Billing
**Priority:** 🔴 Critical
**Status:** Partial - Listed but not explicitly calculated

**Prompt:**
```
Implement individual procedure billing calculation for the cashbox module. The system should:
- Query IndividualProcedureSessionModel records for the booking
- Calculate costs for procedures performed beyond tariff inclusions
- Track which procedures are included in tariff vs. billable
- Add a new field to BookingBilling model for procedure amounts
- Update templates to display procedure costs in the breakdown
- Ensure procedures are properly summed in total_amount
```

**Related files:**
- [core/models/procedure.py](core/models/procedure.py)
- [core/models/booking.py](core/models/booking.py)

---

### 1.4 Billing Calculation Validation
**Priority:** 🟡 High

**Prompt:**
```
Add comprehensive validation and error handling to the billing calculation system:
- Validate that all services have prices defined
- Check for missing tariff information
- Handle edge cases (null prices, zero quantities)
- Add logging for calculation errors
- Return detailed error messages to the UI
- Prevent partial calculations from being saved
- Add unit tests for all calculation scenarios
```

---

## 💰 Phase 2: Payment Processing

### 2.1 Payment Acceptance Functionality
**Priority:** 🟡 High
**Status:** UI button exists, no backend

**Prompt:**
```
Implement payment acceptance functionality for the cashbox module:
- Create a payment acceptance form with fields: amount, payment method (cash/card/transfer), payment date, notes
- Integrate with TransactionsModel to record payments
- Link payments to BookingBilling records
- Update payment status on the billing (unpaid/partially paid/fully paid/overpaid)
- Add AJAX endpoint for accepting payments without page reload
- Generate payment confirmation/receipt number
- Add validation to prevent overpayment without confirmation
- Show payment status badges in billing list and detail views
```

**Related files:**
- [core/models/transactions.py](core/models/transactions.py)
- [application/cashbox/views/billing_views.py](application/cashbox/views/billing_views.py)

---

### 2.2 Payment History View
**Priority:** 🟡 High

**Prompt:**
```
Create a payment history view for bookings in the cashbox module:
- Add a new tab/section in billing_detail.html to show payment history
- Display table of all payments: date, amount, method, cashier, receipt number
- Show running balance (total billed vs. total paid)
- Add ability to view/print individual payment receipts
- Include payment status timeline (visual progress indicator)
- Add filters for payment method and date range
```

---

### 2.3 Multiple Payment Methods Support
**Priority:** 🟢 Medium

**Prompt:**
```
Enhance payment acceptance to support split payments:
- Allow multiple payment methods for a single invoice (e.g., part cash, part card)
- Add UI to accept multiple payment entries at once
- Track each payment method separately in TransactionsModel
- Show payment method breakdown in reports
- Support insurance payments with separate workflow
- Add payment method statistics to dashboard
```

---

### 2.4 Payment Status Tracking
**Priority:** 🟡 High

**Prompt:**
```
Add comprehensive payment status tracking to the BookingBilling model:
- Add new fields: payment_status (unpaid/partially_paid/fully_paid/overpaid), total_paid, balance_due
- Create database migration for new fields
- Update billing calculation to compute payment status
- Add indexes for payment status queries
- Update billing list filters to include payment status
- Add color-coded badges for payment status
- Create "Unpaid Invoices" quick filter in dashboard
```

---

## 📄 Phase 3: Documents & Reports

### 3.1 PDF Invoice Generation
**Priority:** 🟡 High
**Status:** Templates ready, no PDF generation

**Prompt:**
```
Implement PDF invoice generation for the cashbox module:
- Install and configure a PDF library (WeasyPrint or ReportLab)
- Create a professional invoice template with:
  - Clinic logo and header
  - Invoice number and date
  - Patient information
  - Itemized billing breakdown (tariff, services, medications, labs)
  - Subtotals and grand total
  - Payment information if applicable
  - Footer with terms and clinic contact info
- Add "Download PDF" button to billing detail page
- Add "Print Invoice" button with print-optimized view
- Store PDF files or generate on-demand
- Support invoice reprinting with version tracking
```

**Related files:**
- [application/templates/cashbox/billing/billing_detail.html](application/templates/cashbox/billing/billing_detail.html)

---

### 3.2 Receipt Generation
**Priority:** 🟡 High

**Prompt:**
```
Create payment receipt generation for the cashbox module:
- Design receipt template (smaller format than invoice)
- Include: receipt number, date, patient name, amount paid, payment method, cashier name
- Support thermal printer format (58mm or 80mm)
- Add "Print Receipt" button after payment acceptance
- Generate PDF receipts for email/download
- Support receipt reprinting from payment history
- Add receipt numbering system (sequential, per day/month)
```

---

### 3.3 Email Invoice to Patient
**Priority:** 🟢 Medium

**Prompt:**
```
Implement email functionality for invoices in the cashbox module:
- Configure Django email backend (SMTP settings)
- Create email template with invoice attached
- Add "Email Invoice" button in billing detail view
- Support manual email entry or use patient's email from booking
- Add email sending confirmation and error handling
- Track email sent status in BookingBilling model
- Support resending invoices
- Add email queue for bulk sending
```

---

### 3.4 Export Reports Implementation
**Priority:** 🟢 Medium
**Status:** Button exists, no implementation

**Prompt:**
```
Implement export functionality for billing reports:
- Export billing list to Excel/CSV with current filters applied
- Include columns: booking number, patient name, dates, amounts, status, payment status
- Add "Export to Excel" button in billing list page
- Create daily/weekly/monthly financial summary reports
- Export dashboard statistics
- Support custom date range for exports
- Use openpyxl or pandas for Excel generation
- Add export job tracking for large datasets
```

---

### 3.5 Financial Summary Reports
**Priority:** 🟢 Medium

**Prompt:**
```
Create comprehensive financial summary reports for the cashbox module:
- Daily cashier summary report: total invoiced, total collected, by payment method
- Weekly/Monthly revenue reports with trends
- Outstanding receivables report (unpaid/partially paid invoices)
- Revenue by service category (tariff, additional services, medications, labs)
- Revenue by room/department
- Cashier performance report (per cashier statistics)
- Add report templates and PDF export
- Include charts and visualizations
```

---

## 💸 Phase 4: Financial Operations

### 4.1 Discount System
**Priority:** 🟢 Medium

**Prompt:**
```
Implement a discount system for the cashbox module:
- Add discount fields to BookingBilling model: discount_type (percentage/fixed), discount_amount, discount_reason, discount_approved_by
- Create discount application form in billing detail view
- Support percentage discounts (e.g., 10% off) and fixed amount discounts
- Add authorization requirement for discounts above threshold
- Track discount approval workflow
- Update total_amount calculation to include discounts
- Show discount details on invoices
- Add discount statistics to reports
- Support promotional codes (optional)
```

---

### 4.2 Refund Processing
**Priority:** 🟢 Medium

**Prompt:**
```
Implement refund processing functionality for the cashbox module:
- Create refund model to track refunds: amount, reason, refund_method, approved_by, processed_by
- Add "Process Refund" button/form in billing detail view
- Support partial and full refunds
- Implement approval workflow for refunds above threshold
- Update payment status after refund
- Generate refund receipt/confirmation
- Track refunds in TransactionsModel with negative amounts
- Add refund reporting and audit trail
- Handle refund by different payment methods (cash, card reversal, bank transfer)
```

---

### 4.3 Manual Billing Adjustments
**Priority:** 🟢 Medium

**Prompt:**
```
Add manual billing adjustment capability to the cashbox module:
- Allow authorized users to manually adjust billing amounts before invoicing
- Add "Add Manual Line Item" functionality for miscellaneous charges
- Create adjustment form with: item description, amount, reason, approved_by
- Track all adjustments in audit trail
- Prevent adjustments after invoicing without special permission
- Show adjustments clearly in invoice breakdown
- Require reason codes for all adjustments
- Add approval workflow for adjustments above threshold
```

---

### 4.4 Credit/Debt Management
**Priority:** 🟢 Medium

**Prompt:**
```
Implement credit and debt tracking for the cashbox module:
- Add fields to track outstanding balances per patient
- Create "Outstanding Balances" report showing all unpaid/partially paid invoices
- Add aging report (0-30 days, 30-60 days, 60-90 days, 90+ days overdue)
- Implement payment plan functionality for installments
- Add reminder system for overdue payments
- Track collection efforts and notes
- Flag patients with outstanding balances in booking system
- Support write-offs for uncollectible amounts with approval
```

---

## 🔍 Phase 5: Audit & Compliance

### 5.1 Audit Trail Implementation
**Priority:** 🟡 High

**Prompt:**
```
Implement comprehensive audit trail for all billing operations:
- Create BillingAuditLog model to track: action_type, old_value, new_value, changed_by, changed_at, reason
- Log all billing changes: calculation, status changes, adjustments, discounts, refunds
- Add "View History" button in billing detail showing all changes
- Track who calculated, who invoiced, who accepted payment
- Store IP address and timestamp for security
- Make audit logs immutable (cannot be edited/deleted)
- Add audit log export functionality
- Create audit log search and filter interface
```

---

### 5.2 Billing Version Control
**Priority:** 🟢 Medium

**Prompt:**
```
Implement versioning for billing records:
- Create BillingVersion model to store billing snapshots
- Automatically create version when billing is invoiced
- If recalculation needed after invoicing, create new version
- Add "View Previous Versions" functionality
- Track reason for recalculation
- Support generating invoices for any version
- Show version comparison (what changed)
- Prevent accidental data loss from recalculations
```

---

### 5.3 Financial Controls & Locks
**Priority:** 🟡 High

**Prompt:**
```
Implement financial controls and record locking:
- Lock billing records after invoicing (prevent edits without approval)
- Add "Void Invoice" workflow instead of deletion
- Require dual authorization for sensitive operations (large refunds, write-offs)
- Implement supervisor override functionality with password/PIN
- Add financial period closing (lock all records for a closed period)
- Create permission levels: cashier, senior cashier, finance manager, admin
- Log all override attempts
- Add alerts for suspicious activities
```

---

## 🎯 Phase 6: User Experience Improvements

### 6.1 Bulk Actions Implementation
**Priority:** 🟢 Medium
**Status:** Button exists, no functionality

**Prompt:**
```
Implement bulk actions for the billing list:
- Add checkboxes to billing list for selecting multiple bookings
- Create bulk action dropdown: "Calculate Selected", "Mark as Invoiced", "Export Selected"
- Add "Select All" / "Select None" functionality
- Show count of selected items
- Add confirmation dialog before bulk operations
- Process bulk actions with progress indicator
- Show success/failure summary after bulk operation
- Add bulk email sending for invoices
```

---

### 6.2 Quick Filters & Search
**Priority:** 🟢 Medium

**Prompt:**
```
Enhance filtering and search capabilities:
- Add quick filter buttons: "Needs Calculation", "Ready to Invoice", "Unpaid", "Today's Billings", "This Week"
- Improve search to include: patient phone, patient ID, room number
- Add saved filter presets (user can save custom filter combinations)
- Add "Clear All Filters" button
- Show active filter count indicator
- Implement URL-based filter persistence (bookmarkable filtered views)
- Add autocomplete for patient name search
```

---

### 6.3 Inline Editing & Quick Actions
**Priority:** 🟢 Medium

**Prompt:**
```
Add inline editing capabilities to billing views:
- Allow editing billing amounts directly in detail view (before invoicing)
- Add quick discount application dropdown (5%, 10%, 15%, custom)
- Implement inline payment acceptance (modal popup instead of new page)
- Add quick notes/comments field for billing records
- Support keyboard shortcuts for common actions (Ctrl+S to calculate, etc.)
- Add "Copy from Previous Booking" for repeat patients
- Implement autosave for draft adjustments
```

---

### 6.4 Enhanced Dashboard
**Priority:** 🟢 Medium

**Prompt:**
```
Enhance the cashbox dashboard with more insights:
- Add real-time revenue counter (today's collected amount)
- Show cashier shift summary (if shift management added)
- Add "Top Services by Revenue" chart
- Show payment method distribution (pie chart)
- Add "Recent Payments" widget (last 10 payments)
- Show alerts: pending calculations, overdue payments, large outstanding balances
- Add financial KPIs: collection rate, average billing amount, revenue per patient day
- Support dashboard customization (drag & drop widgets)
```

---

## 🔔 Phase 7: Notifications & Alerts

### 7.1 Staff Notifications
**Priority:** 🟢 Medium

**Prompt:**
```
Implement notification system for cashbox staff:
- Create in-app notification system (bell icon with badge count)
- Send notifications when: booking discharged (needs billing), payment received, refund approved
- Add daily summary email for cashbox manager (revenue, outstanding amounts, alerts)
- Support browser push notifications (optional, with user permission)
- Add notification preferences per user
- Create notification history view
- Mark notifications as read/unread
- Support notification filtering by type
```

---

### 7.2 Patient Payment Reminders
**Priority:** 🔵 Low

**Prompt:**
```
Implement automated payment reminder system:
- Send SMS/email reminders for unpaid invoices after X days
- Create customizable reminder templates
- Support reminder schedule (3 days, 7 days, 14 days overdue)
- Track reminder sent status
- Stop reminders once payment received
- Add manual reminder sending option
- Generate reminder report (who was reminded, response rate)
- Integrate with SMS gateway and email service
```

---

## 🏥 Phase 8: Insurance Integration

### 8.1 Insurance Billing Workflow
**Priority:** 🔵 Low (unless insurance is major revenue source)

**Prompt:**
```
Implement insurance billing functionality:
- Add insurance fields to BookingBilling: insurance_company, insurance_policy_number, insurance_amount, patient_copay_amount
- Create separate insurance billing calculation (may have different pricing)
- Support pre-authorization tracking (authorization number, approved amount)
- Add insurance claim submission functionality
- Track claim status (submitted, approved, denied, partial approval)
- Handle insurance payment reception separately from patient payment
- Generate insurance-specific invoice format
- Add insurance company payment reconciliation
- Support coordination of benefits (multiple insurance)
```

---

### 8.2 Insurance Reports
**Priority:** 🔵 Low

**Prompt:**
```
Create insurance-specific reporting:
- Claims submission report (batch export for insurance companies)
- Outstanding claims report (submitted but not paid)
- Denial report with reasons
- Payment reconciliation report (expected vs. received)
- Insurance company performance report (approval rate, payment speed)
- Patient copay collection report
- Support multiple insurance company formats (Excel, CSV, custom formats)
```

---

## 🔄 Phase 9: Integration Features

### 9.1 Accounting System Integration
**Priority:** 🔵 Low (depends on accounting software used)

**Prompt:**
```
Integrate cashbox with accounting system:
- Research accounting software used (QuickBooks, 1C, custom)
- Create chart of accounts mapping (revenue accounts, receivables, etc.)
- Generate journal entries for invoices and payments
- Add export to accounting format
- Support automatic sync vs. manual export
- Track sync status for each transaction
- Handle sync errors and retries
- Add reconciliation report (cashbox vs. accounting)
```

---

### 9.2 Payment Terminal Integration
**Priority:** 🟢 Medium (if accepting card payments)

**Prompt:**
```
Integrate with payment terminals/gateways:
- Research available payment terminals in Uzbekistan (Payme, Click, UzCard terminals)
- Implement payment terminal API integration
- Add "Process Card Payment" button that triggers terminal
- Handle payment success/failure callbacks
- Store terminal transaction IDs
- Support payment refunds through terminal
- Add QR code payment support (Payme, Click QR codes)
- Test payment terminal connection and error handling
```

---

## 📱 Phase 10: Advanced Features

### 10.1 Patient Self-Service Portal
**Priority:** 🔵 Low

**Prompt:**
```
Create patient portal for invoice viewing and payment:
- Build patient login system (separate from staff login)
- Create patient dashboard showing their bookings and invoices
- Allow patients to view invoice details
- Add online payment functionality (card payment gateway)
- Support invoice PDF download
- Send email notifications when invoices are ready
- Add payment history for patients
- Support payment plan setup by patients
- Implement secure access (OTP or password reset)
```

---

### 10.2 Deposit/Advance Payment
**Priority:** 🟢 Medium

**Prompt:**
```
Implement deposit and advance payment functionality:
- Add deposit recording at booking creation time
- Create DepositPayment model linked to bookings
- Track deposit amount separately from final billing
- Automatically apply deposit to final invoice
- Calculate balance due (total - deposit)
- Handle deposit refunds for cancelled bookings
- Generate deposit receipts
- Show deposit information in billing detail
- Support partial deposits and multiple deposit payments
- Add deposit tracking report
```

---

### 10.3 Cashier Shift Management
**Priority:** 🟢 Medium

**Prompt:**
```
Implement cashier shift management:
- Create CashierShift model: cashier, start_time, end_time, opening_balance, closing_balance, status
- Add "Open Shift" functionality (cashier declares opening cash amount)
- Track all transactions during shift
- Add "Close Shift" with cash counting and reconciliation
- Calculate expected cash (opening + cash payments - cash refunds)
- Show variance (expected vs. actual)
- Generate shift summary report
- Require shift closure before cashier logout
- Add supervisor approval for large variances
- Track shift handovers
```

---

### 10.4 Tax Handling
**Priority:** 🔵 Low (unless required by regulations)

**Prompt:**
```
Implement tax calculation and reporting:
- Research Uzbekistan medical service tax requirements
- Add tax fields to BookingBilling: tax_rate, tax_amount, is_tax_exempt
- Configure tax rates in settings or database
- Calculate tax automatically based on service type
- Support tax-exempt services (if applicable)
- Show tax breakdown on invoices
- Generate tax reports for filing
- Support different tax rates for different services
- Add tax period closing and reporting
```

---

### 10.5 Multi-Currency Support
**Priority:** 🔵 Low (unless serving international patients)

**Prompt:**
```
Add multi-currency billing support:
- Add currency field to BookingBilling
- Support USD, EUR, RUB alongside UZS
- Integrate with currency exchange rate API
- Convert amounts for display
- Accept payments in different currencies
- Generate invoices in patient's preferred currency
- Track exchange rates used for each transaction
- Add currency conversion report
- Handle currency rounding properly
```

---

## 🧪 Phase 11: Testing & Quality

### 11.1 Comprehensive Unit Tests
**Priority:** 🟡 High

**Prompt:**
```
Create comprehensive unit tests for cashbox module:
- Test all billing calculation functions with various scenarios
- Test tariff change mid-stay prorating
- Test medication and lab billing calculations
- Test discount and refund calculations
- Test payment status updates
- Test edge cases (null prices, zero quantities, negative amounts)
- Achieve >80% code coverage for cashbox module
- Add test fixtures for common scenarios
- Test concurrent access and race conditions
- Add performance tests for large datasets
```

---

### 11.2 Integration Tests
**Priority:** 🟡 High

**Prompt:**
```
Create integration tests for complete billing workflows:
- Test end-to-end: booking creation → discharge → calculate → invoice → payment
- Test with multiple services, medications, and labs
- Test refund workflow
- Test discount application and approval
- Test report generation
- Test email sending
- Test PDF generation
- Test payment terminal integration
- Test audit trail creation
```

---

### 11.3 Performance Optimization
**Priority:** 🟢 Medium

**Prompt:**
```
Optimize cashbox module performance:
- Add database indexes for common queries
- Optimize billing calculation queries (reduce N+1 queries)
- Add caching for dashboard statistics
- Implement pagination for large reports
- Optimize PDF generation (consider background jobs)
- Add query profiling and optimization
- Test with large datasets (1000+ bookings)
- Implement lazy loading for related objects
- Use select_related and prefetch_related appropriately
```

---

## 📋 Implementation Checklist Template

For each feature, track progress:

```
Feature: [Feature Name]
Status: [ ] Not Started  [ ] In Progress  [ ] Testing  [ ] Completed
Priority: [ ] Critical  [ ] High  [ ] Medium  [ ] Low
Estimated Effort: [ ] Small (1-2 days)  [ ] Medium (3-5 days)  [ ] Large (1-2 weeks)
Dependencies: [List any prerequisites]
Assigned To: [Developer name]
Started: [Date]
Completed: [Date]
Notes: [Any implementation notes or blockers]
```

---

## 🎯 Quick Start Recommendations

**If you have limited time, start with these essential features:**

1. ✅ Complete medication billing calculation (Phase 1.1)
2. ✅ Complete lab research billing calculation (Phase 1.2)
3. ✅ Payment acceptance functionality (Phase 2.1)
4. ✅ Payment status tracking (Phase 2.4)
5. ✅ PDF invoice generation (Phase 3.1)

**These 5 features will make the cashbox module fully functional for basic operations.**

---

## 📞 Support & Questions

For questions about implementation or prioritization:
- Review existing code in [application/cashbox/](application/cashbox/)
- Check models in [core/models/](core/models/)
- Refer to billing calculator at [core/billing/calculator.py](core/billing/calculator.py)

---

**Last Updated:** 2025-12-03
**Module Version:** 1.0
**Total Features Listed:** 50+
