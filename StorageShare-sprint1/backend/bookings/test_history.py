"""US-06: booking history and QR codes."""

from datetime import datetime, time, timedelta
from decimal import Decimal
from urllib.parse import unquote

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase

from bookings.models import Booking, BookingStatus
from storage.models import District, StoragePoint

QR_TEMPLATE = "https://storageshare.test/partner/check-in/{token}"


def make_booking(traveler, point, status=BookingStatus.CONFIRMED, days=2):
    day = timezone.localdate() + timedelta(days=days)
    start = timezone.make_aware(datetime.combine(day, time(10)))
    return Booking.objects.create(
        traveler=traveler, storage_point=point,
        drop_off_at=start, pick_up_at=start + timedelta(hours=2),
        bags_count=2, total_price=Decimal("1200.00"), status=status,
    )


@override_settings(BOOKING_QR_URL_TEMPLATE=QR_TEMPLATE)
class BookingHistoryAPITests(APITestCase):
    url = reverse("bookings:booking-history")

    @classmethod
    def setUpTestData(cls):
        user_model = get_user_model()
        cls.traveler = user_model.objects.create_user(email="history@example.com")
        cls.other = user_model.objects.create_user(email="history-other@example.com")
        cls.partner = user_model.objects.create_user(
            email="history-partner@example.com", role="partner",
        )
        cls.point = StoragePoint.objects.create(
            partner=cls.partner, name="History storage", address="Abay 1",
            district=District.MEDEU, price_per_bag_per_hour=Decimal("300.00"),
            capacity_bags=50, opens_at=time(8), closes_at=time(23),
        )

    def setUp(self):
        self.client.force_authenticate(self.traveler)

    def get_history(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200, response.data)
        return {item["id"]: item for item in response.data}

    # Ownership

    def test_returns_only_current_travelers_bookings(self):
        mine = make_booking(self.traveler, self.point)
        make_booking(self.other, self.point)
        self.assertEqual(set(self.get_history()), {mine.pk})

    def test_other_traveler_does_not_see_my_bookings_or_tokens(self):
        mine = make_booking(self.traveler, self.point)
        self.client.force_authenticate(self.other)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, [])
        self.assertNotIn(mine.qr_token, str(response.content))

    def test_anonymous_user_is_rejected(self):
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get(self.url).status_code, 401)

    def test_partner_is_rejected(self):
        self.client.force_authenticate(self.partner)
        self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_history_is_read_only(self):
        self.assertEqual(self.client.post(self.url, {}, format="json").status_code, 405)

    # Status rules

    def test_awaiting_payment_bookings_are_excluded(self):
        make_booking(self.traveler, self.point, status=BookingStatus.AWAITING_PAYMENT)
        paid = make_booking(self.traveler, self.point)
        self.assertEqual(set(self.get_history()), {paid.pk})

    def test_paid_and_finished_statuses_are_listed(self):
        expected = {
            make_booking(self.traveler, self.point, status=status).pk: status
            for status in (
                BookingStatus.CONFIRMED, BookingStatus.CHECKED_IN,
                BookingStatus.COMPLETED, BookingStatus.CANCELLED,
            )
        }
        history = self.get_history()
        self.assertEqual(
            {pk: item["status"] for pk, item in history.items()}, expected,
        )

    def test_confirmed_and_checked_in_return_a_qr(self):
        for status in (BookingStatus.CONFIRMED, BookingStatus.CHECKED_IN):
            with self.subTest(status=status):
                booking = make_booking(self.traveler, self.point, status=status)
                qr = self.get_history()[booking.pk]["qr"]
                self.assertEqual(qr["token"], booking.qr_token)
                self.assertEqual(qr["url"], QR_TEMPLATE.format(token=booking.qr_token))
                self.assertTrue(qr["image"].startswith("data:image/svg+xml"))

    def test_completed_and_cancelled_return_no_qr(self):
        for status in (BookingStatus.COMPLETED, BookingStatus.CANCELLED):
            with self.subTest(status=status):
                booking = make_booking(self.traveler, self.point, status=status)
                item = self.get_history()[booking.pk]
                self.assertIsNone(item["qr"])
                self.assertNotIn(booking.qr_token, str(item))

    def test_qr_disappears_when_booking_is_completed(self):
        booking = make_booking(self.traveler, self.point, status=BookingStatus.CHECKED_IN)
        self.assertIsNotNone(self.get_history()[booking.pk]["qr"])
        Booking.objects.filter(pk=booking.pk).update(status=BookingStatus.COMPLETED)
        self.assertIsNone(self.get_history()[booking.pk]["qr"])

    # Token rules

    def test_different_bookings_have_different_tokens(self):
        bookings = [make_booking(self.traveler, self.point) for _ in range(5)]
        history = self.get_history()
        tokens = {history[b.pk]["qr"]["token"] for b in bookings}
        self.assertEqual(len(tokens), 5)
        urls = {history[b.pk]["qr"]["url"] for b in bookings}
        self.assertEqual(len(urls), 5)

    def test_token_stays_the_same_for_the_same_booking(self):
        booking = make_booking(self.traveler, self.point)
        first = self.get_history()[booking.pk]["qr"]
        Booking.objects.filter(pk=booking.pk).update(status=BookingStatus.CHECKED_IN)
        second = self.get_history()[booking.pk]["qr"]
        self.assertEqual(first["token"], second["token"])
        self.assertEqual(first["url"], second["url"])
        self.assertEqual(first["image"], second["image"])

    def test_qr_link_does_not_use_booking_id(self):
        booking = make_booking(self.traveler, self.point)
        qr = self.get_history()[booking.pk]["qr"]
        self.assertGreaterEqual(len(qr["token"]), 40)
        self.assertNotEqual(qr["token"], str(booking.pk))
        self.assertTrue(qr["url"].endswith("/" + qr["token"]))

    def test_different_bookings_get_different_qr_images(self):
        a = make_booking(self.traveler, self.point)
        b = make_booking(self.traveler, self.point)
        history = self.get_history()
        self.assertNotEqual(history[a.pk]["qr"]["image"], history[b.pk]["qr"]["image"])
        self.assertIn("<svg", unquote(history[a.pk]["qr"]["image"]))

    def test_booking_appears_with_qr_after_mock_payment(self):
        booking = make_booking(self.traveler, self.point, status=BookingStatus.AWAITING_PAYMENT)
        self.assertNotIn(booking.pk, self.get_history())
        pay = self.client.post(reverse("bookings:booking-pay", args=[booking.pk]))
        self.assertEqual(pay.status_code, 200, pay.data)
        item = self.get_history()[booking.pk]
        self.assertEqual(item["status"], "confirmed")
        self.assertEqual(item["qr"]["token"], booking.qr_token)

    def test_storage_point_details_are_included(self):
        booking = make_booking(self.traveler, self.point)
        point = self.get_history()[booking.pk]["storage_point"]
        self.assertEqual(point, {
            "id": self.point.pk, "name": "History storage",
            "address": "Abay 1", "district": "Medeu",
        })

    def test_newest_drop_off_first(self):
        older = make_booking(self.traveler, self.point, days=2)
        newer = make_booking(self.traveler, self.point, days=5)
        response = self.client.get(self.url)
        self.assertEqual([i["id"] for i in response.data], [newer.pk, older.pk])


class BookingQrTokenModelTests(TestCase):
    def test_token_is_set_on_create_and_not_changed_by_saves(self):
        user_model = get_user_model()
        traveler = user_model.objects.create_user(email="token@example.com")
        partner = user_model.objects.create_user(email="token-p@example.com", role="partner")
        point = StoragePoint.objects.create(
            partner=partner, name="Token storage", address="Test",
            district=District.MEDEU, price_per_bag_per_hour=Decimal("300.00"),
            capacity_bags=5, opens_at=time(8), closes_at=time(23),
        )
        booking = make_booking(traveler, point, status=BookingStatus.AWAITING_PAYMENT)
        token = booking.qr_token
        self.assertTrue(token)
        booking.status = BookingStatus.CONFIRMED
        booking.save()
        booking.refresh_from_db()
        self.assertEqual(booking.qr_token, token)
