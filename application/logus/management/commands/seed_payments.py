from decimal import Decimal
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from core.models import (
    Account,
    Booking,
    BookingDetail,
    Room,
    RoomType,
    Tariff,
    TariffRoomPrice,
    TransactionsModel,
    PatientModel,
    Service,
    ServiceTypeModel,
    ServiceUsage,
)


class Command(BaseCommand):
    help = "Seed sample bookings and transactions for the Logus payments dashboard"

    SAMPLE_PREFIX = "PAYTEST-"

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Remove existing seeded payment data before creating new records",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        reset = options.get("reset")

        if reset:
            self._reset_seed_data()

        staff = self._ensure_staff()
        room = self._ensure_room()
        tariff = self._ensure_tariff(room.room_type)
        service = self._ensure_service()

        patients = self._ensure_patients()

        bookings = self._create_bookings(staff, room, tariff, patients, service)
        totals = self._summarise(bookings)

        self.stdout.write(self.style.SUCCESS("Seeded payment data successfully."))
        self.stdout.write(
            "Created {bookings} bookings, {details} booking details and {payments} payments".format(**totals)
        )

    def _reset_seed_data(self):
        deleted, _ = Booking.objects.filter(booking_number__startswith=self.SAMPLE_PREFIX).delete()
        self.stdout.write(self.style.WARNING(f"Removed {deleted} existing seeded records."))

    def _ensure_staff(self):
        staff = Account.objects.filter(is_staff=True).first()
        if staff:
            return staff

        staff = Account.objects.create_user(
            email="cashier@example.com",
            username="cashier",
            password="cashier123",
        )
        staff.is_staff = True
        staff.f_name = "Кассир"
        staff.l_name = "Системный"
        staff.save(update_fields=["is_staff", "f_name", "l_name"])
        self.stdout.write("Created fallback cashier account (cashier@example.com / cashier123)")
        return staff

    def _ensure_room(self):
        room_type, _ = RoomType.objects.get_or_create(name="Single Deluxe", defaults={"description": "Тестовый тип"})
        room, _ = Room.objects.get_or_create(
            name="Deluxe-101",
            defaults={
                "room_type": room_type,
                "price": 250,
                "capacity": 2,
                "is_active": True,
            },
        )
        if room.room_type != room_type:
            room.room_type = room_type
            room.save(update_fields=["room_type"])
        return room

    def _ensure_tariff(self, room_type):
        tariff, _ = Tariff.objects.get_or_create(
            name="Wellness Package",
            defaults={
                "description": "Тестовый тариф для демонстрации платежей",
                "price": 500,
                "is_active": True,
            },
        )
        TariffRoomPrice.objects.get_or_create(
            tariff=tariff,
            room_type=room_type,
            defaults={"price": Decimal("450.00")},
        )
        return tariff

    def _ensure_service(self):
        service_type, _ = ServiceTypeModel.objects.get_or_create(type="SPA")
        service, _ = Service.objects.get_or_create(
            name="Арома массаж",
            defaults={
                "type": service_type,
                "price": 120,
                "is_active": True,
            },
        )
        if service.type != service_type:
            service.type = service_type
            service.save(update_fields=["type"])
        return service

    def _ensure_patients(self):
        sample_patients = [
            {"first": "Алексей", "last": "Иванов", "gender": True},
            {"first": "Мария", "last": "Петрова", "gender": False},
            {"first": "Саид", "last": "Каримов", "gender": True},
        ]
        patients = []
        for data in sample_patients:
            patient, _ = PatientModel.objects.get_or_create(
                f_name=data["first"],
                l_name=data["last"],
                defaults={
                    "gender": data["gender"],
                    "mobile_phone_number": "+99890" + str(5550000 + len(patients)),
                    "is_active": True,
                },
            )
            patients.append(patient)
        return patients

    def _create_bookings(self, staff, room, tariff, patients, service):
        now = timezone.now()
        bookings = []

        booking_specs = [
            {
                "suffix": "001",
                "nights": 5,
                "patients": [patients[0]],
                "payments": [Decimal("200.00"), Decimal("120.00")],
                "service_amount": Decimal("80.00"),
            },
            {
                "suffix": "002",
                "nights": 7,
                "patients": [patients[1], patients[2]],
                "payments": [Decimal("300.00")],
                "service_amount": Decimal("150.00"),
            },
            {
                "suffix": "003",
                "nights": 4,
                "patients": [patients[2]],
                "payments": [Decimal("450.00"), Decimal("120.00")],
                "service_amount": Decimal("0.00"),
            },
        ]

        for index, spec in enumerate(booking_specs):
            start = now - timedelta(days=10 - index * 3)
            end = start + timedelta(days=spec["nights"])

            booking, created = Booking.objects.get_or_create(
                booking_number=f"{self.SAMPLE_PREFIX}{spec['suffix']}",
                defaults={
                    "staff": staff,
                    "start_date": start,
                    "end_date": end,
                    "status": Booking.BookingStatus.CONFIRMED,
                },
            )

            if not created:
                # refresh dates/status in case booking persisted from previous runs
                booking.start_date = start
                booking.end_date = end
                booking.status = Booking.BookingStatus.CONFIRMED
                booking.save(update_fields=["start_date", "end_date", "status"])

            BookingDetail.objects.filter(booking=booking).delete()
            for patient in spec["patients"]:
                BookingDetail.objects.create(
                    booking=booking,
                    client=patient,
                    room=room,
                    tariff=tariff,
                    price=Decimal("450.00"),
                )

            ServiceUsage.objects.filter(booking=booking).delete()
            if spec["service_amount"] > 0:
                ServiceUsage.objects.create(
                    booking=booking,
                    booking_detail=booking.details.first(),
                    service=service,
                    quantity=1,
                    price=spec["service_amount"],
                    date_used=end - timedelta(days=1),
                )

            TransactionsModel.objects.filter(booking=booking).delete()
            for payment_amount in spec["payments"]:
                TransactionsModel.objects.create(
                    booking=booking,
                    patient=spec["patients"][0],
                    amount=payment_amount,
                    transaction_type=TransactionsModel.TransactionType.CASH,
                    created_by=staff,
                    modified_by=staff,
                )

            bookings.append(booking)

        return bookings

    def _summarise(self, bookings):
        return {
            "bookings": len(bookings),
            "details": sum(booking.details.count() for booking in bookings),
            "payments": sum(booking.transactions.count() for booking in bookings),
        }
