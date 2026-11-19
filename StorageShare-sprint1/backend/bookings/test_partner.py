"""US-08: the partner's bookings list. US-09: check-in and check-out by QR token."""

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


def make_point(partner, name="Point"):
    return StoragePoint.objects.create(
        partner=partner, name=name, address="Test address",
        district=District.MEDEU, price_per_bag_per_hour=Decimal("300.00"),
        capacity_bags=50, opens_at=time(8), closes_at=time(23),
    )


def make_booking(traveler, point, status=BookingStatus.CONFIRMED, days=2, hour=10):
    day = timezone.localdate() + timedelta(days=days)
    start = timezone.make_aware(datetime.combine(day, time(hour)))
    return Booking.objects.create(
        traveler=traveler, storage_point=point,
        drop_off_at=start, pick_up_at=start + timedelta(hours=2),
        bags_count=2, total_price=Decimal("1200.00"), status=status,
    )


class PartnerTestData:
    @classmethod
    def setUpTestData(cls):
        user_model = get_user_model()
        cls.partner = user_model.objects.create_user(
            email="owner-partner@example.com", role="partner",
        )
        cls.other_partner = user_model.objects.create_user(
            email="other-partner@example.com", role="partner",
        )
        cls.traveler = user_model.objects.create_user(
            email="partner-traveler@example.com", full_name="Aigerim S.",
        )
        cls.point = make_point(cls.partner, "My hostel")
        cls.second_point = make_point(cls.partner, "My cafe")
        cls.other_point = make_point(cls.other_partner, "Not mine")


class PartnerBookingListTests(PartnerTestData, APITestCase):
    url = reverse("partner:partner-bookings")

    def setUp(self):
        self.client.force_authenticate(self.partner)

    def get_ids(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200, response.data)
        return [item["id"] for item in response.data]

    def test_partner_sees_paid_bookings_of_own_points_with_details(self):
        booking = make_booking(self.traveler, self.point)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        item = response.data[0]
        self.assertEqual(item["id"], booking.pk)
        self.assertEqual(item["storage_point_id"], self.point.pk)
        self.assertEqual(item["storage_point_name"], "My hostel")
        self.assertEqual(item["bags_count"], 2)
        self.assertEqual(item["status"], "confirmed")
        self.assertIn("drop_off_at", item)
        self.assertIn("pick_up_at", item)

    def test_bookings_from_all_own_points_are_listed(self):
        a = make_booking(self.traveler, self.point)
        b = make_booking(self.traveler, self.second_point)
        self.assertCountEqual(self.get_ids(), [a.pk, b.pk])

    def test_other_partners_bookings_never_appear(self):
        mine = make_booking(self.traveler, self.point)
        make_booking(self.traveler, self.other_point)
        self.assertEqual(self.get_ids(), [mine.pk])

    def test_other_partner_does_not_see_mine(self):
        make_booking(self.traveler, self.point)
        self.client.force_authenticate(self.other_partner)
        self.assertEqual(self.get_ids(), [])

    def test_unpaid_bookings_are_not_returned(self):
        make_booking(self.traveler, self.point, status=BookingStatus.AWAITING_PAYMENT)
        make_booking(self.traveler, self.point, status=BookingStatus.EXPIRED)
        paid = [
            make_booking(self.traveler, self.point, status=status).pk
            for status in (
                BookingStatus.CONFIRMED, BookingStatus.CHECKED_IN, BookingStatus.COMPLETED,
            )
        ]
        self.assertCountEqual(self.get_ids(), paid)

    def test_partner_without_bookings_gets_empty_list(self):
        self.assertEqual(self.get_ids(), [])

    def test_ordered_by_drop_off_time(self):
        late = make_booking(self.traveler, self.point, days=5)
        early = make_booking(self.traveler, self.point, days=2, hour=9)
        middle = make_booking(self.traveler, self.second_point, days=2, hour=15)
        self.assertEqual(self.get_ids(), [early.pk, middle.pk, late.pk])

    def test_no_extra_queries_per_booking(self):
        for _ in range(5):
            make_booking(self.traveler, self.point)
        # Session/auth is forced, so: one query for the list with the joined point.
        with self.assertNumQueries(1):
            response = self.client.get(self.url)
        self.assertEqual(len(response.data), 5)

    def test_traveler_gets_403(self):
        self.client.force_authenticate(self.traveler)
        self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_anonymous_gets_401(self):
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get(self.url).status_code, 401)

    def test_list_is_read_only(self):
        self.assertEqual(self.client.post(self.url, {}, format="json").status_code, 405)


