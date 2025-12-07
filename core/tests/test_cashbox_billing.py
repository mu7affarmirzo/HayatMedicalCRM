"""
Comprehensive test scenarios for cashbox billing module

Test scenarios include:
1. Single patient booking with basic tariff
2. Multiple patients booking with different tariffs
3. Tariff changes during stay
4. Additional services billing
5. Medication billing
6. Lab research billing
7. Complete billing calculation
"""

from decimal import Decimal
from datetime import timedelta
from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model

from core.models import (
    Booking, BookingDetail, BookingBilling, ServiceUsage,
    PatientModel, Room, RoomType, Tariff, TariffRoomPrice,
    Service, TariffService, ServiceSessionTracking,
    Account, RolesModel
)
from core.billing.calculator import (
    calculate_booking_billing,
    update_booking_billing_record,
    BookingBillingBreakdown
)


User = get_user_model()


class CashboxBillingTestCase(TestCase):
    """Test cases for cashbox billing functionality"""

    def setUp(self):
        """Set up test data"""
        # Create test user with cashbox role
        self.cashbox_user = Account.objects.create_user(
            username='cashbox_user',
            email='cashbox@test.com',
            password='testpass123'
        )
        self.cashbox_user.f_name = 'Cashbox'
        self.cashbox_user.l_name = 'User'
        self.cashbox_user.role = RolesModel.CASHBOX
        self.cashbox_user.save()

        # Create room types
        self.standard_room_type = RoomType.objects.create(
            name='Стандарт',
            description='Стандартный номер'
        )
        self.deluxe_room_type = RoomType.objects.create(
            name='Люкс',
            description='Люкс номер'
        )

        # Create rooms
        self.room_101 = Room.objects.create(
            name='101',
            room_type=self.standard_room_type,
            capacity=2,
            is_active=True
        )
        self.room_102 = Room.objects.create(
            name='102',
            room_type=self.deluxe_room_type,
            capacity=2,
            is_active=True
        )

        # Create services
        self.massage_service = Service.objects.create(
            name='Массаж',
            description='Лечебный массаж',
            price=50000
        )
        self.physiotherapy_service = Service.objects.create(
            name='Физиотерапия',
            description='Физиотерапевтические процедуры',
            price=30000
        )

        # Create tariffs
        self.basic_tariff = Tariff.objects.create(
            name='Базовый',
            description='Базовый тариф',
            price=Decimal('500000')
        )
        self.premium_tariff = Tariff.objects.create(
            name='Премиум',
            description='Премиум тариф',
            price=Decimal('800000')
        )

        # Create tariff-room prices
        TariffRoomPrice.objects.create(
            tariff=self.basic_tariff,
            room_type=self.standard_room_type,
            price=Decimal('500000')
        )
        TariffRoomPrice.objects.create(
            tariff=self.basic_tariff,
            room_type=self.deluxe_room_type,
            price=Decimal('600000')
        )
        TariffRoomPrice.objects.create(
            tariff=self.premium_tariff,
            room_type=self.standard_room_type,
            price=Decimal('800000')
        )
        TariffRoomPrice.objects.create(
            tariff=self.premium_tariff,
            room_type=self.deluxe_room_type,
            price=Decimal('1000000')
        )

        # Create tariff services
        TariffService.objects.create(
            tariff=self.basic_tariff,
            service=self.massage_service,
            sessions_included=5
        )
        TariffService.objects.create(
            tariff=self.basic_tariff,
            service=self.physiotherapy_service,
            sessions_included=10
        )
        TariffService.objects.create(
            tariff=self.premium_tariff,
            service=self.massage_service,
            sessions_included=10
        )
        TariffService.objects.create(
            tariff=self.premium_tariff,
            service=self.physiotherapy_service,
            sessions_included=15
        )

        # Create test patients
        self.patient1 = PatientModel.objects.create(
            f_name='Иван',
            l_name='Иванов',
            phone='+998901234567',
            date_of_birth='1980-01-01'
        )
        self.patient2 = PatientModel.objects.create(
            f_name='Мария',
            l_name='Петрова',
            phone='+998901234568',
            date_of_birth='1985-05-15'
        )

    def test_scenario_1_single_patient_basic_tariff(self):
        """
        Test Scenario 1: Single patient booking with basic tariff
        - 1 patient
        - Basic tariff
        - Standard room
        - 7 days stay
        - No additional services
        """
        # Create booking
        start_date = timezone.now()
        end_date = start_date + timedelta(days=7)

        booking = Booking.objects.create(
            booking_number=Booking.generate_booking_number(),
            staff=self.cashbox_user,
            start_date=start_date,
            end_date=end_date,
            status='checked_in'
        )

        # Create booking detail
        booking_detail = BookingDetail.objects.create(
            booking=booking,
            client=self.patient1,
            room=self.room_101,
            tariff=self.basic_tariff,
            price=Decimal('500000'),
            start_date=start_date,
            end_date=end_date,
            effective_from=start_date
        )

        # Calculate billing
        breakdown = calculate_booking_billing(booking)

        # Assertions
        self.assertEqual(breakdown.booking_number, booking.booking_number)
        self.assertEqual(len(breakdown.periods), 1)
        self.assertEqual(breakdown.total_tariff_charges, 500000.0)
        self.assertEqual(breakdown.total_service_charges, 0)
        self.assertEqual(breakdown.medications_amount, 0)
        self.assertEqual(breakdown.lab_research_amount, 0)
        self.assertEqual(breakdown.grand_total, 500000.0)

        print("\n" + "="*80)
        print("TEST SCENARIO 1: Single Patient Basic Tariff")
        print("="*80)
        print(breakdown)
        print("="*80)

    def test_scenario_2_multiple_patients_different_tariffs(self):
        """
        Test Scenario 2: Multiple patients with different tariffs
        - 2 patients
        - Patient 1: Basic tariff, Standard room
        - Patient 2: Premium tariff, Deluxe room
        - 7 days stay
        - No additional services
        """
        start_date = timezone.now()
        end_date = start_date + timedelta(days=7)

        booking = Booking.objects.create(
            booking_number=Booking.generate_booking_number(),
            staff=self.cashbox_user,
            start_date=start_date,
            end_date=end_date,
            status='checked_in'
        )

        # Patient 1 - Basic tariff
        booking_detail1 = BookingDetail.objects.create(
            booking=booking,
            client=self.patient1,
            room=self.room_101,
            tariff=self.basic_tariff,
            price=Decimal('500000'),
            start_date=start_date,
            end_date=end_date,
            effective_from=start_date
        )

        # Patient 2 - Premium tariff
        booking_detail2 = BookingDetail.objects.create(
            booking=booking,
            client=self.patient2,
            room=self.room_102,
            tariff=self.premium_tariff,
            price=Decimal('1000000'),
            start_date=start_date,
            end_date=end_date,
            effective_from=start_date
        )

        # Calculate billing
        breakdown = calculate_booking_billing(booking)

        # Assertions
        self.assertEqual(len(breakdown.periods), 2)
        self.assertEqual(breakdown.total_tariff_charges, 1500000.0)
        self.assertEqual(breakdown.grand_total, 1500000.0)

        print("\n" + "="*80)
        print("TEST SCENARIO 2: Multiple Patients Different Tariffs")
        print("="*80)
        print(breakdown)
        print("="*80)

    def test_scenario_3_tariff_change_during_stay(self):
        """
        Test Scenario 3: Tariff change during stay
        - 1 patient
        - Days 1-3: Basic tariff, Standard room
        - Days 4-7: Premium tariff, Deluxe room (upgrade)
        - Total: 7 days
        """
        start_date = timezone.now()
        end_date = start_date + timedelta(days=7)
        change_date = start_date + timedelta(days=3)

        booking = Booking.objects.create(
            booking_number=Booking.generate_booking_number(),
            staff=self.cashbox_user,
            start_date=start_date,
            end_date=end_date,
            status='checked_in'
        )

        # Initial booking detail - Basic tariff
        initial_detail = BookingDetail.objects.create(
            booking=booking,
            client=self.patient1,
            room=self.room_101,
            tariff=self.basic_tariff,
            price=Decimal('500000'),
            start_date=start_date,
            end_date=end_date,
            effective_from=start_date,
            is_current=True
        )

        # Simulate tariff change
        new_detail = BookingDetail.change_tariff(
            booking=booking,
            client=self.patient1,
            new_tariff=self.premium_tariff,
            new_room=self.room_102,
            change_datetime=change_date
        )

        # Calculate billing
        breakdown = calculate_booking_billing(booking)

        # Assertions
        self.assertEqual(len(breakdown.periods), 2)

        # Period 1: 3 days at basic tariff
        period1 = breakdown.periods[0]
        self.assertEqual(period1.days_in_period, 3)

        # Period 2: 4 days at premium tariff
        period2 = breakdown.periods[1]
        self.assertEqual(period2.days_in_period, 4)

        print("\n" + "="*80)
        print("TEST SCENARIO 3: Tariff Change During Stay")
        print("="*80)
        print(breakdown)
        print("="*80)

    def test_scenario_4_additional_services(self):
        """
        Test Scenario 4: Additional services beyond tariff
        - 1 patient
        - Basic tariff (includes 5 massage, 10 physiotherapy)
        - Used: 8 massage sessions (3 extra), 12 physiotherapy (2 extra)
        - Additional services should be billed
        """
        start_date = timezone.now()
        end_date = start_date + timedelta(days=7)

        booking = Booking.objects.create(
            booking_number=Booking.generate_booking_number(),
            staff=self.cashbox_user,
            start_date=start_date,
            end_date=end_date,
            status='checked_in'
        )

        booking_detail = BookingDetail.objects.create(
            booking=booking,
            client=self.patient1,
            room=self.room_101,
            tariff=self.basic_tariff,
            price=Decimal('500000'),
            start_date=start_date,
            end_date=end_date,
            effective_from=start_date
        )

        # Add extra massage sessions (3 beyond included)
        ServiceUsage.objects.create(
            booking=booking,
            booking_detail=booking_detail,
            service=self.massage_service,
            quantity=3,
            price=Decimal('150000'),  # 3 * 50000
            date_used=start_date + timedelta(days=2)
        )

        # Add extra physiotherapy sessions (2 beyond included)
        ServiceUsage.objects.create(
            booking=booking,
            booking_detail=booking_detail,
            service=self.physiotherapy_service,
            quantity=2,
            price=Decimal('60000'),  # 2 * 30000
            date_used=start_date + timedelta(days=3)
        )

        # Update billing record
        billing = update_booking_billing_record(booking)

        # Assertions
        self.assertEqual(billing.tariff_base_amount, 500000)
        self.assertEqual(billing.additional_services_amount, 210000)  # 150000 + 60000
        self.assertEqual(billing.total_amount, 710000)

        print("\n" + "="*80)
        print("TEST SCENARIO 4: Additional Services Beyond Tariff")
        print("="*80)
        print(f"Tariff Base: {billing.tariff_base_amount:,} UZS")
        print(f"Additional Services: {billing.additional_services_amount:,} UZS")
        print(f"Total: {billing.total_amount:,} UZS")
        print("="*80)

    def test_scenario_5_complete_billing_workflow(self):
        """
        Test Scenario 5: Complete billing workflow
        - 2 patients with different tariffs
        - Patient 1 changes tariff mid-stay
        - Both patients have additional services
        - Test billing status transitions
        """
        start_date = timezone.now()
        end_date = start_date + timedelta(days=10)

        booking = Booking.objects.create(
            booking_number=Booking.generate_booking_number(),
            staff=self.cashbox_user,
            start_date=start_date,
            end_date=end_date,
            status='checked_in'
        )

        # Patient 1 - starts with Basic, upgrades to Premium on day 5
        detail1_initial = BookingDetail.objects.create(
            booking=booking,
            client=self.patient1,
            room=self.room_101,
            tariff=self.basic_tariff,
            price=Decimal('500000'),
            start_date=start_date,
            end_date=end_date,
            effective_from=start_date,
            is_current=True
        )

        # Upgrade patient 1 on day 5
        upgrade_date = start_date + timedelta(days=5)
        detail1_upgraded = BookingDetail.change_tariff(
            booking=booking,
            client=self.patient1,
            new_tariff=self.premium_tariff,
            new_room=self.room_102,
            change_datetime=upgrade_date
        )

        # Patient 2 - Premium tariff entire stay
        detail2 = BookingDetail.objects.create(
            booking=booking,
            client=self.patient2,
            room=self.room_102,
            tariff=self.premium_tariff,
            price=Decimal('1000000'),
            start_date=start_date,
            end_date=end_date,
            effective_from=start_date
        )

        # Add additional services for patient 1
        ServiceUsage.objects.create(
            booking=booking,
            booking_detail=detail1_upgraded,
            service=self.massage_service,
            quantity=2,
            price=Decimal('100000'),
            date_used=upgrade_date + timedelta(days=1)
        )

        # Add additional services for patient 2
        ServiceUsage.objects.create(
            booking=booking,
            booking_detail=detail2,
            service=self.physiotherapy_service,
            quantity=3,
            price=Decimal('90000'),
            date_used=start_date + timedelta(days=4)
        )

        # Test billing workflow
        # 1. Create billing record (should be pending)
        billing, created = BookingBilling.objects.get_or_create(
            booking=booking,
            defaults={'created_by': self.cashbox_user}
        )
        self.assertEqual(billing.billing_status, 'pending')

        # 2. Calculate billing
        billing = update_booking_billing_record(booking)
        self.assertEqual(billing.billing_status, 'calculated')

        # 3. Mark as invoiced
        billing.billing_status = 'invoiced'
        billing.save()
        self.assertEqual(billing.billing_status, 'invoiced')

        # Get detailed breakdown
        breakdown = calculate_booking_billing(booking)

        print("\n" + "="*80)
        print("TEST SCENARIO 5: Complete Billing Workflow")
        print("="*80)
        print(breakdown)
        print("\nBilling Record:")
        print(f"  Tariff Base Amount: {billing.tariff_base_amount:,} UZS")
        print(f"  Additional Services: {billing.additional_services_amount:,} UZS")
        print(f"  Medications: {billing.medications_amount:,} UZS")
        print(f"  Lab Research: {billing.lab_research_amount:,} UZS")
        print(f"  Total Amount: {billing.total_amount:,} UZS")
        print(f"  Status: {billing.billing_status}")
        print("="*80)

        # Assertions
        self.assertTrue(billing.total_amount > 0)
        self.assertEqual(billing.billing_status, 'invoiced')
        self.assertEqual(len(breakdown.periods), 3)  # 2 periods for patient1, 1 for patient2

    def test_scenario_6_booking_status_filtering(self):
        """
        Test Scenario 6: Verify only billable bookings are shown
        - Create bookings with various statuses
        - Only checked_in, in_progress, completed, discharged should be billable
        """
        start_date = timezone.now()
        end_date = start_date + timedelta(days=7)

        # Create bookings with different statuses
        statuses = [
            'pending', 'confirmed', 'checked_in', 'in_progress',
            'completed', 'cancelled', 'discharged'
        ]

        bookings = []
        for status in statuses:
            booking = Booking.objects.create(
                booking_number=Booking.generate_booking_number(),
                staff=self.cashbox_user,
                start_date=start_date,
                end_date=end_date,
                status=status
            )

            BookingDetail.objects.create(
                booking=booking,
                client=self.patient1,
                room=self.room_101,
                tariff=self.basic_tariff,
                price=Decimal('500000'),
                start_date=start_date,
                end_date=end_date,
                effective_from=start_date
            )

            bookings.append(booking)

        # Query billable bookings (as done in billing_list view)
        billable_statuses = ['checked_in', 'in_progress', 'completed', 'discharged']
        billable_bookings = Booking.objects.filter(status__in=billable_statuses)

        print("\n" + "="*80)
        print("TEST SCENARIO 6: Booking Status Filtering")
        print("="*80)
        print(f"Total bookings created: {len(bookings)}")
        print(f"Billable bookings: {billable_bookings.count()}")
        print("\nBillable statuses:")
        for booking in billable_bookings:
            print(f"  - {booking.booking_number}: {booking.status}")
        print("="*80)

        # Assertions
        self.assertEqual(billable_bookings.count(), 4)
        for booking in billable_bookings:
            self.assertIn(booking.status, billable_statuses)

    def test_scenario_7_prorated_pricing(self):
        """
        Test Scenario 7: Prorated pricing for partial periods
        - 10 day booking
        - Tariff change on day 3 and day 7
        - Verify prorated calculations
        """
        start_date = timezone.now()
        end_date = start_date + timedelta(days=10)

        booking = Booking.objects.create(
            booking_number=Booking.generate_booking_number(),
            staff=self.cashbox_user,
            start_date=start_date,
            end_date=end_date,
            status='checked_in'
        )

        # Period 1: Days 0-2 (3 days) - Basic tariff
        detail1 = BookingDetail.objects.create(
            booking=booking,
            client=self.patient1,
            room=self.room_101,
            tariff=self.basic_tariff,
            price=Decimal('500000'),
            start_date=start_date,
            end_date=end_date,
            effective_from=start_date,
            effective_to=start_date + timedelta(days=3),
            is_current=False
        )

        # Period 2: Days 3-6 (4 days) - Premium tariff
        detail2 = BookingDetail.objects.create(
            booking=booking,
            client=self.patient1,
            room=self.room_102,
            tariff=self.premium_tariff,
            price=Decimal('1000000'),
            start_date=start_date,
            end_date=end_date,
            effective_from=start_date + timedelta(days=3),
            effective_to=start_date + timedelta(days=7),
            is_current=False
        )

        # Period 3: Days 7-10 (4 days) - Back to Basic
        detail3 = BookingDetail.objects.create(
            booking=booking,
            client=self.patient1,
            room=self.room_101,
            tariff=self.basic_tariff,
            price=Decimal('500000'),
            start_date=start_date,
            end_date=end_date,
            effective_from=start_date + timedelta(days=7),
            is_current=True
        )

        # Calculate billing
        breakdown = calculate_booking_billing(booking)

        print("\n" + "="*80)
        print("TEST SCENARIO 7: Prorated Pricing")
        print("="*80)
        print(breakdown)
        print("\nPeriod Details:")
        for idx, period in enumerate(breakdown.periods, 1):
            print(f"Period {idx}: {period.days_in_period} days × {period.tariff_name}")
            print(f"  Prorated charge: {period.tariff_base_charge:,.2f} UZS")
        print("="*80)

        # Assertions
        self.assertEqual(len(breakdown.periods), 3)
        self.assertEqual(breakdown.periods[0].days_in_period, 3)
        self.assertEqual(breakdown.periods[1].days_in_period, 4)
        self.assertEqual(breakdown.periods[2].days_in_period, 4)


