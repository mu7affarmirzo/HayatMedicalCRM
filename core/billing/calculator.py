"""
Billing calculator for bookings with support for tariff changes during stay
"""
from decimal import Decimal
from typing import List, Dict, Any
from collections import defaultdict
from django.db.models import Sum, Q


class TariffPeriodBilling:
    """Represents billing information for a single tariff period"""

    def __init__(self, booking_detail):
        self.booking_detail = booking_detail
        self.tariff_name = booking_detail.tariff.name
        self.room_name = booking_detail.room.name
        self.effective_from = booking_detail.effective_from
        self.effective_to = booking_detail.effective_to
        self.days_in_period = booking_detail.get_days_in_period()
        self.tariff_base_charge = float(booking_detail.get_prorated_price())

        # Service billing details
        self.service_sessions = []  # List of {service_name, sessions_used, sessions_included, sessions_billed, amount}
        self.total_service_charges = 0

    def add_service_billing(self, service_name: str, sessions_used: int, sessions_included: int,
                            sessions_billed: int, billed_amount: float):
        """Add service billing information for this period"""
        self.service_sessions.append({
            'service_name': service_name,
            'sessions_used': sessions_used,
            'sessions_included': sessions_included,
            'sessions_billed': sessions_billed,
            'amount': billed_amount
        })
        self.total_service_charges += billed_amount

    @property
    def total_period_charge(self):
        """Total charge for this period (tariff base + services)"""
        return self.tariff_base_charge + self.total_service_charges

    def to_dict(self):
        """Convert to dictionary for serialization"""
        return {
            'tariff_name': self.tariff_name,
            'room_name': self.room_name,
            'effective_from': self.effective_from.isoformat() if self.effective_from else None,
            'effective_to': self.effective_to.isoformat() if self.effective_to else None,
            'days_in_period': self.days_in_period,
            'tariff_base_charge': self.tariff_base_charge,
            'service_sessions': self.service_sessions,
            'total_service_charges': self.total_service_charges,
            'total_period_charge': self.total_period_charge
        }


class BookingBillingBreakdown:
    """Complete billing breakdown for a booking"""

    def __init__(self, booking):
        self.booking = booking
        self.booking_number = booking.booking_number
        self.periods: List[TariffPeriodBilling] = []
        self.total_tariff_charges = 0
        self.total_service_charges = 0
        self.medications_amount = 0
        self.lab_research_amount = 0
        self.grand_total = 0

    def add_period(self, period: TariffPeriodBilling):
        """Add a tariff period to the breakdown"""
        self.periods.append(period)
        self.total_tariff_charges += period.tariff_base_charge
        self.total_service_charges += period.total_service_charges

    def calculate_grand_total(self):
        """Calculate the final grand total"""
        self.grand_total = (
            self.total_tariff_charges +
            self.total_service_charges +
            self.medications_amount +
            self.lab_research_amount
        )
        return self.grand_total

    def to_dict(self):
        """Convert to dictionary for serialization"""
        return {
            'booking_number': self.booking_number,
            'periods': [period.to_dict() for period in self.periods],
            'total_tariff_charges': self.total_tariff_charges,
            'total_service_charges': self.total_service_charges,
            'medications_amount': self.medications_amount,
            'lab_research_amount': self.lab_research_amount,
            'grand_total': self.grand_total
        }

    def __str__(self):
        """String representation of billing breakdown"""
        lines = [
            f"Billing Breakdown for Booking #{self.booking_number}",
            "=" * 60,
            ""
        ]

        for idx, period in enumerate(self.periods, 1):
            lines.append(f"Period {idx}: {period.tariff_name} ({period.room_name})")
            lines.append(f"  Dates: {period.effective_from.strftime('%Y-%m-%d')} to "
                        f"{period.effective_to.strftime('%Y-%m-%d') if period.effective_to else 'current'}")
            lines.append(f"  Days: {period.days_in_period}")
            lines.append(f"  Tariff Base: {period.tariff_base_charge:,.2f} UZS")

            if period.service_sessions:
                lines.append(f"  Services:")
                for service in period.service_sessions:
                    lines.append(
                        f"    - {service['service_name']}: "
                        f"{service['sessions_used']}/{service['sessions_included']} sessions "
                        f"(billed: {service['sessions_billed']}) = {service['amount']:,.2f} UZS"
                    )

            lines.append(f"  Period Total: {period.total_period_charge:,.2f} UZS")
            lines.append("")

        lines.append("=" * 60)
        lines.append(f"Total Tariff Charges: {self.total_tariff_charges:,.2f} UZS")
        lines.append(f"Total Service Charges: {self.total_service_charges:,.2f} UZS")
        lines.append(f"Medications: {self.medications_amount:,.2f} UZS")
        lines.append(f"Lab Research: {self.lab_research_amount:,.2f} UZS")
        lines.append("=" * 60)
        lines.append(f"GRAND TOTAL: {self.grand_total:,.2f} UZS")

        return "\n".join(lines)


