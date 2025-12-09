"""
Tests for the booking patient assignment functionality (TASK-050)
Tests the third step of the booking process where patients are assigned to rooms.
"""
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta

from core.models import (
    PatientModel, Room, RoomType, Booking, BookingDetail,
    Tariff, TariffRoomPrice, Region, District
)
from application.logus.forms.booking import PatientAssignmentForm

User = get_user_model()


class PatientAssignmentFormTest(TestCase):
    """Test the PatientAssignmentForm validation and behavior"""

    def setUp(self):
        """Set up test data"""
        # Create test user
        self.user = User.objects.create_user(
            email='testuser@example.com',
            username='testuser',
            password='testpass123'
        )

        # Create region and district
        self.region = Region.objects.create(
            name='Test Region',
            is_active=True
        )
        self.district = District.objects.create(
            name='Test District',
            region=self.region,
            is_active=True
        )

        # Create room type
        self.room_type = RoomType.objects.create(
            name='Standard',
            description='Standard Room'
        )

        # Create rooms
        self.room1 = Room.objects.create(
            name='Room 101',
            room_type=self.room_type,
            is_active=True,
            price=100.00
        )
        self.room2 = Room.objects.create(
            name='Room 102',
            room_type=self.room_type,
            is_active=True,
            price=100.00
        )

        # Create patients
        self.patient1 = PatientModel.objects.create(
            f_name='John',
            l_name='Doe',
            mobile_phone_number='+998901234567',
            gender=True,  # Male
            region=self.region,
            district=self.district,
            is_active=True,
            created_by=self.user,
            modified_by=self.user
        )
        self.patient2 = PatientModel.objects.create(
            f_name='Jane',
            l_name='Smith',
            mobile_phone_number='+998901234568',
            gender=False,  # Female
            region=self.region,
            district=self.district,
            is_active=True,
            created_by=self.user,
            modified_by=self.user
        )

    def test_form_valid_with_all_patients_selected(self):
        """Test that form is valid when all rooms have patients assigned"""
        form_data = {
            'patient_0': str(self.patient1.id),
            'room_0': str(self.room1.id),
            'patient_1': str(self.patient2.id),
            'room_1': str(self.room2.id),
        }

        form = PatientAssignmentForm(
            data=form_data,
            primary_patient=self.patient1,
            selected_rooms=[self.room1, self.room2]
        )

        self.assertTrue(form.is_valid(), f"Form errors: {form.errors}")

    def test_form_invalid_when_patient_not_selected(self):
        """Test that form raises validation error when patient is not selected for a room"""
        form_data = {
            'patient_0': str(self.patient1.id),
            'room_0': str(self.room1.id),
            'patient_1': '',  # Empty - no patient selected
            'room_1': str(self.room2.id),
        }

        form = PatientAssignmentForm(
            data=form_data,
            primary_patient=self.patient1,
            selected_rooms=[self.room1, self.room2]
        )

        self.assertFalse(form.is_valid())
        # Empty fields trigger field-specific 'required' errors before clean() validation
        # So we check for either field-specific or non-field errors
        has_error = 'patient_1' in form.errors or '__all__' in form.errors
        self.assertTrue(has_error, f"Expected error for patient_1 or __all__, got: {form.errors}")

    def test_form_invalid_when_all_patients_empty(self):
        """Test validation error when no patients are selected"""
        form_data = {
            'patient_0': '',
            'room_0': str(self.room1.id),
            'patient_1': '',
            'room_1': str(self.room2.id),
        }

        form = PatientAssignmentForm(
            data=form_data,
            primary_patient=self.patient1,
            selected_rooms=[self.room1, self.room2]
        )

        self.assertFalse(form.is_valid())
        # Should get field-specific errors when fields are empty
        self.assertIn('patient_0', form.errors)

    def test_form_invalid_duplicate_patients(self):
        """Test that same patient cannot be assigned to multiple rooms"""
        form_data = {
            'patient_0': str(self.patient1.id),
            'room_0': str(self.room1.id),
            'patient_1': str(self.patient1.id),  # Same patient
            'room_1': str(self.room2.id),
        }

        form = PatientAssignmentForm(
            data=form_data,
            primary_patient=self.patient1,
            selected_rooms=[self.room1, self.room2]
        )

        self.assertFalse(form.is_valid())
        self.assertIn('Один и тот же пациент не может быть назначен на несколько комнат',
                     str(form.errors['__all__']))

    def test_get_assignments_method(self):
        """Test that get_assignments() returns correct patient-room tuples"""
        form_data = {
            'patient_0': str(self.patient1.id),
            'room_0': str(self.room1.id),
            'patient_1': str(self.patient2.id),
            'room_1': str(self.room2.id),
        }

        form = PatientAssignmentForm(
            data=form_data,
            primary_patient=self.patient1,
            selected_rooms=[self.room1, self.room2]
        )

        self.assertTrue(form.is_valid())
        assignments = form.get_assignments()

        self.assertEqual(len(assignments), 2)
        self.assertEqual(assignments[0], (self.patient1.id, self.room1.id))
        self.assertEqual(assignments[1], (self.patient2.id, self.room2.id))

    def test_primary_patient_preselected_for_first_room(self):
        """Test that primary patient is pre-selected for the first room"""
        form = PatientAssignmentForm(
            primary_patient=self.patient1,
            selected_rooms=[self.room1, self.room2]
        )

        self.assertEqual(form.fields['patient_0'].initial, self.patient1.id)
        self.assertIsNone(form.fields['patient_1'].initial)