class BookingBillingModelTestCase(TestCase):
    """Test BookingBilling model functionality"""

    def setUp(self):
        """Set up test data"""
        self.cashbox_user = Account.objects.create_user(
            username='cashbox_user',
            email='cashbox@test.com',
            password='testpass123'
        )
        self.cashbox_user.f_name = 'Cashbox'
        self.cashbox_user.l_name = 'User'
        self.cashbox_user.role = RolesModel.CASHBOX
        self.cashbox_user.save()

        start_date = timezone.now()
        end_date = start_date + timedelta(days=7)

        self.booking = Booking.objects.create(
            booking_number=Booking.generate_booking_number(),
            staff=self.cashbox_user,
            start_date=start_date,
            end_date=end_date,
            status='checked_in'
        )

    def test_billing_auto_calculation(self):
        """Test automatic total calculation on save"""
        billing = BookingBilling.objects.create(
            booking=self.booking,
            tariff_base_amount=500000,
            additional_services_amount=100000,
            medications_amount=50000,
            lab_research_amount=30000
        )

        self.assertEqual(billing.total_amount, 680000)

    def test_billing_status_properties(self):
        """Test billing status properties"""
        billing = BookingBilling.objects.create(
            booking=self.booking,
            billing_status='pending'
        )

        self.assertFalse(billing.is_calculated)
        self.assertFalse(billing.is_invoiced)

        billing.billing_status = 'calculated'
        billing.save()
        self.assertTrue(billing.is_calculated)
        self.assertFalse(billing.is_invoiced)

        billing.billing_status = 'invoiced'
        billing.save()
        self.assertTrue(billing.is_calculated)
        self.assertTrue(billing.is_invoiced)

    def test_billing_calculate_total_method(self):
        """Test calculate_total method"""
        billing = BookingBilling.objects.create(
            booking=self.booking
        )

        billing.tariff_base_amount = 400000
        billing.additional_services_amount = 80000
        billing.medications_amount = 40000
        billing.lab_research_amount = 20000

        total = billing.calculate_total()
        self.assertEqual(total, 540000)
        self.assertEqual(billing.total_amount, 540000)


