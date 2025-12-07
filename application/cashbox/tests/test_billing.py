from django.test import TestCase
from django.contrib.auth import get_user_model
from decimal import Decimal
from datetime import datetime, timedelta

from core.models import (
    Booking, BookingBilling, PatientModel, Room, RoomType,
    Tariff, Account, IllnessHistory, Service, ServiceUsage,
    Medication, PrescribedMedication, MedicationSession,
    LabResearchModel, AssignedLabs, RolesModel, TransactionsModel
)

User = get_user_model()


def create_test_user_with_role(username, email, password, role_name):
    """Helper function to create test user with role"""
    role, _ = RolesModel.objects.get_or_create(
        name=role_name,
        defaults={'description': f'{role_name} role'}
    )
    user = Account.objects.create_user(
        username=username,
        email=email,
        password=password
    )
    user.roles.add(role)
    return user


class BillingCalculationTests(TestCase):
    """Test billing calculation functionality"""

    def setUp(self):
        """Set up test data"""
        # Create test user
        self.user = create_test_user_with_role(
            username='doctor',
            email='doctor@test.com',
            password='testpass123',
            role_name=RolesModel.DOCTOR
        )

        # Create patient
        self.patient = PatientModel.objects.create(
            first_name='Test',
            last_name='Patient',
            date_of_birth=datetime.now().date() - timedelta(days=365*30)
        )

        # Create room type and room
        self.room_type = RoomType.objects.create(
            name='Standard',
            base_price=Decimal('100000')
        )
        self.room = Room.objects.create(
            room_type=self.room_type,
            room_number='101',
            max_capacity=2
        )

        # Create tariff
        self.tariff = Tariff.objects.create(
            name='Basic Package',
            price=Decimal('500000'),
            created_by=self.user,
            modified_by=self.user
        )

        # Create services
        self.service1 = Service.objects.create(
            name='Massage',
            unit_price=Decimal('50000'),
            created_by=self.user,
            modified_by=self.user
        )
        self.service2 = Service.objects.create(
            name='Physiotherapy',
            unit_price=Decimal('40000'),
            created_by=self.user,
            modified_by=self.user
        )

        # Create booking
        self.booking = Booking.objects.create(
            check_in_date=datetime.now().date(),
            check_out_date=datetime.now().date() + timedelta(days=7),
            status='active',
            created_by=self.user,
            modified_by=self.user
        )

        # Create illness history
        self.illness_history = IllnessHistory.objects.create(
            booking=self.booking,
            patient=self.patient,
            created_by=self.user,
            modified_by=self.user
        )

    def test_medication_calculation(self):
        """Test medication billing calculation"""
        # Create medication
        medication = Medication.objects.create(
            name='Aspirin',
            unit_price=Decimal('5000'),
            created_by=self.user,
            modified_by=self.user
        )

        # Create prescribed medication
        prescribed_med = PrescribedMedication.objects.create(
            illness_history=self.illness_history,
            medication=medication,
            dosage='100mg',
            frequency='2 times daily',
            duration_days=7,
            created_by=self.user,
            modified_by=self.user
        )

        # Create medication session
        MedicationSession.objects.create(
            prescribed_medication=prescribed_med,
            quantity=Decimal('20'),
            created_by=self.user,
            modified_by=self.user
        )

        # Create billing
        from application.cashbox.views.billing import calculate_billing_amounts

        billing = BookingBilling.objects.create(
            booking=self.booking,
            billing_status='pending',
            created_by=self.user,
            modified_by=self.user
        )

        calculate_billing_amounts(self.booking, billing, self.user)

        # Check medication amount
        self.assertEqual(billing.medications_amount, 100000)  # 20 * 5000

    def test_lab_research_calculation(self):
        """Test lab research billing calculation"""
        # Create lab research
        lab_test = LabResearchModel.objects.create(
            name='Blood Test',
            price=Decimal('30000'),
            created_by=self.user,
            modified_by=self.user
        )

        # Create assigned lab (dispatched - billable)
        AssignedLabs.objects.create(
            illness_history=self.illness_history,
            lab=lab_test,
            state='dispatched',
            created_by=self.user,
            modified_by=self.user
        )

        # Create another lab (recommended - not billable)
        AssignedLabs.objects.create(
            illness_history=self.illness_history,
            lab=lab_test,
            state='recommended',
            created_by=self.user,
            modified_by=self.user
        )

        # Create billing
        from application.cashbox.views.billing import calculate_billing_amounts

        billing = BookingBilling.objects.create(
            booking=self.booking,
            billing_status='pending',
            created_by=self.user,
            modified_by=self.user
        )

        calculate_billing_amounts(self.booking, billing, self.user)

        # Check lab amount (only billable state should be counted)
        self.assertEqual(billing.lab_research_amount, 30000)

    def test_combined_billing_calculation(self):
        """Test combined billing with all components"""
        # Create medication
        medication = Medication.objects.create(
            name='Aspirin',
            unit_price=Decimal('5000'),
            created_by=self.user,
            modified_by=self.user
        )
        prescribed_med = PrescribedMedication.objects.create(
            illness_history=self.illness_history,
            medication=medication,
            dosage='100mg',
            frequency='2 times daily',
            duration_days=7,
            created_by=self.user,
            modified_by=self.user
        )
        MedicationSession.objects.create(
            prescribed_medication=prescribed_med,
            quantity=Decimal('20'),
            created_by=self.user,
            modified_by=self.user
        )

        # Create lab
        lab_test = LabResearchModel.objects.create(
            name='Blood Test',
            price=Decimal('30000'),
            created_by=self.user,
            modified_by=self.user
        )
        AssignedLabs.objects.create(
            illness_history=self.illness_history,
            lab=lab_test,
            state='results',
            created_by=self.user,
            modified_by=self.user
        )

        # Create billing
        from application.cashbox.views.billing import calculate_billing_amounts

        billing = BookingBilling.objects.create(
            booking=self.booking,
            billing_status='pending',
            created_by=self.user,
            modified_by=self.user
        )

        calculate_billing_amounts(self.booking, billing, self.user)

        # Check totals
        self.assertEqual(billing.medications_amount, 100000)  # 20 * 5000
        self.assertEqual(billing.lab_research_amount, 30000)
        # Total should be sum of all components
        expected_total = (
            billing.tariff_base_amount +
            billing.additional_services_amount +
            billing.medications_amount +
            billing.lab_research_amount
        )
        self.assertEqual(billing.total_amount, expected_total)


