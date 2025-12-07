"""
Django management command to create comprehensive test data for billing demonstration

Usage:
    python manage.py create_billing_test_data
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from core.models import (
    Account, RolesModel, PatientModel, Room, RoomType,
    Tariff, TariffService, Service, Booking, BookingDetail,
    IllnessHistory, MedicationModel, PrescribedMedication,
    LabResearchModel, ServiceSessionTracking, CompanyModel,
    MedicationsInStockModel, Warehouse
)
from core.models.sanatorium.prescriptions.medications import MedicationSession
from core.models.sanatorium.prescriptions.assigned_labs import AssignedLabs


class Command(BaseCommand):
    help = 'Create comprehensive billing test data'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Creating billing test data...'))

        # Get or create role instances
        cashbox_role, _ = RolesModel.objects.get_or_create(
            name=RolesModel.CASHBOX,
            defaults={'is_active': True}
        )
        doctor_role, _ = RolesModel.objects.get_or_create(
            name=RolesModel.DOCTOR,
            defaults={'is_active': True}
        )

        # Create or get cashbox user
        cashbox_user, created = Account.objects.get_or_create(
            username='cashbox_demo',
            defaults={
                'email': 'cashbox_demo@hayat.com',
                'f_name': 'Demo',
                'l_name': 'Cashier',
            }
        )
        if created:
            cashbox_user.set_password('demo123')
            cashbox_user.save()
            cashbox_user.roles.add(cashbox_role)
            self.stdout.write(self.style.SUCCESS(f'✓ Created cashbox user: {cashbox_user.username}'))
        else:
            self.stdout.write(f'  Using existing cashbox user: {cashbox_user.username}')

        # Create doctor user
        doctor_user, created = Account.objects.get_or_create(
            username='doctor_demo',
            defaults={
                'email': 'doctor_demo@hayat.com',
                'f_name': 'Demo',
                'l_name': 'Doctor',
            }
        )
        if created:
            doctor_user.set_password('demo123')
            doctor_user.save()
            doctor_user.roles.add(doctor_role)
            self.stdout.write(self.style.SUCCESS(f'✓ Created doctor user: {doctor_user.username}'))
        else:
            self.stdout.write(f'  Using existing doctor user: {doctor_user.username}')

        # Create room type and room
        room_type, _ = RoomType.objects.get_or_create(
            name='Standard',
            defaults={
                'description': 'Standard Room'
            }
        )

        room, _ = Room.objects.get_or_create(
            name='101',
            defaults={
                'room_type': room_type,
                'is_active': True
            }
        )
        self.stdout.write(self.style.SUCCESS(f'✓ Created room: {room.name}'))

        # Create services
        services = {}
        service_data = [
            ('Массаж', 'Massage', 50000),
            ('Физиотерапия', 'Physiotherapy', 40000),
            ('Иглоукалывание', 'Acupuncture', 60000),
            ('ЛФК', 'Physical Therapy', 30000),
        ]

        for name_ru, name_en, price in service_data:
            service, _ = Service.objects.get_or_create(
                name=name_ru,
                defaults={
                    'price': price,
                    'description': name_en
                }
            )
            services[name_en.lower().replace(' ', '_')] = service

        self.stdout.write(self.style.SUCCESS(f'✓ Created {len(services)} services'))

        # Create tariff with included services
        tariff, _ = Tariff.objects.get_or_create(
            name='Базовый санаторный пакет',
            defaults={
                'description': 'Basic sanatorium package with included services',
                'price': 500000,
                'is_active': True,
                'created_by': cashbox_user,
                'modified_by': cashbox_user
            }
        )

        # Add services to tariff
        tariff_services_data = [
            (services['massage'], 5),  # 5 massage sessions included
            (services['physiotherapy'], 10),  # 10 physiotherapy sessions included
            (services['physical_therapy'], 7),  # 7 PT sessions included
        ]

        for service, sessions in tariff_services_data:
            TariffService.objects.get_or_create(
                tariff=tariff,
                service=service,
                defaults={
                    'sessions_included': sessions,
                    'created_by': cashbox_user,
                    'modified_by': cashbox_user
                }
            )

        self.stdout.write(self.style.SUCCESS(f'✓ Created tariff: {tariff.name} with included services'))

        # Create medication company
        company, _ = CompanyModel.objects.get_or_create(
            name='Demo Pharma Company',
            defaults={
                'created_by': doctor_user,
                'modified_by': doctor_user
            }
        )
        self.stdout.write(self.style.SUCCESS(f'✓ Created company: {company.name}'))

        # Create medications
        medications = {}
        medication_data = [
            ('Аспирин', 'Aspirin', 5000),
            ('Витамин C', 'Vitamin C', 3000),
            ('Ибупрофен', 'Ibuprofen', 7000),
            ('Амоксициллин', 'Amoxicillin', 12000),
        ]

        for name_ru, name_en, unit_price in medication_data:
            med, _ = MedicationModel.objects.get_or_create(
                name=name_ru,
                defaults={
                    'company': company,
                    'unit_price': unit_price,
                    'created_by': doctor_user,
                    'modified_by': doctor_user
                }
            )
            # Use lowercase with underscores for keys
            key = name_en.lower().replace(' ', '_')
            medications[key] = med

        self.stdout.write(self.style.SUCCESS(f'✓ Created {len(medications)} medications'))

        # Create warehouse
        warehouse, _ = Warehouse.objects.get_or_create(
            name='Main Warehouse',
            defaults={
                'created_by': doctor_user,
                'modified_by': doctor_user
            }
        )
        self.stdout.write(self.style.SUCCESS(f'✓ Created warehouse: {warehouse.name}'))

        # Create stock items for medications
        stock_items = {}
        for key, med in medications.items():
            stock, _ = MedicationsInStockModel.objects.get_or_create(
                item=med,
                warehouse=warehouse,
                income_seria=f'DEMO-{key.upper()}',
                defaults={
                    'quantity': 100,  # 100 packs
                    'unit_quantity': 0,
                    'price': med.unit_price * med.in_pack,  # Pack price
                    'unit_price': med.unit_price,
                    'expire_date': timezone.now().date() + timedelta(days=365),
                    'delivery_date': timezone.now().date(),
                    'created_by': doctor_user,
                    'modified_by': doctor_user
                }
            )
            stock_items[key] = stock

        self.stdout.write(self.style.SUCCESS(f'✓ Created {len(stock_items)} stock items'))

        # Create lab tests
        labs = {}
        lab_data = [
            ('Общий анализ крови', 'Complete Blood Count', 30000),
            ('Биохимический анализ крови', 'Blood Chemistry', 45000),
            ('Анализ мочи', 'Urinalysis', 20000),
            ('ЭКГ', 'ECG', 25000),
            ('Рентген грудной клетки', 'Chest X-Ray', 50000),
        ]

        for name_ru, name_en, price in lab_data:
            lab, _ = LabResearchModel.objects.get_or_create(
                name=name_ru,
                defaults={
                    'price': price,
                    'created_by': doctor_user,
                    'modified_by': doctor_user
                }
            )
            labs[name_en.lower().replace(' ', '_')] = lab

        self.stdout.write(self.style.SUCCESS(f'✓ Created {len(labs)} lab tests'))

        # Create patient
        patient, _ = PatientModel.objects.get_or_create(
            f_name='Иван',
            l_name='Иванов',
            mid_name='Иванович',
            defaults={
                'date_of_birth': timezone.now().date() - timedelta(days=15000),  # ~41 years old
                'gender': True,  # True for male, False for female
            }
        )
        self.stdout.write(self.style.SUCCESS(f'✓ Created patient: {patient.full_name}'))

        # Create booking
        start_date = timezone.now()
        end_date = start_date + timedelta(days=7)

        booking = Booking.objects.create(
            booking_number=Booking.generate_booking_number(),
            staff=doctor_user,
            start_date=start_date,
            end_date=end_date,
            status='discharged'  # Ready for billing
        )
        self.stdout.write(self.style.SUCCESS(f'✓ Created booking: {booking.booking_number}'))

        # Create booking detail
        booking_detail = BookingDetail.objects.create(
            booking=booking,
            client=patient,
            room=room,
            tariff=tariff,
            start_date=start_date.date(),
            end_date=end_date.date(),
            effective_from=start_date,
            is_current=True,
            price=tariff.price,
            created_by=doctor_user,
            modified_by=doctor_user
        )
        self.stdout.write(self.style.SUCCESS(f'✓ Created booking detail for patient'))

        # Create illness history
        illness_history = IllnessHistory.objects.create(
            booking=booking,
            patient=patient,
            created_by=doctor_user,
            modified_by=doctor_user
        )
        self.stdout.write(self.style.SUCCESS(f'✓ Created illness history'))

        # Create service session tracking
        # Scenario: Patient used MORE services than included
        service_usage_data = [
            (services['massage'], 5, 8),  # 5 included, 8 used = 3 extra (3 × 50,000 = 150,000)
            (services['physiotherapy'], 10, 12),  # 10 included, 12 used = 2 extra (2 × 40,000 = 80,000)
            (services['physical_therapy'], 7, 7),  # 7 included, 7 used = 0 extra
            (services['acupuncture'], 0, 3),  # 0 included, 3 used = 3 extra (3 × 60,000 = 180,000)
        ]

        total_service_extra = 0
        for service, included, used in service_usage_data:
            # Get or create tariff service for this service
            tariff_service, _ = TariffService.objects.get_or_create(
                tariff=tariff,
                service=service,
                defaults={
                    'sessions_included': included,
                    'created_by': doctor_user,
                    'modified_by': doctor_user
                }
            )

            # Create or update tracking
            tracking, _ = ServiceSessionTracking.objects.update_or_create(
                booking_detail=booking_detail,
                service=service,
                defaults={
                    'tariff_service': tariff_service,
                    'sessions_included': included,
                    'sessions_used': used,
                    'created_by': doctor_user,
                    'modified_by': doctor_user
                }
            )

            if used > included:
                extra = used - included
                extra_cost = extra * service.price
                total_service_extra += extra_cost
                self.stdout.write(
                    self.style.WARNING(
                        f'  → {service.name}: {included} included, {used} used, '
                        f'{extra} extra = {extra_cost:,} сум'
                    )
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'  → {service.name}: {included} included, {used} used (within limit)'
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'✓ Total extra service charges: {total_service_extra:,} сум'
            )
        )

        # Prescribe medications with various quantities
        medication_usage_data = [
            (stock_items['aspirin'], 20, '1 таб.', '2 раза в день'),  # 20 × 5,000 = 100,000
            (stock_items['vitamin_c'], 14, '1 капс.', '1 раз в день'),  # 14 × 3,000 = 42,000
            (stock_items['ibuprofen'], 10, '1 таб.', '3 раза в день'),  # 10 × 7,000 = 70,000
        ]

        total_medications = 0
        for stock_item, quantity, dosage, frequency in medication_usage_data:
            prescribed = PrescribedMedication.objects.create(
                illness_history=illness_history,
                medication=stock_item,
                dosage=dosage,
                frequency='bid',  # Twice daily
                start_date=booking.start_date.date(),
                end_date=booking.end_date.date(),
                duration_days=7,
                status='active',
                created_by=doctor_user,
                modified_by=doctor_user
            )

            med_session = MedicationSession.objects.create(
                prescribed_medication=prescribed,
                quantity=quantity,
                session_datetime=timezone.now(),
                status='administered',
                created_by=doctor_user,
                modified_by=doctor_user
            )

            cost = quantity * stock_item.item.unit_price
            total_medications += cost
            self.stdout.write(
                self.style.SUCCESS(
                    f'  → {stock_item.item.name}: {quantity} units × {stock_item.item.unit_price:,} = {cost:,} сум'
                )
            )

        self.stdout.write(
            self.style.SUCCESS(
                f'✓ Total medication charges: {total_medications:,} сум'
            )
        )

        # Assign lab tests with different states
        lab_usage_data = [
            (labs['complete_blood_count'], 'dispatched'),  # Billable: 30,000
            (labs['blood_chemistry'], 'results'),  # Billable: 45,000
            (labs['urinalysis'], 'dispatched'),  # Billable: 20,000
            (labs['ecg'], 'cancelled'),  # NOT billable
            (labs['chest_x-ray'], 'recommended'),  # NOT billable
        ]

        total_labs = 0
        for lab, state in lab_usage_data:
            assigned_lab = AssignedLabs.objects.create(
                illness_history=illness_history,
                lab=lab,
                state=state,
                created_by=doctor_user,
                modified_by=doctor_user
            )

            is_billable = state in ['dispatched', 'results']
            if is_billable:
                total_labs += lab.price
                self.stdout.write(
                    self.style.SUCCESS(
                        f'  → {lab.name}: {state} (BILLABLE) = {lab.price:,} сум'
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f'  → {lab.name}: {state} (NOT BILLABLE)'
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'✓ Total lab charges: {total_labs:,} сум'
            )
        )

        # Calculate expected totals
        tariff_base = tariff.price
        grand_total = tariff_base + total_service_extra + total_medications + total_labs

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('EXPECTED BILLING BREAKDOWN:'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(f'  Tariff Base:          {tariff_base:>15,} сум')
        self.stdout.write(f'  Extra Services:       {total_service_extra:>15,} сум')
        self.stdout.write(f'  Medications:          {total_medications:>15,} сум')
        self.stdout.write(f'  Lab Tests:            {total_labs:>15,} сум')
        self.stdout.write(self.style.SUCCESS('  ' + '-' * 58))
        self.stdout.write(self.style.SUCCESS(f'  TOTAL:                {grand_total:>15,} сум'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write('')
        self.stdout.write(
            self.style.SUCCESS(
                f'✅ Test data created successfully! Booking ID: {booking.id}'
            )
        )
        self.stdout.write(
            self.style.SUCCESS(
                f'   Visit: /application/cashbox/billing/{booking.id}/'
            )
        )