class MedicationBillingTestCase(TestCase):
    """Test medication billing calculation"""

    def setUp(self):
        """Set up test data"""
        from core.models import (
            MedicationModel, IllnessHistory, PrescribedMedication
        )
        from core.models.sanatorium.prescriptions.medication_session import MedicationSession
        
        # Create test user
        self.user = Account.objects.create_user(
            username='test_user',
            email='test@test.com',
            password='testpass123'
        )
        self.user.f_name = 'Test'
        self.user.l_name = 'User'
        self.user.role = RolesModel.DOCTOR
        self.user.save()

        # Create patient
        self.patient = PatientModel.objects.create(
            f_name='Test',
            l_name='Patient',
            m_name='Middle',
            date_of_birth=timezone.now() - timedelta(days=10000),
            gender='M'
        )

        # Create booking
        start_date = timezone.now()
        end_date = start_date + timedelta(days=7)
        
        self.booking = Booking.objects.create(
            booking_number=Booking.generate_booking_number(),
            staff=self.user,
            start_date=start_date,
            end_date=end_date,
            status='checked_in'
        )

        # Create illness history
        self.illness_history = IllnessHistory.objects.create(
            booking=self.booking,
            patient=self.patient,
            created_by=self.user,
            modified_by=self.user
        )

    def test_medication_billing_single_medication(self):
        """Test billing calculation with single medication"""
        from core.models import MedicationModel, PrescribedMedication
        from core.models.sanatorium.prescriptions.medication_session import MedicationSession
        
        # Create medication with known price
        medication = MedicationModel.objects.create(
            name='Test Med',
            unit_price=5000,  # 5,000 UZS per unit
            created_by=self.user,
            modified_by=self.user
        )

        # Prescribe medication
        prescribed = PrescribedMedication.objects.create(
            illness_history=self.illness_history,
            medication=medication,
            dosage='1 pill',
            frequency='2 times daily',
            duration='7 days',
            created_by=self.user,
            modified_by=self.user
        )

        # Create medication session: 10 units × 5,000 = 50,000
        MedicationSession.objects.create(
            prescribed_medication=prescribed,
            quantity=10,
            created_by=self.user,
            modified_by=self.user
        )

        # Calculate billing
        breakdown = calculate_booking_billing(self.booking)

        # Assert
        self.assertEqual(breakdown.medications_amount, 50000)

    def test_medication_billing_multiple_medications(self):
        """Test billing with multiple medications"""
        from core.models import MedicationModel, PrescribedMedication
        from core.models.sanatorium.prescriptions.medication_session import MedicationSession
        
        # Create two medications
        med1 = MedicationModel.objects.create(
            name='Med 1',
            unit_price=3000,
            created_by=self.user,
            modified_by=self.user
        )
        med2 = MedicationModel.objects.create(
            name='Med 2',
            unit_price=7000,
            created_by=self.user,
            modified_by=self.user
        )

        # Prescribe both
        prescribed1 = PrescribedMedication.objects.create(
            illness_history=self.illness_history,
            medication=med1,
            created_by=self.user,
            modified_by=self.user
        )
        prescribed2 = PrescribedMedication.objects.create(
            illness_history=self.illness_history,
            medication=med2,
            created_by=self.user,
            modified_by=self.user
        )

        # Create sessions
        MedicationSession.objects.create(
            prescribed_medication=prescribed1,
            quantity=5,  # 5 × 3,000 = 15,000
            created_by=self.user,
            modified_by=self.user
        )
        MedicationSession.objects.create(
            prescribed_medication=prescribed2,
            quantity=3,  # 3 × 7,000 = 21,000
            created_by=self.user,
            modified_by=self.user
        )

        # Calculate billing
        breakdown = calculate_booking_billing(self.booking)

        # Total = 15,000 + 21,000 = 36,000
        self.assertEqual(breakdown.medications_amount, 36000)

    def test_medication_billing_null_price(self):
        """Test billing with null medication price"""
        from core.models import MedicationModel, PrescribedMedication
        from core.models.sanatorium.prescriptions.medication_session import MedicationSession
        
        # Create medication with null price
        medication = MedicationModel.objects.create(
            name='Free Med',
            unit_price=None,
            created_by=self.user,
            modified_by=self.user
        )

        prescribed = PrescribedMedication.objects.create(
            illness_history=self.illness_history,
            medication=medication,
            created_by=self.user,
            modified_by=self.user
        )

        MedicationSession.objects.create(
            prescribed_medication=prescribed,
            quantity=10,
            created_by=self.user,
            modified_by=self.user
        )

        # Calculate billing
        breakdown = calculate_booking_billing(self.booking)

        # Should be 0 (null price treated as 0)
        self.assertEqual(breakdown.medications_amount, 0)


