from datetime import datetime, time, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from bookings.models import Booking, BookingStatus
from bookings.services import expire_pending_bookings
from storage.models import District, StoragePoint


class BookingExpiryTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        user_model = get_user_model()
        cls.traveler = user_model.objects.create_user(email="expiry-traveler@example.com")
        partner = user_model.objects.create_user(
            email="expiry-partner@example.com", role="partner",
        )
        cls.point = StoragePoint.objects.create(
            partner=partner, name="Expiry test storage", address="Test address",
            district=District.MEDEU, price_per_bag_per_hour=Decimal("300.00"),
            capacity_bags=5, opens_at=time(8), closes_at=time(23),
        )

    def make_booking(self, *, status=BookingStatus.AWAITING_PAYMENT, expires_at=None):
        created_at = timezone.now() - timedelta(minutes=20)
        start = timezone.make_aware(datetime.combine(
            timezone.localdate() + timedelta(days=2), time(10),
        ))
        return Booking.objects.create(
            traveler=self.traveler,
            storage_point=self.point,
            drop_off_at=start,
            pick_up_at=start + timedelta(hours=2),
            bags_count=1,
            total_price=Decimal("600.00"),
            status=status,
            created_at=created_at,
            payment_expires_at=expires_at or created_at + timedelta(minutes=15),
        )

    def test_expiry_service_marks_only_due_awaiting_bookings(self):
        due = self.make_booking()
        future = self.make_booking(expires_at=timezone.now() + timedelta(minutes=1))
        confirmed = self.make_booking(status=BookingStatus.CONFIRMED)

        changed = expire_pending_bookings()

        self.assertEqual(changed, 1)
        due.refresh_from_db()
        future.refresh_from_db()
        confirmed.refresh_from_db()
        self.assertEqual(due.status, BookingStatus.EXPIRED)
        self.assertEqual(future.status, BookingStatus.AWAITING_PAYMENT)
        self.assertEqual(confirmed.status, BookingStatus.CONFIRMED)

    def test_management_command_expires_bookings_without_api_request(self):
        booking = self.make_booking()

        call_command("expire_pending_bookings", stdout=None)

        booking.refresh_from_db()
        self.assertEqual(booking.status, BookingStatus.EXPIRED)

    def test_expiry_service_is_idempotent(self):
        booking = self.make_booking()

        self.assertEqual(expire_pending_bookings(), 1)
        self.assertEqual(expire_pending_bookings(), 0)
        booking.refresh_from_db()
        self.assertEqual(booking.status, BookingStatus.EXPIRED)