def calculate_booking_billing(booking, include_medications=True, include_lab_research=True):
    """
    Calculate complete billing for a booking with support for multiple tariff changes.

    Args:
        booking: Booking instance
        include_medications: Include medication costs in calculation
        include_lab_research: Include lab research costs in calculation

    Returns:
        BookingBillingBreakdown instance with complete billing information
    """
    from core.models.booking import BookingDetail
    from core.models.sanatorium.prescriptions.procedures import IndividualProcedureSessionModel
    from core.models.tariffs import ServiceSessionTracking

    breakdown = BookingBillingBreakdown(booking)

    # Get all BookingDetails for this booking, ordered by effective_from
    booking_details = BookingDetail.objects.filter(
        booking=booking
    ).order_by('effective_from', 'client__full_name')

    # Process each BookingDetail period
    for booking_detail in booking_details:
        period = TariffPeriodBilling(booking_detail)

        # Get service session tracking for this period
        tracking_records = ServiceSessionTracking.objects.filter(
            booking_detail=booking_detail
        ).select_related('service')

        for tracking in tracking_records:
            # Get the total billed amount for this service in this period
            sessions = IndividualProcedureSessionModel.objects.filter(
                booking_detail_at_time=booking_detail,
                assigned_procedure__medical_service=tracking.service,
                is_billable=True
            )

            total_billed = sessions.aggregate(
                total=Sum('billed_amount')
            )['total'] or 0

            # Add to period if there were any sessions (billed or not)
            if tracking.sessions_used > 0:
                period.add_service_billing(
                    service_name=tracking.service.name,
                    sessions_used=tracking.sessions_used,
                    sessions_included=tracking.sessions_included,
                    sessions_billed=tracking.sessions_billed,
                    billed_amount=float(total_billed)
                )

        breakdown.add_period(period)

    # Add medications if requested
    if include_medications:
        # TODO: Implement medication billing calculation
        # This would query prescribed medications and sum their costs
        breakdown.medications_amount = 0

    # Add lab research if requested
    if include_lab_research:
        # TODO: Implement lab research billing calculation
        # This would query lab orders and sum their costs
        breakdown.lab_research_amount = 0

    # Calculate final total
    breakdown.calculate_grand_total()

    return breakdown


def update_booking_billing_record(booking):
    """
    Calculate billing and update the BookingBilling record.

    Args:
        booking: Booking instance

    Returns:
        BookingBilling instance
    """
    from core.models.booking import BookingBilling

    # Calculate billing breakdown
    breakdown = calculate_booking_billing(booking)

    # Get or create BookingBilling record
    billing, created = BookingBilling.objects.get_or_create(
        booking=booking,
        defaults={
            'billing_status': BookingBilling.BillingStatus.CALCULATED
        }
    )

    # Update billing amounts
    billing.tariff_base_amount = int(breakdown.total_tariff_charges)
    billing.additional_services_amount = int(breakdown.total_service_charges)
    billing.medications_amount = int(breakdown.medications_amount)
    billing.lab_research_amount = int(breakdown.lab_research_amount)
    billing.billing_status = BookingBilling.BillingStatus.CALCULATED
    billing.save()

    return billing


def recalculate_all_sessions_for_booking(booking):
    """
    Recalculate billing for all completed sessions in a booking.
    Useful after a tariff change to ensure correct billing.

    Args:
        booking: Booking instance

    Returns:
        Number of sessions recalculated
    """
    from core.models.sanatorium.prescriptions.procedures import IndividualProcedureSessionModel
    from core.models import IllnessHistory

    # Get all illness histories for this booking
    illness_histories = IllnessHistory.objects.filter(booking=booking)

    # Get all completed sessions for these illness histories
    sessions = IndividualProcedureSessionModel.objects.filter(
        assigned_procedure__illness_history__in=illness_histories,
        status='completed',
        completed_at__isnull=False
    )

    count = 0
    for session in sessions:
        session.recalculate_billing()
        count += 1

    return count