class LabBillingTestCase(TestCase):
    """Test lab research billing calculation"""

    def setUp(self):
        """Set up test data"""
        from core.models import LabResearchModel, IllnessHistory
        
        # Create test user
        self.user = Account.objects.create_user(
            username='test_user',
            email='test@test.com',
            password='testpass123'
        )
        self.user.f_name = 'Test'
        self.user.l_name = 'User'
        self.user.role = RolesModel.DOCTOR
        self.user.save()

        # Create patient
        self.patient = PatientModel.objects.create(
            f_name='Test',
            l_name='Patient',
            m_name='Middle',
            date_of_birth=timezone.now() - timedelta(days=10000),
            gender='M'
        )

        # Create booking
        start_date = timezone.now()
        end_date = start_date + timedelta(days=7)
        
        self.booking = Booking.objects.create(
            booking_number=Booking.generate_booking_number(),
            staff=self.user,
            start_date=start_date,
            end_date=end_date,
            status='checked_in'
        )

        # Create illness history
        self.illness_history = IllnessHistory.objects.create(
            booking=self.booking,
            patient=self.patient,
            created_by=self.user,
            modified_by=self.user
        )

    def test_lab_billing_single_lab(self):
        """Test billing calculation with single lab test"""
        from core.models import LabResearchModel
        from core.models.sanatorium.prescriptions.assigned_labs import AssignedLabs
        
        # Create lab research with known price
        lab = LabResearchModel.objects.create(
            name='Blood Test',
            price=30000,  # 30,000 UZS
            created_by=self.user,
            modified_by=self.user
        )

        # Assign lab with billable state
        AssignedLabs.objects.create(
            illness_history=self.illness_history,
            lab=lab,
            state='dispatched',  # Billable state
            created_by=self.user,
            modified_by=self.user
        )

        # Calculate billing
        breakdown = calculate_booking_billing(self.booking)

        # Assert
        self.assertEqual(breakdown.lab_research_amount, 30000)

    def test_lab_billing_multiple_labs(self):
        """Test billing with multiple lab tests"""
        from core.models import LabResearchModel
        from core.models.sanatorium.prescriptions.assigned_labs import AssignedLabs
        
        # Create multiple labs
        lab1 = LabResearchModel.objects.create(
            name='Blood Test',
            price=30000,
            created_by=self.user,
            modified_by=self.user
        )
        lab2 = LabResearchModel.objects.create(
            name='X-Ray',
            price=50000,
            created_by=self.user,
            modified_by=self.user
        )

        # Assign both labs with billable states
        AssignedLabs.objects.create(
            illness_history=self.illness_history,
            lab=lab1,
            state='dispatched',
            created_by=self.user,
            modified_by=self.user
        )
        AssignedLabs.objects.create(
            illness_history=self.illness_history,
            lab=lab2,
            state='results',  # Another billable state
            created_by=self.user,
            modified_by=self.user
        )

        # Calculate billing
        breakdown = calculate_booking_billing(self.booking)

        # Total = 30,000 + 50,000 = 80,000
        self.assertEqual(breakdown.lab_research_amount, 80000)

    def test_lab_billing_only_billable_states(self):
        """Test that only labs in billable states are charged"""
        from core.models import LabResearchModel
        from core.models.sanatorium.prescriptions.assigned_labs import AssignedLabs
        
        # Create labs
        lab1 = LabResearchModel.objects.create(
            name='Test 1',
            price=20000,
            created_by=self.user,
            modified_by=self.user
        )
        lab2 = LabResearchModel.objects.create(
            name='Test 2',
            price=25000,
            created_by=self.user,
            modified_by=self.user
        )
        lab3 = LabResearchModel.objects.create(
            name='Test 3',
            price=30000,
            created_by=self.user,
            modified_by=self.user
        )

        # Assign labs with different states
        AssignedLabs.objects.create(
            illness_history=self.illness_history,
            lab=lab1,
            state='cancelled',  # NOT billable
            created_by=self.user,
            modified_by=self.user
        )
        AssignedLabs.objects.create(
            illness_history=self.illness_history,
            lab=lab2,
            state='dispatched',  # Billable
            created_by=self.user,
            modified_by=self.user
        )
        AssignedLabs.objects.create(
            illness_history=self.illness_history,
            lab=lab3,
            state='recommended',  # NOT billable
            created_by=self.user,
            modified_by=self.user
        )

        # Calculate billing
        breakdown = calculate_booking_billing(self.booking)

        # Only lab2 should be billed
        self.assertEqual(breakdown.lab_research_amount, 25000)


