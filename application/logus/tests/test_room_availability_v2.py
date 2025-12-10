"""
Tests for Room Availability Matrix V2 (RM2) feature

FEATURE: RM2 - Room Availability V2
"""

from datetime import date, timedelta
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone

from core.models.rooms import Room, RoomType, RoomMaintenance
from core.models.booking import Booking, BookingDetail
from core.models.clients import PatientModel
from core.models.tariffs import Tariff

from application.logus.services.room_availability_v2 import (
    get_availability_matrix_v2,
    validate_booking_from_matrix
)

User = get_user_model()


class RoomAvailabilityV2ServiceTests(TestCase):
    """Test cases for RM2 service layer functions"""

    def setUp(self):
        """Set up test data"""
        # Create room type
        self.room_type = RoomType.objects.create(
            name="Standard",
            description="Standard room type"
        )

        # Create rooms
        self.room1 = Room.objects.create(
            name="Room 101",
            room_type=self.room_type,
            capacity=2,
            price=15000,
            is_active=True
        )

        self.room2 = Room.objects.create(
            name="Room 102",
            room_type=self.room_type,
            capacity=2,
            price=15000,
            is_active=True
        )

        # Create patient
        self.patient = PatientModel.objects.create(
            first_name="Test",
            last_name="Patient",
            date_of_birth=date(1980, 1, 1),
            gender="M"
        )

        # Create tariff
        self.tariff = Tariff.objects.create(
            name="Standard Care",
            is_active=True
        )

        # Create user
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

    def test_get_availability_matrix_v2_basic(self):
        """Test basic matrix generation"""
        start_date = date.today()
        end_date = start_date + timedelta(days=7)

        matrix_data = get_availability_matrix_v2(
            start_date=start_date,
            end_date=end_date
        )

        # Check structure
        self.assertIn('period', matrix_data)
        self.assertIn('statistics', matrix_data)
        self.assertIn('room_types', matrix_data)

        # Check period data
        self.assertEqual(matrix_data['period']['start'], start_date)
        self.assertEqual(matrix_data['period']['end'], end_date)
        self.assertEqual(matrix_data['period']['total_days'], 8)  # inclusive

        # Check room types
        self.assertEqual(len(matrix_data['room_types']), 1)
        self.assertEqual(matrix_data['room_types'][0]['name'], 'Standard')
        self.assertEqual(matrix_data['room_types'][0]['total_rooms'], 2)

    def test_get_availability_matrix_v2_with_booking(self):
        """Test matrix generation with existing booking"""
        start_date = date.today()
        end_date = start_date + timedelta(days=7)

        # Create a booking
        booking_start = timezone.make_aware(
            timezone.datetime.combine(start_date + timedelta(days=2), timezone.datetime.min.time())
        )
        booking_end = timezone.make_aware(
            timezone.datetime.combine(start_date + timedelta(days=5), timezone.datetime.min.time())
        )

        booking = Booking.objects.create(
            staff=self.user,
            start_date=booking_start,
            end_date=booking_end,
            status='confirmed',
            booking_number='TEST-001'
        )

        BookingDetail.objects.create(
            booking=booking,
            client=self.patient,
            room=self.room1,
            tariff=self.tariff,
            price=15000,
            start_date=booking_start,
            end_date=booking_end,
            is_current=True
        )

        matrix_data = get_availability_matrix_v2(
            start_date=start_date,
            end_date=end_date
        )

        # Find the room in the data
        room_type_data = matrix_data['room_types'][0]
        room1_data = next(r for r in room_type_data['rooms'] if r['id'] == self.room1.id)

        # Check that booking days show occupied status
        booking_day_status = room1_data['daily_status'][2]  # Day 2 (0-indexed)
        self.assertIn(booking_day_status['status'], ['occupied', 'checkin', 'checkout'])

    def test_validate_booking_from_matrix_success(self):
        """Test successful booking validation"""
        start_date = date.today() + timedelta(days=1)
        end_date = start_date + timedelta(days=3)

        is_valid, message = validate_booking_from_matrix(
            room_id=self.room1.id,
            start_date=start_date,
            end_date=end_date,
            patient_id=self.patient.id,
            tariff_id=self.tariff.id
        )

        self.assertTrue(is_valid)
        self.assertEqual(message, "Validation successful")

    def test_validate_booking_from_matrix_invalid_room(self):
        """Test booking validation with invalid room"""
        start_date = date.today() + timedelta(days=1)
        end_date = start_date + timedelta(days=3)

        is_valid, message = validate_booking_from_matrix(
            room_id=99999,  # Non-existent room
            start_date=start_date,
            end_date=end_date,
            patient_id=self.patient.id,
            tariff_id=self.tariff.id
        )

        self.assertFalse(is_valid)
        self.assertIn("not found", message.lower())

    def test_validate_booking_from_matrix_maintenance_conflict(self):
        """Test booking validation with maintenance conflict"""
        start_date = date.today() + timedelta(days=1)
        end_date = start_date + timedelta(days=3)

        # Create maintenance period
        maintenance_start = timezone.make_aware(
            timezone.datetime.combine(start_date, timezone.datetime.min.time())
        )
        maintenance_end = timezone.make_aware(
            timezone.datetime.combine(end_date, timezone.datetime.min.time())
        )

        RoomMaintenance.objects.create(
            room=self.room1,
            maintenance_type='routine',
            status='scheduled',
            start_date=maintenance_start,
            end_date=maintenance_end,
            description="Test maintenance"
        )

        is_valid, message = validate_booking_from_matrix(
            room_id=self.room1.id,
            start_date=start_date,
            end_date=end_date,
            patient_id=self.patient.id,
            tariff_id=self.tariff.id
        )

        self.assertFalse(is_valid)
        self.assertIn("maintenance", message.lower())


