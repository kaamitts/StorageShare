"""US-05: mock payment confirms the owner's booking."""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, time, timedelta
from decimal import Decimal
from threading import Barrier
from unittest import skipUnless

from django.contrib.auth import get_user_model
from django.db import connection, connections
from django.test import TransactionTestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient, APITestCase

from bookings.models import Booking, BookingStatus
from storage.models import District, StoragePoint


def make_point(partner):
    return StoragePoint.objects.create(
        partner=partner, name="Payment test storage", address="Test address",
        district=District.MEDEU, price_per_bag_per_hour=Decimal("300.00"),
        capacity_bags=5, opens_at=time(8), closes_at=time(23),
    )


def make_booking(traveler, point, **overrides):
    tomorrow = timezone.localdate() + timedelta(days=2)
    start = timezone.make_aware(datetime.combine(tomorrow, time(10)))
    data = {
        "traveler": traveler, "storage_point": point,
        "drop_off_at": start, "pick_up_at": start + timedelta(hours=2),
        "bags_count": 2, "total_price": Decimal("1200.00"),
        "status": BookingStatus.AWAITING_PAYMENT,
    }
    data.update(overrides)
    return Booking.objects.create(**data)


def pay_url(booking_id):
    return reverse("bookings:booking-pay", args=[booking_id])


class BookingPaymentAPITests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        user_model = get_user_model()
        cls.owner = user_model.objects.create_user(email="pay-owner@example.com")
        cls.other = user_model.objects.create_user(email="pay-other@example.com")
        cls.partner = user_model.objects.create_user(
            email="pay-partner@example.com", role="partner",
        )
        cls.point = make_point(cls.partner)

    def setUp(self):
        self.booking = make_booking(self.owner, self.point)
        self.client.force_authenticate(self.owner)

    def pay(self, booking_id=None):
        return self.client.post(pay_url(booking_id or self.booking.pk), format="json")

    def test_owner_confirms_pending_booking(self):
        response = self.pay()
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["id"], self.booking.pk)
        self.assertEqual(response.data["status"], "confirmed")
        self.assertEqual(response.data["total_price"], "1200.00")
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, BookingStatus.CONFIRMED)

    def test_total_price_is_not_recalculated(self):
        # A stored total that differs from the current tariff must stay as it is.
        Booking.objects.filter(pk=self.booking.pk).update(total_price=Decimal("999.99"))
        self.point.price_per_bag_per_hour = Decimal("1000.00")
        self.point.save()
        response = self.pay()
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["total_price"], "999.99")
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.total_price, Decimal("999.99"))

    def test_other_user_cannot_confirm(self):
        self.client.force_authenticate(self.other)
        response = self.pay()
        self.assertEqual(response.status_code, 404)
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, BookingStatus.AWAITING_PAYMENT)

    def test_partner_of_the_point_cannot_confirm(self):
        self.client.force_authenticate(self.partner)
        response = self.pay()
        self.assertEqual(response.status_code, 404)
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, BookingStatus.AWAITING_PAYMENT)

    def test_anonymous_user_cannot_confirm(self):
        self.client.force_authenticate(None)
        response = self.pay()
        self.assertEqual(response.status_code, 401)
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, BookingStatus.AWAITING_PAYMENT)

    def test_missing_booking_returns_404(self):
        response = self.pay(booking_id=self.booking.pk + 1000)
        self.assertEqual(response.status_code, 404)

    def test_get_is_not_allowed(self):
        response = self.client.get(pay_url(self.booking.pk))
        self.assertEqual(response.status_code, 405)

    def test_repeated_requests_do_not_duplicate_or_repeat_transition(self):
        first = self.pay()
        self.assertEqual(first.status_code, 200, first.data)
        self.booking.refresh_from_db()
        updated_at = self.booking.updated_at

        for _ in range(3):
            response = self.pay()
            self.assertEqual(response.status_code, 200, response.data)
            self.assertEqual(response.data["status"], "confirmed")
            self.assertEqual(response.data["id"], self.booking.pk)

        self.assertEqual(Booking.objects.count(), 1)
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, BookingStatus.CONFIRMED)
        # No second save happened.
        self.assertEqual(self.booking.updated_at, updated_at)

    def test_repeated_request_does_not_reset_later_statuses(self):
        for later in (BookingStatus.CHECKED_IN, BookingStatus.COMPLETED):
            with self.subTest(status=later):
                Booking.objects.filter(pk=self.booking.pk).update(status=later)
                response = self.pay()
                self.assertEqual(response.status_code, 200, response.data)
                self.assertEqual(response.data["status"], later)
                self.booking.refresh_from_db()
                self.assertEqual(self.booking.status, later)

    def test_cancelled_booking_cannot_be_paid(self):
        Booking.objects.filter(pk=self.booking.pk).update(
            status=BookingStatus.CANCELLED,
        )
        response = self.pay()
        self.assertEqual(response.status_code, 409)
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, BookingStatus.CANCELLED)

    def test_confirming_one_booking_leaves_others_unchanged(self):
        second = make_booking(self.owner, self.point)
        response = self.pay()
        self.assertEqual(response.status_code, 200, response.data)
        second.refresh_from_db()
        self.assertEqual(second.status, BookingStatus.AWAITING_PAYMENT)


@skipUnless(connection.vendor == "postgresql", "Requires PostgreSQL row locks")
class BookingPaymentConcurrencyTests(TransactionTestCase):
    def setUp(self):
        user_model = get_user_model()
        self.owner = user_model.objects.create_user(email="race-pay@example.com")
        partner = user_model.objects.create_user(
            email="race-pay-partner@example.com", role="partner",
        )
        self.booking = make_booking(self.owner, make_point(partner))

    def test_simultaneous_payments_confirm_once(self):
        workers = 5
        barrier = Barrier(workers)

        def pay(_):
            try:
                client = APIClient()
                client.force_authenticate(self.owner)
                barrier.wait(timeout=10)
                return client.post(pay_url(self.booking.pk), format="json").status_code
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=workers) as pool:
            codes = list(pool.map(pay, range(workers)))

        self.assertEqual(codes, [200] * workers)
        self.assertEqual(Booking.objects.count(), 1)
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, BookingStatus.CONFIRMED)
        self.assertEqual(self.booking.total_price, Decimal("1200.00"))
