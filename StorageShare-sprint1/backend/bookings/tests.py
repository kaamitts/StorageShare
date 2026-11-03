from datetime import datetime, time, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.db.models.deletion import ProtectedError
from django.test import TestCase
from django.utils import timezone

from bookings.models import Booking, BookingStatus
from storage.models import District, StoragePoint


class BookingModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        user_model = get_user_model()
        cls.traveler = user_model.objects.create_user(
            email="booking-traveler@example.com",
            full_name="Test Traveler",
            role="traveler",
        )
        partner = user_model.objects.create_user(
            email="booking-partner@example.com",
            full_name="Test Partner",
            role="partner",
        )
        cls.point = StoragePoint.objects.create(
            partner=partner,
            name="Test luggage room",
            address="Test address",
            district=District.MEDEU,
            price_per_bag_per_hour=Decimal("300.00"),
            capacity_bags=10,
            opens_at=time(8),
            closes_at=time(23),
        )

    def booking_data(self, **overrides):
        drop_off = timezone.now() + timedelta(days=1)
        data = {
            "traveler": self.traveler,
            "storage_point": self.point,
            "drop_off_at": drop_off,
            "pick_up_at": drop_off + timedelta(hours=2),
            "bags_count": 2,
            "total_price": Decimal("1200.00"),
        }
        data.update(overrides)
        return data

    def test_database_rejects_invalid_rows_without_saving_them(self):
        base = self.booking_data()
        invalid_values = [
            {"bags_count": 0},
            {"bags_count": -1},
            {"pick_up_at": base["drop_off_at"]},
            {"pick_up_at": base["drop_off_at"] - timedelta(minutes=1)},
            {"total_price": Decimal("-0.01")},
            {"status": "unknown"},
        ]
        for overrides in invalid_values:
            with self.subTest(overrides=overrides):
                data = {**base, **overrides}
                with self.assertRaises(IntegrityError), transaction.atomic():
                    Booking.objects.create(**data)
                self.assertEqual(Booking.objects.count(), 0)

    def test_full_timestamps_and_price_survive_database_round_trip(self):
        drop_off = timezone.make_aware(
            datetime(2030, 5, 10, 22),
        )
        pick_up = drop_off + timedelta(hours=11)
        booking = Booking.objects.create(**self.booking_data(
            drop_off_at=drop_off,
            pick_up_at=pick_up,
            total_price=Decimal("6600.00"),
        ))
        booking.refresh_from_db()
        self.assertEqual(booking.drop_off_at, drop_off)
        self.assertEqual(booking.pick_up_at, pick_up)
        self.assertEqual(booking.total_price, Decimal("6600.00"))
        self.assertEqual(booking.status, BookingStatus.AWAITING_PAYMENT)

    def test_booking_prevents_deleting_its_traveler_or_storage_point(self):
        Booking.objects.create(**self.booking_data())
        for related_object in (self.traveler, self.point):
            with self.subTest(model=type(related_object).__name__):
                with self.assertRaises(ProtectedError):
                    related_object.delete()