class CheckInCheckOutTests(PartnerTestData, APITestCase):
    def setUp(self):
        self.client.force_authenticate(self.partner)
        self.booking = make_booking(self.traveler, self.point)

    def url(self, action="", token=None):
        token = token or self.booking.qr_token
        name = {
            "": "bookings:booking-by-token",
            "check-in": "bookings:booking-check-in",
            "check-out": "bookings:booking-check-out",
        }[action]
        return reverse(name, args=[token])

    def check_in(self, **kw):
        return self.client.post(self.url("check-in", **kw))

    def check_out(self, **kw):
        return self.client.post(self.url("check-out", **kw))

    def set_status(self, status):
        Booking.objects.filter(pk=self.booking.pk).update(status=status)

    def assert_status(self, status):
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, status)

    # The check-in page

    def test_owner_opens_check_in_page(self):
        response = self.client.get(self.url())
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["id"], self.booking.pk)
        self.assertEqual(response.data["storage_point"]["name"], "My hostel")
        self.assertEqual(response.data["traveler_name"], "Aigerim S.")
        self.assertEqual(response.data["bags_count"], 2)
        self.assertEqual(response.data["status"], "confirmed")
        self.assertTrue(response.data["can_check_in"])
        self.assertFalse(response.data["can_check_out"])

    def test_page_works_with_the_link_from_history(self):
        self.client.force_authenticate(self.traveler)
        history = self.client.get(reverse("bookings:booking-history")).data
        token = history[0]["qr"]["token"]
        self.assertTrue(history[0]["qr"]["url"].endswith("/partner/check-in/" + token))
        self.client.force_authenticate(self.partner)
        self.assertEqual(self.client.get(self.url(token=token)).status_code, 200)

    # Happy path

    def test_full_flow_check_in_then_check_out(self):
        before = timezone.now()
        response = self.check_in()
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["status"], "checked_in")
        self.assertTrue(response.data["can_check_out"])
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, BookingStatus.CHECKED_IN)
        self.assertGreaterEqual(self.booking.checked_in_at, before)
        self.assertIsNone(self.booking.checked_out_at)
        checked_in_at = self.booking.checked_in_at

        response = self.check_out()
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["status"], "completed")
        self.assertFalse(response.data["can_check_in"])
        self.assertFalse(response.data["can_check_out"])
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, BookingStatus.COMPLETED)
        self.assertEqual(self.booking.checked_in_at, checked_in_at)
        self.assertGreaterEqual(self.booking.checked_out_at, checked_in_at)
        self.assertEqual(self.booking.total_price, Decimal("1200.00"))

    def test_qr_disappears_from_history_after_check_out(self):
        self.check_in()
        self.client.force_authenticate(self.traveler)
        history = self.client.get(reverse("bookings:booking-history")).data
        self.assertIsNotNone(history[0]["qr"])

        self.client.force_authenticate(self.partner)
        self.assertEqual(self.check_out().status_code, 200)

        self.client.force_authenticate(self.traveler)
        history = self.client.get(reverse("bookings:booking-history")).data
        self.assertEqual(history[0]["status"], "completed")
        self.assertIsNone(history[0]["qr"])

    def test_page_still_opens_after_completion_but_offers_no_action(self):
        self.check_in()
        self.check_out()
        response = self.client.get(self.url())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], "completed")
        self.assertFalse(response.data["can_check_in"])
        self.assertFalse(response.data["can_check_out"])

    # Owner check

    def test_other_partner_gets_403_everywhere(self):
        self.client.force_authenticate(self.other_partner)
        for response in (self.client.get(self.url()), self.check_in(), self.check_out()):
            self.assertEqual(response.status_code, 403)
            self.assertIn("another partner", str(response.data["detail"]))
        self.assert_status(BookingStatus.CONFIRMED)

    def test_other_partner_cannot_check_out(self):
        self.set_status(BookingStatus.CHECKED_IN)
        self.client.force_authenticate(self.other_partner)
        self.assertEqual(self.check_out().status_code, 403)
        self.assert_status(BookingStatus.CHECKED_IN)

    def test_traveler_gets_403_even_for_own_booking(self):
        self.client.force_authenticate(self.traveler)
        for response in (self.client.get(self.url()), self.check_in(), self.check_out()):
            self.assertEqual(response.status_code, 403)
        self.assert_status(BookingStatus.CONFIRMED)

    def test_anonymous_gets_401(self):
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get(self.url()).status_code, 401)
        self.assertEqual(self.check_in().status_code, 401)
        self.assert_status(BookingStatus.CONFIRMED)

    def test_unknown_token_returns_404(self):
        for response in (
            self.client.get(self.url(token="does-not-exist")),
            self.check_in(token="does-not-exist"),
            self.check_out(token="does-not-exist"),
        ):
            self.assertEqual(response.status_code, 404)
            self.assertEqual(str(response.data["detail"]), "No booking found for this QR code.")

    def test_booking_id_is_not_accepted_as_token(self):
        self.assertEqual(self.check_in(token=str(self.booking.pk)).status_code, 404)
        self.assert_status(BookingStatus.CONFIRMED)

    def test_get_does_not_change_status(self):
        self.client.get(self.url())
        self.assertEqual(self.client.get(self.url("check-in")).status_code, 405)
        self.assert_status(BookingStatus.CONFIRMED)

    # Status rules

    def assert_conflict(self, response, message):
        self.assertEqual(response.status_code, 409, response.data)
        self.assertEqual(str(response.data["detail"]), message)

    def test_check_out_before_check_in_is_rejected(self):
        self.assert_conflict(self.check_out(), "The bags must be checked in before check-out.")
        self.assert_status(BookingStatus.CONFIRMED)
        self.booking.refresh_from_db()
        self.assertIsNone(self.booking.checked_out_at)

    def test_unpaid_booking_cannot_be_checked_in_or_out(self):
        self.set_status(BookingStatus.AWAITING_PAYMENT)
        self.assert_conflict(self.check_in(), "This booking has not been paid yet.")
        self.assert_conflict(self.check_out(), "This booking has not been paid yet.")
        self.assert_status(BookingStatus.AWAITING_PAYMENT)

    def test_second_check_in_is_rejected_and_keeps_first_time(self):
        self.assertEqual(self.check_in().status_code, 200)
        self.booking.refresh_from_db()
        first_time = self.booking.checked_in_at
        self.assert_conflict(self.check_in(), "The bags are already checked in.")
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.checked_in_at, first_time)

    def test_second_check_out_is_rejected_and_keeps_first_time(self):
        self.check_in()
        self.assertEqual(self.check_out().status_code, 200)
        self.booking.refresh_from_db()
        first_time = self.booking.checked_out_at
        self.assert_conflict(self.check_out(), "The bags are already checked out.")
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.checked_out_at, first_time)

    def test_completed_booking_cannot_be_checked_in_again(self):
        self.set_status(BookingStatus.COMPLETED)
        self.assert_conflict(self.check_in(), "This booking is already completed.")
        self.assert_status(BookingStatus.COMPLETED)

    def test_cancelled_booking_is_rejected(self):
        self.set_status(BookingStatus.CANCELLED)
        self.assert_conflict(self.check_in(), "This booking was cancelled.")
        self.assert_conflict(self.check_out(), "This booking was cancelled.")
        self.assert_status(BookingStatus.CANCELLED)

    def test_partner_list_shows_check_in_time(self):
        self.check_in()
        item = self.client.get(reverse("partner:partner-bookings")).data[0]
        self.assertEqual(item["status"], "checked_in")
        self.assertIsNotNone(item["checked_in_at"])