class PatientAssignmentViewTest(TestCase):
    """Test the booking_assign_patients view"""

    def setUp(self):
        """Set up test data and client"""
        self.client = Client()

        # Create test user
        self.user = User.objects.create_user(
            email='testuser@example.com',
            username='testuser',
            password='testpass123'
        )
        self.client.login(email='testuser@example.com', password='testpass123')

        # Create region and district
        self.region = Region.objects.create(name='Test Region', is_active=True)
        self.district = District.objects.create(
            name='Test District',
            region=self.region,
            is_active=True
        )

        # Create room type
        self.room_type = RoomType.objects.create(
            name='Standard',
            description='Standard Room'
        )

        # Create rooms
        self.room1 = Room.objects.create(
            name='Room 101',
            room_type=self.room_type,
            is_active=True,
            price=100.00
        )
        self.room2 = Room.objects.create(
            name='Room 102',
            room_type=self.room_type,
            is_active=True,
            price=100.00
        )

        # Create patients
        self.patient1 = PatientModel.objects.create(
            f_name='John',
            l_name='Doe',
            mobile_phone_number='+998901234567',
            gender=True,  # Male
            region=self.region,
            district=self.district,
            is_active=True,
            created_by=self.user,
            modified_by=self.user
        )
        self.patient2 = PatientModel.objects.create(
            f_name='Jane',
            l_name='Smith',
            mobile_phone_number='+998901234568',
            gender=False,  # Female
            region=self.region,
            district=self.district,
            is_active=True,
            created_by=self.user,
            modified_by=self.user
        )

        # Set up session data as if we came from previous steps
        session = self.client.session
        session['booking_data'] = {
            'patient_id': self.patient1.id,
            'start_date': (timezone.now() + timedelta(days=1)).isoformat(),
            'end_date': (timezone.now() + timedelta(days=8)).isoformat(),
            'guests_count': 2,
            'selected_rooms': [self.room1.id, self.room2.id]
        }
        session.save()

    def test_view_requires_login(self):
        """Test that view redirects to login if user is not authenticated"""
        self.client.logout()
        response = self.client.get(reverse('logus:booking_assign_patients'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    def test_view_redirects_without_session_data(self):
        """Test that view redirects to start if session data is missing"""
        session = self.client.session
        del session['booking_data']
        session.save()

        response = self.client.get(reverse('logus:booking_assign_patients'))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('logus:booking_start'))

    def test_view_get_renders_form(self):
        """Test that GET request renders the form correctly"""
        response = self.client.get(reverse('logus:booking_assign_patients'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'logus/booking/booking_assign_patients.html')
        self.assertIn('form', response.context)
        self.assertIn('primary_patient', response.context)
        self.assertIn('selected_rooms', response.context)

    def test_view_post_valid_data_redirects_to_confirm(self):
        """Test that valid POST data redirects to confirmation step"""
        post_data = {
            'patient_0': str(self.patient1.id),
            'room_0': str(self.room1.id),
            'patient_1': str(self.patient2.id),
            'room_1': str(self.room2.id),
        }

        response = self.client.post(
            reverse('logus:booking_assign_patients'),
            data=post_data
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('logus:booking_confirm'))

        # Check that assignments were stored in session
        session = self.client.session
        self.assertIn('patient_assignments', session['booking_data'])
        assignments = session['booking_data']['patient_assignments']
        self.assertEqual(len(assignments), 2)

    def test_view_post_invalid_data_shows_errors(self):
        """Test that invalid POST data (missing patient) shows validation errors"""
        post_data = {
            'patient_0': str(self.patient1.id),
            'room_0': str(self.room1.id),
            'patient_1': '',  # Missing patient for second room
            'room_1': str(self.room2.id),
        }

        response = self.client.post(
            reverse('logus:booking_assign_patients'),
            data=post_data
        )

        self.assertEqual(response.status_code, 200)  # Stays on same page
        # Check that the form has errors
        self.assertIn('form', response.context)
        form = response.context['form']
        self.assertFalse(form.is_valid())
        # The error should be a non-field error about selecting all patients
        self.assertTrue(form.errors)  # Ensure there are errors

    def test_view_post_duplicate_patients_shows_error(self):
        """Test that assigning same patient to multiple rooms shows error"""
        post_data = {
            'patient_0': str(self.patient1.id),
            'room_0': str(self.room1.id),
            'patient_1': str(self.patient1.id),  # Duplicate
            'room_1': str(self.room2.id),
        }

        response = self.client.post(
            reverse('logus:booking_assign_patients'),
            data=post_data
        )

        self.assertEqual(response.status_code, 200)
        # Check that the form has the duplicate patient error
        self.assertIn('form', response.context)
        form = response.context['form']
        self.assertFalse(form.is_valid())
        self.assertIn('Один и тот же пациент не может быть назначен на несколько комнат',
                     str(form.errors))


class PatientAssignmentIntegrationTest(TestCase):
    """Integration tests for the full booking flow with patient assignment"""

    def setUp(self):
        """Set up complete booking environment"""
        self.client = Client()

        # Create user
        self.user = User.objects.create_user(
            email='testuser@example.com',
            username='testuser',
            password='testpass123'
        )
        self.client.login(email='testuser@example.com', password='testpass123')

        # Create region and district
        self.region = Region.objects.create(name='Test Region', is_active=True)
        self.district = District.objects.create(
            name='Test District',
            region=self.region,
            is_active=True
        )

        # Create room type
        self.room_type = RoomType.objects.create(
            name='Standard',
            description='Standard Room'
        )

        # Create tariff
        self.tariff = Tariff.objects.create(
            name='Standard Tariff',
            description='Standard pricing',
            is_active=True,
            created_by=self.user
        )
        TariffRoomPrice.objects.create(
            tariff=self.tariff,
            room_type=self.room_type,
            price=100.00
        )

        # Create rooms
        self.room1 = Room.objects.create(
            name='Room 101',
            room_type=self.room_type,
            is_active=True,
            price=100.00
        )
        self.room2 = Room.objects.create(
            name='Room 102',
            room_type=self.room_type,
            is_active=True,
            price=100.00
        )

        # Create patients
        self.patient1 = PatientModel.objects.create(
            f_name='John',
            l_name='Doe',
            mobile_phone_number='+998901234567',
            gender=True,  # Male
            region=self.region,
            district=self.district,
            is_active=True,
            created_by=self.user,
            modified_by=self.user
        )
        self.patient2 = PatientModel.objects.create(
            f_name='Jane',
            l_name='Smith',
            mobile_phone_number='+998901234568',
            gender=False,  # Female
            region=self.region,
            district=self.district,
            is_active=True,
            created_by=self.user,
            modified_by=self.user
        )

    def test_full_booking_flow_with_multiple_patients(self):
        """Test complete booking flow from start to confirmation with patient assignment"""
        # Step 1: Start booking
        start_date = timezone.now() + timedelta(days=1)
        end_date = start_date + timedelta(days=7)
        date_range = f"{start_date.strftime('%d.%m.%Y')} - {end_date.strftime('%d.%m.%Y')}"

        # Manually set session for step 2 (room selection)
        session = self.client.session
        session['booking_data'] = {
            'patient_id': self.patient1.id,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'guests_count': 2,
            'date_range': date_range,
            'selected_rooms': [self.room1.id, self.room2.id]
        }
        session.save()

        # Step 3: Assign patients
        response = self.client.post(
            reverse('logus:booking_assign_patients'),
            data={
                'patient_0': str(self.patient1.id),
                'room_0': str(self.room1.id),
                'patient_1': str(self.patient2.id),
                'room_1': str(self.room2.id),
            }
        )

        # Should redirect to confirmation
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('logus:booking_confirm'))

        # Step 4: Confirm booking
        response = self.client.post(
            reverse('logus:booking_confirm'),
            data={'notes': 'Test booking with multiple patients'}
        )

        # Should create booking and redirect to detail
        self.assertEqual(response.status_code, 302)

        # Verify booking was created
        booking = Booking.objects.first()
        self.assertIsNotNone(booking)
        self.assertEqual(booking.details.count(), 2)

        # Verify patient assignments
        detail1 = booking.details.filter(room=self.room1).first()
        detail2 = booking.details.filter(room=self.room2).first()

        self.assertEqual(detail1.client, self.patient1)
        self.assertEqual(detail2.client, self.patient2)