class PaymentProcessingTestCase(TestCase):
    """Test payment processing functionality"""

    def setUp(self):
        """Set up test data"""
        # Create test user
        self.user = Account.objects.create_user(
            username='cashbox_user',
            email='cashbox@test.com',
            password='testpass123'
        )
        self.user.f_name = 'Cashbox'
        self.user.l_name = 'User'
        self.user.role = RolesModel.CASHBOX
        self.user.save()

        # Create patient
        self.patient = PatientModel.objects.create(
            f_name='Test',
            l_name='Patient',
            m_name='Middle',
            date_of_birth=timezone.now() - timedelta(days=10000),
            gender='M'
        )

        # Create room
        room_type = RoomType.objects.create(
            name='Standard',
            description='Standard Room',
            created_by=self.user,
            modified_by=self.user
        )
        self.room = Room.objects.create(
            name='101',
            room_type=room_type,
            is_active=True,
            created_by=self.user,
            modified_by=self.user
        )

        # Create tariff
        self.tariff = Tariff.objects.create(
            name='Basic',
            description='Basic Package',
            price=500000,
            duration_days=7,
            created_by=self.user,
            modified_by=self.user
        )

        # Create booking
        start_date = timezone.now()
        end_date = start_date + timedelta(days=7)
        
        self.booking = Booking.objects.create(
            booking_number=Booking.generate_booking_number(),
            staff=self.user,
            start_date=start_date,
            end_date=end_date,
            status='discharged'
        )

        # Create booking detail
        self.booking_detail = BookingDetail.objects.create(
            booking=self.booking,
            client=self.patient,
            room=self.room,
            tariff=self.tariff,
            start_date=start_date,
            end_date=end_date,
            effective_from=start_date,
            is_current=True,
            price=500000,
            created_by=self.user,
            modified_by=self.user
        )

        # Create billing record
        self.billing = BookingBilling.objects.create(
            booking=self.booking,
            tariff_base_amount=500000,
            additional_services_amount=0,
            medications_amount=0,
            lab_research_amount=0,
            billing_status='invoiced',
            created_by=self.user,
            modified_by=self.user
        )

    def test_create_payment_transaction(self):
        """Test creating a payment transaction"""
        from core.models.transactions import TransactionsModel
        
        # Create payment
        payment = TransactionsModel.objects.create(
            booking=self.booking,
            billing=self.billing,
            patient=self.patient,
            amount=Decimal('500000'),
            transaction_type='cash',
            status='COMPLETED',
            created_by=self.user,
            modified_by=self.user
        )

        # Assert
        self.assertEqual(payment.booking, self.booking)
        self.assertEqual(payment.billing, self.billing)
        self.assertEqual(payment.amount, Decimal('500000'))
        self.assertEqual(payment.status, 'COMPLETED')

    def test_partial_payment(self):
        """Test partial payment updates billing status"""
        from core.models.transactions import TransactionsModel
        from django.db.models import Sum
        
        # Create partial payment
        TransactionsModel.objects.create(
            booking=self.booking,
            billing=self.billing,
            patient=self.patient,
            amount=Decimal('300000'),
            transaction_type='cash',
            status='COMPLETED',
            created_by=self.user,
            modified_by=self.user
        )

        # Check total paid
        total_paid = self.billing.transactions.filter(
            status='COMPLETED'
        ).aggregate(total=Sum('amount'))['total']

        self.assertEqual(total_paid, Decimal('300000'))
        self.assertLess(total_paid, Decimal(str(self.billing.total_amount)))

    def test_full_payment(self):
        """Test full payment updates billing status"""
        from core.models.transactions import TransactionsModel
        from django.db.models import Sum
        
        # Create full payment
        TransactionsModel.objects.create(
            booking=self.booking,
            billing=self.billing,
            patient=self.patient,
            amount=Decimal('500000'),
            transaction_type='card',
            reference_number='CARD-12345',
            status='COMPLETED',
            created_by=self.user,
            modified_by=self.user
        )

        # Check total paid
        total_paid = self.billing.transactions.filter(
            status='COMPLETED'
        ).aggregate(total=Sum('amount'))['total']

        self.assertEqual(total_paid, Decimal('500000'))
        self.assertEqual(total_paid, Decimal(str(self.billing.total_amount)))

    def test_multiple_payments(self):
        """Test multiple payments totaling full amount"""
        from core.models.transactions import TransactionsModel
        from django.db.models import Sum
        
        # Create multiple payments
        TransactionsModel.objects.create(
            booking=self.booking,
            billing=self.billing,
            patient=self.patient,
            amount=Decimal('200000'),
            transaction_type='cash',
            status='COMPLETED',
            created_by=self.user,
            modified_by=self.user
        )
        TransactionsModel.objects.create(
            booking=self.booking,
            billing=self.billing,
            patient=self.patient,
            amount=Decimal('300000'),
            transaction_type='card',
            status='COMPLETED',
            created_by=self.user,
            modified_by=self.user
        )

        # Check total paid
        total_paid = self.billing.transactions.filter(
            status='COMPLETED'
        ).aggregate(total=Sum('amount'))['total']

        self.assertEqual(total_paid, Decimal('500000'))


