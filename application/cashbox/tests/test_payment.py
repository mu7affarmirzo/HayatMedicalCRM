from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from decimal import Decimal
from datetime import datetime, timedelta

from core.models import (
    Booking, BookingBilling, TransactionsModel,
    PatientModel, Tariff, Room, RoomType, Account, RolesModel
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


class PaymentProcessingTests(TestCase):
    """Test payment processing functionality"""

    def setUp(self):
        """Set up test data"""
        # Create test user
        self.user = create_test_user_with_role(
            username='cashier',
            email='cashier@test.com',
            password='testpass123',
            role_name=RolesModel.CASHBOX
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

        # Login
        self.client = Client()
        self.client.force_login(self.user)

    def test_accept_payment_cash(self):
        """Test accepting cash payment"""
        url = reverse('cashbox:accept_payment', args=[self.booking.id])
        data = {
            'amount': '680000',
            'payment_method': 'cash',
            'notes': 'Test cash payment'
        }

        response = self.client.post(url, data)

        # Check redirect
        self.assertEqual(response.status_code, 302)

        # Check transaction created
        transaction = TransactionsModel.objects.filter(booking=self.booking).first()
        self.assertIsNotNone(transaction)
        self.assertEqual(transaction.amount, Decimal('680000'))
        self.assertEqual(transaction.transaction_type, 'cash')
        self.assertEqual(transaction.status, 'COMPLETED')

        # Check billing status updated
        self.billing.refresh_from_db()
        self.assertEqual(self.billing.billing_status, 'paid')

    def test_accept_partial_payment(self):
        """Test accepting partial payment"""
        url = reverse('cashbox:accept_payment', args=[self.booking.id])
        data = {
            'amount': '300000',
            'payment_method': 'cash'
        }

        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)

        # Check billing status
        self.billing.refresh_from_db()
        self.assertEqual(self.billing.billing_status, 'partially_paid')

    def test_accept_payment_card_requires_reference(self):
        """Test that card payment requires reference number"""
        url = reverse('cashbox:accept_payment', args=[self.booking.id])
        data = {
            'amount': '680000',
            'payment_method': 'card',
            # Missing reference_number
        }

        response = self.client.post(url, data)

        # Should redirect back with error
        self.assertEqual(response.status_code, 302)

        # No transaction should be created
        transaction_count = TransactionsModel.objects.filter(booking=self.booking).count()
        self.assertEqual(transaction_count, 0)

    def test_accept_payment_overpayment_prevented(self):
        """Test that overpayment is prevented"""
        url = reverse('cashbox:accept_payment', args=[self.booking.id])
        data = {
            'amount': '1000000',  # More than total
            'payment_method': 'cash'
        }

        response = self.client.post(url, data)

        # Should redirect with error
        self.assertEqual(response.status_code, 302)

        # No transaction should be created
        transaction_count = TransactionsModel.objects.filter(booking=self.booking).count()
        self.assertEqual(transaction_count, 0)

    def test_multiple_payments(self):
        """Test multiple partial payments"""
        url = reverse('cashbox:accept_payment', args=[self.booking.id])

        # First payment
        self.client.post(url, {
            'amount': '300000',
            'payment_method': 'cash'
        })

        # Second payment
        self.client.post(url, {
            'amount': '380000',
            'payment_method': 'card',
            'reference_number': 'CARD-12345'
        })

        # Check total paid
        self.billing.refresh_from_db()
        self.assertEqual(self.billing.billing_status, 'paid')

        # Check transaction count
        transaction_count = TransactionsModel.objects.filter(booking=self.booking).count()
        self.assertEqual(transaction_count, 2)


class RefundProcessingTests(TestCase):
    """Test refund processing functionality"""

    def setUp(self):
        """Set up test data"""
        # Create test user
        self.user = create_test_user_with_role(
            username='cashier2',
            email='cashier2@test.com',
            password='testpass123',
            role_name=RolesModel.CASHBOX
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
            additional_services_amount=0,
            medications_amount=0,
            lab_research_amount=0,
            billing_status='paid',
            created_by=self.user,
            modified_by=self.user
        )

        # Create completed payment
        self.payment = TransactionsModel.objects.create(
            booking=self.booking,
            billing=self.billing,
            patient=self.patient,
            amount=Decimal('500000'),
            transaction_type='cash',
            status='COMPLETED',
            created_by=self.user,
            modified_by=self.user
        )

        # Login
        self.client = Client()
        self.client.force_login(self.user)

    def test_full_refund(self):
        """Test full refund"""
        url = reverse('cashbox:refund_payment', args=[self.payment.id])
        data = {
            'refund_amount': '500000',
            'refund_reason': 'Test refund',
            'confirm': True
        }

        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)

        # Check refund transaction created
        refund = TransactionsModel.objects.filter(
            reference_number=f'REFUND-{self.payment.id}'
        ).first()
        self.assertIsNotNone(refund)
        self.assertEqual(refund.amount, Decimal('-500000'))

        # Check original payment status
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, 'REFUNDED')

        # Check billing status
        self.billing.refresh_from_db()
        self.assertEqual(self.billing.billing_status, 'calculated')

    def test_partial_refund(self):
        """Test partial refund"""
        url = reverse('cashbox:refund_payment', args=[self.payment.id])
        data = {
            'refund_amount': '200000',
            'refund_reason': 'Partial refund test',
            'confirm': True
        }

        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)

        # Check refund created
        refund = TransactionsModel.objects.filter(
            reference_number=f'REFUND-{self.payment.id}'
        ).first()
        self.assertIsNotNone(refund)
        self.assertEqual(refund.amount, Decimal('-200000'))

        # Original payment should still be COMPLETED
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, 'COMPLETED')

        # Billing should be partially paid
        self.billing.refresh_from_db()
        self.assertEqual(self.billing.billing_status, 'partially_paid')

    def test_refund_already_refunded(self):
        """Test that already refunded payment cannot be refunded again"""
        self.payment.status = 'REFUNDED'
        self.payment.save()

        url = reverse('cashbox:refund_payment', args=[self.payment.id])
        data = {
            'refund_amount': '500000',
            'refund_reason': 'Test',
            'confirm': True
        }

        response = self.client.post(url, data)

        # Should redirect with error
        self.assertEqual(response.status_code, 302)

        # No new refund transaction should be created
        refund_count = TransactionsModel.objects.filter(
            reference_number=f'REFUND-{self.payment.id}'
        ).count()
        self.assertEqual(refund_count, 0)

    def test_refund_excessive_amount(self):
        """Test that refund amount cannot exceed payment amount"""
        url = reverse('cashbox:refund_payment', args=[self.payment.id])
        data = {
            'refund_amount': '600000',  # More than payment
            'refund_reason': 'Test',
            'confirm': True
        }

        response = self.client.post(url, data)

        # Should redirect with error
        self.assertEqual(response.status_code, 302)

        # No refund should be created
        refund_count = TransactionsModel.objects.filter(
            reference_number=f'REFUND-{self.payment.id}'
        ).count()
        self.assertEqual(refund_count, 0)

    def test_refund_requires_reason(self):
        """Test that refund requires a reason"""
        url = reverse('cashbox:refund_payment', args=[self.payment.id])
        data = {
            'refund_amount': '500000',
            # Missing refund_reason
            'confirm': True
        }

        response = self.client.post(url, data)

        # Should redirect with error
        self.assertEqual(response.status_code, 302)

        # No refund should be created
        refund_count = TransactionsModel.objects.filter(
            reference_number=f'REFUND-{self.payment.id}'
        ).count()
        self.assertEqual(refund_count, 0)


class PaymentReceiptTests(TestCase):
    """Test payment receipt functionality"""

    def setUp(self):
        """Set up test data"""
        # Create test user
        self.user = create_test_user_with_role(
            username='cashier3',
            email='cashier3@test.com',
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
            billing_status='paid',
            created_by=self.user,
            modified_by=self.user
        )

        # Create payment
        self.payment = TransactionsModel.objects.create(
            booking=self.booking,
            billing=self.billing,
            patient=self.patient,
            amount=Decimal('500000'),
            transaction_type='cash',
            status='COMPLETED',
            created_by=self.user,
            modified_by=self.user
        )

        # Login
        self.client = Client()
        self.client.force_login(self.user)

    def test_receipt_view(self):
        """Test that receipt view loads successfully"""
        url = reverse('cashbox:payment_receipt', args=[self.payment.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'КВИТАНЦИЯ ОБ ОПЛАТЕ')
        self.assertContains(response, 'Test Patient')
        self.assertContains(response, '500,000')