class RoomAvailabilityV2ViewTests(TestCase):
    """Test cases for RM2 views"""

    def setUp(self):
        """Set up test data"""
        self.client = Client()

        # Create user
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

        # Create room type and room
        self.room_type = RoomType.objects.create(name="Standard")
        self.room = Room.objects.create(
            name="Room 101",
            room_type=self.room_type,
            capacity=2,
            price=15000,
            is_active=True
        )

    def test_matrix_view_requires_login(self):
        """Test that matrix view requires authentication"""
        url = reverse('logus:room_availability_v2')
        response = self.client.get(url)

        # Should redirect to login
        self.assertEqual(response.status_code, 302)

    def test_matrix_view_loads_successfully(self):
        """Test that matrix view loads for authenticated user"""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('logus:room_availability_v2')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Room Availability Matrix')

    def test_matrix_view_with_date_parameters(self):
        """Test matrix view with custom date parameters"""
        self.client.login(username='testuser', password='testpass123')

        start_date = date.today()
        end_date = start_date + timedelta(days=14)

        url = reverse('logus:room_availability_v2')
        response = self.client.get(url, {
            'start_date': start_date.strftime('%d.%m.%Y'),
            'end_date': end_date.strftime('%d.%m.%Y')
        })

        self.assertEqual(response.status_code, 200)
        self.assertIn('matrix_data', response.context)

    def test_room_details_ajax_requires_login(self):
        """Test that room details AJAX requires authentication"""
        url = reverse('logus:room_details_ajax_v2')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 302)

    def test_room_details_ajax_with_valid_data(self):
        """Test room details AJAX with valid parameters"""
        self.client.login(username='testuser', password='testpass123')

        url = reverse('logus:room_details_ajax_v2')
        response = self.client.get(url, {
            'room_type_id': self.room_type.id,
            'start_date': date.today().strftime('%d.%m.%Y'),
            'end_date': (date.today() + timedelta(days=7)).strftime('%d.%m.%Y')
        })

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('rooms', data)

    def test_room_details_ajax_with_invalid_data(self):
        """Test room details AJAX with invalid parameters"""
        self.client.login(username='testuser', password='testpass123')

        url = reverse('logus:room_details_ajax_v2')
        response = self.client.get(url, {
            'room_type_id': 'invalid',
            'start_date': 'invalid',
            'end_date': 'invalid'
        })

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('error', data)


class RoomAvailabilityV2IntegrationTests(TestCase):
    """Integration tests for RM2 feature"""

    def setUp(self):
        """Set up comprehensive test scenario"""
        # Create multiple room types and rooms
        self.standard_type = RoomType.objects.create(name="Standard")
        self.deluxe_type = RoomType.objects.create(name="Deluxe")

        # Create standard rooms
        for i in range(1, 4):
            Room.objects.create(
                name=f"Standard {i}",
                room_type=self.standard_type,
                capacity=2,
                price=15000,
                is_active=True
            )

        # Create deluxe rooms
        for i in range(1, 3):
            Room.objects.create(
                name=f"Deluxe {i}",
                room_type=self.deluxe_type,
                capacity=3,
                price=25000,
                is_active=True
            )

        self.user = User.objects.create_user(username='testuser', password='test123')

    def test_full_matrix_generation(self):
        """Test generation of complete matrix with multiple room types"""
        start_date = date.today()
        end_date = start_date + timedelta(days=30)

        matrix_data = get_availability_matrix_v2(
            start_date=start_date,
            end_date=end_date
        )

        # Should have 2 room types
        self.assertEqual(len(matrix_data['room_types']), 2)

        # Check statistics
        self.assertEqual(matrix_data['statistics']['total_rooms'], 5)

        # Check that each room type has correct number of rooms
        standard_data = next(rt for rt in matrix_data['room_types'] if rt['name'] == 'Standard')
        deluxe_data = next(rt for rt in matrix_data['room_types'] if rt['name'] == 'Deluxe')

        self.assertEqual(standard_data['total_rooms'], 3)
        self.assertEqual(deluxe_data['total_rooms'], 2)

        # Check that daily availability data is correct length
        self.assertEqual(len(standard_data['daily_availability']), 31)  # 30 days inclusive