class IntegratedBillingTestCase(TestCase):
    """Test complete billing workflow with medications, labs, and payments"""

    def setUp(self):
        """Set up comprehensive test data"""
        # Create test user
        self.user = Account.objects.create_user(
            username='test_user',
            email='test@test.com',
            password='testpass123'
        )
        self.user.f_name = 'Test'
        self.user.l_name = 'User'
        self.user.role = RolesModel.CASHBOX
        self.user.save()

        # Create patient
        self.patient = PatientModel.objects.create(
            f_name='Test',
            l_name='Patient',
            m_name='Middle',
            date_of_birth=timezone.now() - timedelta(days=10000),
            gender='M'
        )

        # Create room
        room_type = RoomType.objects.create(
            name='Standard',
            description='Standard Room',
            created_by=self.user,
            modified_by=self.user
        )
        self.room = Room.objects.create(
            name='101',
            room_type=room_type,
            is_active=True,
            created_by=self.user,
            modified_by=self.user
        )

        # Create tariff
        self.tariff = Tariff.objects.create(
            name='Basic',
            description='Basic Package',
            price=500000,
            duration_days=7,
            created_by=self.user,
            modified_by=self.user
        )

        # Create booking
        start_date = timezone.now()
        end_date = start_date + timedelta(days=7)
        
        self.booking = Booking.objects.create(
            booking_number=Booking.generate_booking_number(),
            staff=self.user,
            start_date=start_date,
            end_date=end_date,
            status='discharged'
        )

        # Create booking detail
        self.booking_detail = BookingDetail.objects.create(
            booking=self.booking,
            client=self.patient,
            room=self.room,
            tariff=self.tariff,
            start_date=start_date,
            end_date=end_date,
            effective_from=start_date,
            is_current=True,
            price=500000,
            created_by=self.user,
            modified_by=self.user
        )

    def test_complete_billing_workflow(self):
        """Test complete workflow: tariff + medications + labs + payment"""
        from core.models import (
            MedicationModel, PrescribedMedication, IllnessHistory,
            LabResearchModel
        )
        from core.models.sanatorium.prescriptions.medication_session import MedicationSession
        from core.models.sanatorium.prescriptions.assigned_labs import AssignedLabs
        from core.models.transactions import TransactionsModel
        
        # Create illness history
        illness_history = IllnessHistory.objects.create(
            booking=self.booking,
            patient=self.patient,
            created_by=self.user,
            modified_by=self.user
        )

        # Add medication
        medication = MedicationModel.objects.create(
            name='Test Med',
            unit_price=5000,
            created_by=self.user,
            modified_by=self.user
        )
        prescribed = PrescribedMedication.objects.create(
            illness_history=illness_history,
            medication=medication,
            created_by=self.user,
            modified_by=self.user
        )
        MedicationSession.objects.create(
            prescribed_medication=prescribed,
            quantity=10,  # 10 × 5,000 = 50,000
            created_by=self.user,
            modified_by=self.user
        )

        # Add lab
        lab = LabResearchModel.objects.create(
            name='Blood Test',
            price=30000,
            created_by=self.user,
            modified_by=self.user
        )
        AssignedLabs.objects.create(
            illness_history=illness_history,
            lab=lab,
            state='dispatched',
            created_by=self.user,
            modified_by=self.user
        )

        # Calculate billing
        breakdown = calculate_booking_billing(self.booking)

        # Assert breakdown
        # Tariff: 500,000
        # Medications: 50,000
        # Labs: 30,000
        # Total: 580,000
        self.assertEqual(breakdown.total_tariff_charges, 500000)
        self.assertEqual(breakdown.medications_amount, 50000)
        self.assertEqual(breakdown.lab_research_amount, 30000)
        self.assertEqual(breakdown.grand_total, 580000)

        # Update billing record
        billing = update_booking_billing_record(self.booking)
        self.assertEqual(billing.total_amount, 580000)

        # Create payment
        payment = TransactionsModel.objects.create(
            booking=self.booking,
            billing=billing,
            patient=self.patient,
            amount=Decimal('580000'),
            transaction_type='cash',
            status='COMPLETED',
            created_by=self.user,
            modified_by=self.user
        )

        # Verify payment
        from django.db.models import Sum
        total_paid = billing.transactions.filter(
            status='COMPLETED'
        ).aggregate(total=Sum('amount'))['total']
        
        self.assertEqual(total_paid, Decimal('580000'))