class BillingStatusTests(TestCase):
    """Test billing status transitions"""

    def setUp(self):
        """Set up test data"""
        # Create test user
        self.user = create_test_user_with_role(
            username='cashier4',
            email='cashier4@test.com',
            password='testpass123',
            role_name=RolesModel.CASHBOX
        )

        # Create patient
        self.patient = PatientModel.objects.create(
            first_name='Test',
            last_name='Patient',
            date_of_birth=datetime.now().date() - timedelta(days=365*30)
        )

        # Create booking
        self.booking = Booking.objects.create(
            check_in_date=datetime.now().date(),
            check_out_date=datetime.now().date() + timedelta(days=7),
            status='active',
            created_by=self.user,
            modified_by=self.user
        )

        # Create billing
        self.billing = BookingBilling.objects.create(
            booking=self.booking,
            tariff_base_amount=500000,
            additional_services_amount=100000,
            medications_amount=50000,
            lab_research_amount=30000,
            billing_status='calculated',
            created_by=self.user,
            modified_by=self.user
        )

    def test_billing_status_partial_payment(self):
        """Test billing status changes to partially_paid"""
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

        # Recalculate status
        total_paid = self.billing.transactions.filter(
            status='COMPLETED'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

        if total_paid >= Decimal(str(self.billing.total_amount)):
            self.billing.billing_status = 'paid'
        elif total_paid > 0:
            self.billing.billing_status = 'partially_paid'

        self.billing.save()

        # Check status
        self.assertEqual(self.billing.billing_status, 'partially_paid')

    def test_billing_status_full_payment(self):
        """Test billing status changes to paid"""
        from django.db.models import Sum

        # Create full payment
        TransactionsModel.objects.create(
            booking=self.booking,
            billing=self.billing,
            patient=self.patient,
            amount=self.billing.total_amount,
            transaction_type='cash',
            status='COMPLETED',
            created_by=self.user,
            modified_by=self.user
        )

        # Recalculate status
        total_paid = self.billing.transactions.filter(
            status='COMPLETED'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

        if total_paid >= Decimal(str(self.billing.total_amount)):
            self.billing.billing_status = 'paid'
        elif total_paid > 0:
            self.billing.billing_status = 'partially_paid'

        self.billing.save()

        # Check status
        self.assertEqual(self.billing.billing_status, 'paid')