@skipUnless(connection.vendor == "postgresql", "Requires PostgreSQL row locks")
class CheckInConcurrencyTests(TransactionTestCase):
    def setUp(self):
        user_model = get_user_model()
        self.partner = user_model.objects.create_user(
            email="race-checkin@example.com", role="partner",
        )
        traveler = user_model.objects.create_user(email="race-checkin-t@example.com")
        self.booking = make_booking(traveler, make_point(self.partner))

    def run_parallel(self, url_name, workers=5):
        barrier = Barrier(workers)

        def post(_):
            try:
                client = APIClient()
                client.force_authenticate(self.partner)
                barrier.wait(timeout=10)
                url = reverse(url_name, args=[self.booking.qr_token])
                return client.post(url).status_code
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=workers) as pool:
            return sorted(pool.map(post, range(workers)))

    def test_simultaneous_scans_check_in_once(self):
        codes = self.run_parallel("bookings:booking-check-in")
        self.assertEqual(codes, [200, 409, 409, 409, 409])
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, BookingStatus.CHECKED_IN)

    def test_simultaneous_scans_check_out_once(self):
        Booking.objects.filter(pk=self.booking.pk).update(
            status=BookingStatus.CHECKED_IN, checked_in_at=timezone.now(),
        )
        codes = self.run_parallel("bookings:booking-check-out")
        self.assertEqual(codes, [200, 409, 409, 409, 409])
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, BookingStatus.COMPLETED)
