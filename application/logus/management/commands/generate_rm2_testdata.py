"""
Management command to generate test data for RM2 (Room Availability Matrix V2)

Usage:
    python manage.py generate_rm2_testdata

This will create:
- Room types and rooms
- Test patients
- Tariff packages
- Various booking scenarios
- Maintenance periods

FEATURE: RM2 - Room Availability V2
"""

from datetime import date, timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db import transaction

from core.models.rooms import Room, RoomType, RoomMaintenance
from core.models.booking import Booking, BookingDetail
from core.models.clients import PatientModel
from core.models.tariffs import Tariff, TariffService, ServiceSessionTracking
from core.models.services import Service

User = get_user_model()


class Command(BaseCommand):
    help = 'Generate test data for RM2 Room Availability Matrix V2'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing test data before generating new data',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('Starting RM2 test data generation...'))

        if options['clear']:
            self.clear_test_data()

        with transaction.atomic():
            # Create test user if not exists
            self.user = self.get_or_create_test_user()

            # Create room types and rooms
            self.create_room_types_and_rooms()

            # Create test patients
            self.create_test_patients()

            # Create tariff packages
            self.create_tariff_packages()

            # Create diverse booking scenarios
            self.create_booking_scenarios()

            # Create maintenance periods
            self.create_maintenance_periods()

        self.stdout.write(self.style.SUCCESS('✓ RM2 test data generated successfully!'))
        self.stdout.write(self.style.SUCCESS(f'  - Created {RoomType.objects.count()} room types'))
        self.stdout.write(self.style.SUCCESS(f'  - Created {Room.objects.count()} rooms'))
        self.stdout.write(self.style.SUCCESS(f'  - Created {self.patient_count} patients'))
        self.stdout.write(self.style.SUCCESS(f'  - Created {Tariff.objects.filter(name__startswith="Test").count()} tariffs'))
        self.stdout.write(self.style.SUCCESS(f'  - Created {self.booking_count} bookings'))
        self.stdout.write(self.style.SUCCESS(f'  - Created {self.maintenance_count} maintenance periods'))
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('Access the RM2 matrix at: /logus/rooms/availability-v2/'))

    def clear_test_data(self):
        """Clear existing test data"""
        self.stdout.write('Clearing existing test data...')

        # Delete test bookings
        BookingDetail.objects.filter(
            booking__booking_number__startswith='TEST-'
        ).delete()
        Booking.objects.filter(booking_number__startswith='TEST-').delete()

        # Delete test maintenance
        RoomMaintenance.objects.filter(description__contains='Test').delete()

        # Delete test patients
        PatientModel.objects.filter(
            l_name__in=['Testov', 'Testova', 'Смагулов', 'Смагулова']
        ).delete()

        # Delete test tariffs
        Tariff.objects.filter(name__startswith='Test').delete()

        self.stdout.write(self.style.WARNING('  Test data cleared'))

    def get_or_create_test_user(self):
        """Get or create test user"""
        user, created = User.objects.get_or_create(
            username='rm2_test_user',
            defaults={
                'email': 'rm2test@hayat.kz',
                'f_name': 'RM2',
                'l_name': 'Test User'
            }
        )
        if created:
            user.set_password('test123')
            user.save()
            self.stdout.write(self.style.SUCCESS('  ✓ Created test user'))
        return user

    def create_room_types_and_rooms(self):
        """Create room types and rooms"""
        self.stdout.write('Creating room types and rooms...')

        # Get or create room types
        self.standard_type, _ = RoomType.objects.get_or_create(
            name='Standard',
            defaults={'description': 'Standard rooms with basic amenities'}
        )

        self.deluxe_type, _ = RoomType.objects.get_or_create(
            name='Deluxe',
            defaults={'description': 'Deluxe rooms with premium amenities'}
        )

        self.suite_type, _ = RoomType.objects.get_or_create(
            name='Suite',
            defaults={'description': 'Luxury suites with premium services'}
        )

        # Create Standard rooms (101-105)
        for i in range(101, 106):
            Room.objects.get_or_create(
                name=f'Room {i}',
                defaults={
                    'room_type': self.standard_type,
                    'capacity': 2,
                    'price': 15000,
                    'is_active': True
                }
            )

        # Create Deluxe rooms (201-203)
        for i in range(201, 204):
            Room.objects.get_or_create(
                name=f'Room {i}',
                defaults={
                    'room_type': self.deluxe_type,
                    'capacity': 2,
                    'price': 25000,
                    'is_active': True
                }
            )

        # Create Suite rooms (301-302)
        for i in range(301, 303):
            Room.objects.get_or_create(
                name=f'Suite {i}',
                defaults={
                    'room_type': self.suite_type,
                    'capacity': 3,
                    'price': 40000,
                    'is_active': True
                }
            )

        self.stdout.write(self.style.SUCCESS('  ✓ Room types and rooms created'))

    def create_test_patients(self):
        """Create test patients with diverse profiles"""
        self.stdout.write('Creating test patients...')

        patients_data = [
            {'f_name': 'Айгуль', 'l_name': 'Смагулова', 'gender': False, 'age_offset': 42},
            {'f_name': 'Нурлан', 'l_name': 'Смагулов', 'gender': True, 'age_offset': 45},
            {'f_name': 'Асель', 'l_name': 'Testova', 'gender': False, 'age_offset': 35},
            {'f_name': 'Болат', 'l_name': 'Testov', 'gender': True, 'age_offset': 58},
            {'f_name': 'Гульнара', 'l_name': 'Testova', 'gender': False, 'age_offset': 28},
            {'f_name': 'Даурен', 'l_name': 'Testov', 'gender': True, 'age_offset': 52},
            {'f_name': 'Жанар', 'l_name': 'Testova', 'gender': False, 'age_offset': 38},
            {'f_name': 'Ермек', 'l_name': 'Testov', 'gender': True, 'age_offset': 47},
            {'f_name': 'Камила', 'l_name': 'Testova', 'gender': False, 'age_offset': 31},
            {'f_name': 'Мурат', 'l_name': 'Testov', 'gender': True, 'age_offset': 55},
            {'f_name': 'Сауле', 'l_name': 'Testova', 'gender': False, 'age_offset': 44},
            {'f_name': 'Темир', 'l_name': 'Testov', 'gender': True, 'age_offset': 39},
            {'f_name': 'Алма', 'l_name': 'Testova', 'gender': False, 'age_offset': 33},
            {'f_name': 'Бакыт', 'l_name': 'Testov', 'gender': True, 'age_offset': 49},
            {'f_name': 'Динара', 'l_name': 'Testova', 'gender': False, 'age_offset': 36},
            {'f_name': 'Ерлан', 'l_name': 'Testov', 'gender': True, 'age_offset': 51},
            {'f_name': 'Жанна', 'l_name': 'Testova', 'gender': False, 'age_offset': 29},
            {'f_name': 'Касым', 'l_name': 'Testov', 'gender': True, 'age_offset': 62},
            {'f_name': 'Мадина', 'l_name': 'Testova', 'gender': False, 'age_offset': 40},
            {'f_name': 'Нуржан', 'l_name': 'Testov', 'gender': True, 'age_offset': 48},
        ]

        self.test_patients = []
        today = date.today()

        for patient_data in patients_data:
            age_offset = patient_data.pop('age_offset')
            birth_date = date(today.year - age_offset, 3, 15)

            patient, _ = PatientModel.objects.get_or_create(
                f_name=patient_data['f_name'],
                l_name=patient_data['l_name'],
                defaults={
                    'gender': patient_data['gender'],
                    'date_of_birth': birth_date,
                }
            )
            self.test_patients.append(patient)

        self.patient_count = len(self.test_patients)
        self.stdout.write(self.style.SUCCESS(f'  ✓ Created {self.patient_count} test patients'))

    def create_tariff_packages(self):
        """Create tariff packages"""
        self.stdout.write('Creating tariff packages...')

        self.standard_tariff, _ = Tariff.objects.get_or_create(
            name='Test Standard Care',
            defaults={
                'description': 'Standard care package for testing',
                'is_active': True,
                'price': 15000
            }
        )

        self.premium_tariff, _ = Tariff.objects.get_or_create(
            name='Test Premium Care',
            defaults={
                'description': 'Premium care package for testing',
                'is_active': True,
                'price': 25000
            }
        )

        self.vip_tariff, _ = Tariff.objects.get_or_create(
            name='Test VIP Care',
            defaults={
                'description': 'VIP care package for testing',
                'is_active': True,
                'price': 40000
            }
        )

        self.stdout.write(self.style.SUCCESS('  ✓ Tariff packages created'))

    def create_booking_scenarios(self):
        """Create diverse booking scenarios to demonstrate matrix features"""
        self.stdout.write('Creating booking scenarios...')

        today = date.today()
        rooms = list(Room.objects.filter(is_active=True))

        self.booking_count = 0

        # Scenario 1: Current bookings (already checked in) - 3 bookings
        self.create_booking(
            patient=self.test_patients[0],
            room=rooms[0],  # Room 101
            tariff=self.standard_tariff,
            start_offset=-2,  # Started 2 days ago
            duration=10,
            status='checked_in',
            description='Ongoing treatment'
        )

        self.create_booking(
            patient=self.test_patients[1],
            room=rooms[1],  # Room 102
            tariff=self.standard_tariff,
            start_offset=-1,  # Started yesterday
            duration=7,
            status='checked_in',
            description='Ongoing rehabilitation'
        )

        self.create_booking(
            patient=self.test_patients[2],
            room=rooms[5],  # Room 201 (Deluxe)
            tariff=self.premium_tariff,
            start_offset=-3,
            duration=14,
            status='in_progress',
            description='Extended care program'
        )

        # Scenario 2: Check-ins today - 2 bookings
        self.create_booking(
            patient=self.test_patients[3],
            room=rooms[2],  # Room 103
            tariff=self.standard_tariff,
            start_offset=0,  # Today
            duration=5,
            status='confirmed',
            description='Check-in today'
        )

        self.create_booking(
            patient=self.test_patients[4],
            room=rooms[6],  # Room 202
            tariff=self.premium_tariff,
            start_offset=0,
            duration=8,
            status='confirmed',
            description='Check-in today'
        )

        # Scenario 3: Check-outs tomorrow - 2 bookings
        self.create_booking(
            patient=self.test_patients[5],
            room=rooms[3],  # Room 104
            tariff=self.standard_tariff,
            start_offset=-5,
            duration=6,  # Will check out tomorrow
            status='checked_in',
            description='Check-out tomorrow'
        )

        # Scenario 4: Future bookings (confirmed) - 4 bookings
        self.create_booking(
            patient=self.test_patients[6],
            room=rooms[4],  # Room 105
            tariff=self.standard_tariff,
            start_offset=2,
            duration=7,
            status='confirmed',
            description='Future booking'
        )

        self.create_booking(
            patient=self.test_patients[7],
            room=rooms[7],  # Room 203
            tariff=self.premium_tariff,
            start_offset=3,
            duration=10,
            status='confirmed',
            description='Future premium booking'
        )

        self.create_booking(
            patient=self.test_patients[8],
            room=rooms[8],  # Suite 301
            tariff=self.vip_tariff,
            start_offset=5,
            duration=14,
            status='confirmed',
            description='Future VIP booking'
        )

        self.create_booking(
            patient=self.test_patients[9],
            room=rooms[9],  # Suite 302
            tariff=self.vip_tariff,
            start_offset=7,
            duration=12,
            status='confirmed',
            description='Future VIP booking'
        )

        # Scenario 5: Partial occupancy (2 guests in same room on different periods) - 2 bookings
        # Room 101 will have another guest after current one
        self.create_booking(
            patient=self.test_patients[10],
            room=rooms[0],  # Room 101 (capacity 2)
            tariff=self.standard_tariff,
            start_offset=5,  # Overlaps with existing if first guest stays
            duration=6,
            status='confirmed',
            description='Shared room scenario'
        )

        # Scenario 6: Back-to-back bookings - 2 bookings
        self.create_booking(
            patient=self.test_patients[11],
            room=rooms[2],  # Room 103
            tariff=self.standard_tariff,
            start_offset=6,  # Right after previous booking ends
            duration=8,
            status='confirmed',
            description='Back-to-back booking'
        )

        # Scenario 7: Week-long bookings starting next week - 3 bookings
        self.create_booking(
            patient=self.test_patients[12],
            room=rooms[1],  # Room 102
            tariff=self.standard_tariff,
            start_offset=8,
            duration=7,
            status='confirmed',
            description='Next week booking'
        )

        self.create_booking(
            patient=self.test_patients[13],
            room=rooms[5],  # Room 201
            tariff=self.premium_tariff,
            start_offset=10,
            duration=7,
            status='confirmed',
            description='Next week premium'
        )

        self.create_booking(
            patient=self.test_patients[14],
            room=rooms[6],  # Room 202
            tariff=self.premium_tariff,
            start_offset=9,
            duration=9,
            status='confirmed',
            description='Extended next week'
        )

        # Scenario 8: Reservations (pending) - 3 bookings
        self.create_booking(
            patient=self.test_patients[15],
            room=rooms[3],  # Room 104
            tariff=self.standard_tariff,
            start_offset=12,
            duration=5,
            status='pending',
            description='Pending reservation'
        )

        self.create_booking(
            patient=self.test_patients[16],
            room=rooms[7],  # Room 203
            tariff=self.premium_tariff,
            start_offset=14,
            duration=6,
            status='pending',
            description='Pending premium'
        )

        # Scenario 9: Long-term stay - 1 booking
        self.create_booking(
            patient=self.test_patients[17],
            room=rooms[4],  # Room 105
            tariff=self.standard_tariff,
            start_offset=15,
            duration=20,
            status='confirmed',
            description='Long-term care'
        )

        self.stdout.write(self.style.SUCCESS(f'  ✓ Created {self.booking_count} bookings'))

    def create_booking(self, patient, room, tariff, start_offset, duration, status, description):
        """Helper method to create a booking"""
        today = date.today()
        start_date = today + timedelta(days=start_offset)
        end_date = start_date + timedelta(days=duration)

        # Convert to datetime
        start_datetime = timezone.make_aware(
            timezone.datetime.combine(start_date, timezone.datetime.min.time())
        )
        end_datetime = timezone.make_aware(
            timezone.datetime.combine(end_date, timezone.datetime.min.time())
        )

        # Generate unique booking number
        booking_number = f"TEST-{timezone.now().strftime('%Y%m%d')}-{self.booking_count + 1:04d}"

        # Create booking
        booking = Booking.objects.create(
            booking_number=booking_number,
            staff=self.user,
            start_date=start_datetime,
            end_date=end_datetime,
            status=status,
            notes=f"Test booking: {description}"
        )

        # Create booking detail
        BookingDetail.objects.create(
            booking=booking,
            client=patient,
            room=room,
            tariff=tariff,
            price=tariff.price if hasattr(tariff, 'price') else 0,
            start_date=start_datetime,
            end_date=end_datetime,
            is_current=True,
            effective_from=start_datetime
        )

        self.booking_count += 1

    def create_maintenance_periods(self):
        """Create maintenance periods for some rooms"""
        self.stdout.write('Creating maintenance periods...')

        today = date.today()
        rooms = list(Room.objects.filter(is_active=True))

        self.maintenance_count = 0

        # Maintenance 1: Room under routine maintenance starting in 4 days
        self.create_maintenance(
            room=rooms[3],  # Room 104
            start_offset=18,
            duration=3,
            maintenance_type='routine',
            description='Test routine maintenance - deep cleaning and inspection'
        )

        # Maintenance 2: Room under repair starting next week
        self.create_maintenance(
            room=rooms[8],  # Suite 301
            start_offset=20,
            duration=5,
            maintenance_type='repair',
            description='Test repair - fixing air conditioning system'
        )

        self.stdout.write(self.style.SUCCESS(f'  ✓ Created {self.maintenance_count} maintenance periods'))

    def create_maintenance(self, room, start_offset, duration, maintenance_type, description):
        """Helper method to create maintenance period"""
        today = date.today()
        start_date = today + timedelta(days=start_offset)
        end_date = start_date + timedelta(days=duration)

        # Convert to datetime
        start_datetime = timezone.make_aware(
            timezone.datetime.combine(start_date, timezone.datetime.min.time())
        )
        end_datetime = timezone.make_aware(
            timezone.datetime.combine(end_date, timezone.datetime.min.time())
        )

        RoomMaintenance.objects.create(
            room=room,
            maintenance_type=maintenance_type,
            status='scheduled',
            start_date=start_datetime,
            end_date=end_datetime,
            description=description,
            assigned_to=self.user,
            created_by=self.user,
            modified_by=self.user
        )

        self.maintenance_count += 1
