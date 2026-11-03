from datetime import datetime, time, timedelta, timezone as datetime_timezone
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIClient, APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from bookings.models import Booking, BookingStatus
from bookings.serializers import BookingSerializer
from storage.models import District, StoragePoint


class BookingAPITests(APITestCase):
    url = reverse("bookings:booking-create")

    @classmethod
    def setUpTestData(cls):
        user_model = get_user_model()
        cls.traveler = user_model.objects.create_user(email="api-traveler@example.com")
        cls.other_traveler = user_model.objects.create_user(email="other@example.com")
        cls.partner = user_model.objects.create_user(
            email="api-partner@example.com", role="partner",
        )
        cls.point = StoragePoint.objects.create(
            partner=cls.partner, name="API test storage", address="Test address",
            district=District.MEDEU, price_per_bag_per_hour=Decimal("300.00"),
            capacity_bags=5, opens_at=time(8), closes_at=time(23),
        )
        tomorrow = timezone.localdate() + timedelta(days=2)
        cls.start = timezone.make_aware(datetime.combine(tomorrow, time(10)))
        cls.end = cls.start + timedelta(hours=2)

    def setUp(self):
        self.client.force_authenticate(self.traveler)

    def payload(self, **overrides):
        data = {
            "storage_point": self.point.pk,
            "drop_off_at": self.start.isoformat(),
            "pick_up_at": self.end.isoformat(),
            "bags_count": 2,
        }
        data.update(overrides)
        return data

    def existing(self, **overrides):
        data = {
            "traveler": self.other_traveler, "storage_point": self.point,
            "drop_off_at": self.start, "pick_up_at": self.end,
            "bags_count": 3, "total_price": Decimal("1800.00"),
            "status": BookingStatus.AWAITING_PAYMENT,
        }
        data.update(overrides)
        return Booking.objects.create(**data)

    def assert_rejected(self, payload, field, expected_status=400):
        before = Booking.objects.count()
        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, expected_status, response.data)
        self.assertIn(field, response.data)
        self.assertEqual(Booking.objects.count(), before)
        return response

    def test_valid_booking_returns_calculated_price_and_awaiting_payment(self):
        response = self.client.post(self.url, self.payload(), format="json")
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data["total_price"], "1200.00")
        self.assertEqual(response.data["status"], "awaiting_payment")
        self.assertEqual(response.data["traveler"], self.traveler.pk)
        self.assertEqual(Booking.objects.get().total_price, Decimal("1200.00"))

    def test_partial_hour_is_billed_by_actual_duration(self):
        response = self.client.post(self.url, self.payload(
            pick_up_at=(self.start + timedelta(minutes=90)).isoformat(),
        ), format="json")
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data["total_price"], "900.00")

    def test_only_final_price_is_rounded_half_up(self):
        self.point.price_per_bag_per_hour = Decimal("0.01")
        self.point.save(update_fields=["price_per_bag_per_hour"])
        response = self.client.post(self.url, self.payload(
            bags_count=1,
            pick_up_at=(self.start + timedelta(minutes=30)).isoformat(),
        ), format="json")
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data["total_price"], "0.01")

    def test_free_storage_returns_zero_price(self):
        self.point.price_per_bag_per_hour = Decimal("0.00")
        self.point.save(update_fields=["price_per_bag_per_hour"])
        response = self.client.post(self.url, self.payload(), format="json")
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data["total_price"], "0.00")

    def test_read_only_fields_cannot_be_spoofed(self):
        response = self.client.post(self.url, self.payload(
            traveler=self.other_traveler.pk, total_price="0.00", status="confirmed",
        ), format="json")
        self.assertEqual(response.status_code, 201, response.data)
        booking = Booking.objects.get()
        self.assertEqual(booking.traveler, self.traveler)
        self.assertEqual(booking.status, BookingStatus.AWAITING_PAYMENT)
        self.assertEqual(booking.total_price, Decimal("1200.00"))

    def test_real_bearer_token_identifies_the_traveler(self):
        client = APIClient()
        access = str(RefreshToken.for_user(self.traveler).access_token)
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        response = client.post(self.url, self.payload(), format="json")
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(Booking.objects.get().traveler, self.traveler)

    def test_anonymous_request_is_rejected(self):
        self.client.force_authenticate(None)
        self.assert_rejected(self.payload(), "detail", 401)

    def test_partner_cannot_create_booking(self):
        self.client.force_authenticate(self.partner)
        self.assert_rejected(self.payload(), "detail", 403)

    def test_invalid_bag_counts_create_no_booking(self):
        for value in [0, -1, 1.5, True, "many", None, 32768]:
            with self.subTest(value=value):
                self.assert_rejected(self.payload(bags_count=value), "bags_count")

    def test_missing_required_fields_create_no_booking(self):
        for field in ["storage_point", "drop_off_at", "pick_up_at", "bags_count"]:
            with self.subTest(field=field):
                payload = self.payload()
                del payload[field]
                self.assert_rejected(payload, field)

    def test_invalid_datetime_inputs_create_no_booking(self):
        for field in ["drop_off_at", "pick_up_at"]:
            for value in ["not-a-date", None, "2030-02-30T10:00:00+05:00"]:
                with self.subTest(field=field, value=value):
                    self.assert_rejected(self.payload(**{field: value}), field)

    def test_drop_off_in_past_is_rejected(self):
        past = timezone.now() - timedelta(minutes=1)
        self.assert_rejected(self.payload(drop_off_at=past.isoformat()), "drop_off_at")

    def test_pick_up_must_be_strictly_after_drop_off(self):
        for end in [self.start, self.start - timedelta(minutes=1)]:
            with self.subTest(end=end):
                self.assert_rejected(self.payload(pick_up_at=end.isoformat()), "pick_up_at")

    def test_inactive_or_missing_point_is_rejected(self):
        self.assert_rejected(self.payload(storage_point=999999), "storage_point")
        self.point.is_active = False
        self.point.save(update_fields=["is_active"])
        self.assert_rejected(self.payload(), "storage_point")

    def test_cannot_book_more_than_total_capacity(self):
        self.assert_rejected(self.payload(bags_count=6), "bags_count")

    def test_overlapping_booking_reduces_capacity(self):
        self.existing()
        response = self.assert_rejected(self.payload(
            bags_count=3,
            drop_off_at=(self.start + timedelta(hours=1)).isoformat(),
            pick_up_at=(self.end + timedelta(hours=1)).isoformat(),
        ), "bags_count")
        self.assertIn("2 bag(s)", str(response.data["bags_count"]))

    def test_exact_remaining_capacity_can_be_booked(self):
        self.existing(bags_count=3)
        response = self.client.post(self.url, self.payload(bags_count=2), format="json")
        self.assertEqual(response.status_code, 201, response.data)

    def test_all_capacity_reserving_statuses_are_counted(self):
        for value in ["awaiting_payment", "confirmed", "checked_in"]:
            with self.subTest(status=value):
                previous = self.existing(status=value, bags_count=5)
                self.assert_rejected(self.payload(bags_count=1), "bags_count")
                previous.delete()

    def test_cancelled_and_completed_bookings_do_not_reserve_capacity(self):
        self.existing(status=BookingStatus.CANCELLED, bags_count=5)
        self.existing(status=BookingStatus.COMPLETED, bags_count=5)
        response = self.client.post(self.url, self.payload(bags_count=5), format="json")
        self.assertEqual(response.status_code, 201, response.data)

    def test_adjacent_bookings_do_not_overlap(self):
        self.existing(
            drop_off_at=self.start - timedelta(hours=2),
            pick_up_at=self.start, bags_count=5,
        )
        self.existing(
            drop_off_at=self.end, pick_up_at=self.end + timedelta(hours=2),
            bags_count=5,
        )
        response = self.client.post(self.url, self.payload(bags_count=5), format="json")
        self.assertEqual(response.status_code, 201, response.data)

    def test_sequential_bookings_are_not_added_as_simultaneous(self):
        middle = self.start + timedelta(hours=1)
        self.existing(pick_up_at=middle, bags_count=3)
        self.existing(drop_off_at=middle, bags_count=3)
        response = self.client.post(self.url, self.payload(bags_count=2), format="json")
        self.assertEqual(response.status_code, 201, response.data)

    def test_peak_occupancy_inside_requested_interval_is_checked(self):
        self.existing(bags_count=3)
        self.existing(
            drop_off_at=self.start + timedelta(hours=1),
            pick_up_at=self.end + timedelta(hours=1), bags_count=2,
        )
        self.assert_rejected(self.payload(
            bags_count=1, pick_up_at=(self.end + timedelta(hours=1)).isoformat(),
        ), "bags_count")

    def test_bookings_at_other_points_do_not_reduce_capacity(self):
        other = StoragePoint.objects.create(
            partner=self.partner, name="Other point", address="Other address",
            district=District.ALMALY, price_per_bag_per_hour=Decimal("200.00"),
            capacity_bags=5, opens_at=time(8), closes_at=time(23),
        )
        self.existing(storage_point=other, bags_count=5)
        response = self.client.post(self.url, self.payload(bags_count=5), format="json")
        self.assertEqual(response.status_code, 201, response.data)

    def test_overnight_storage_is_allowed_when_handover_times_are_open(self):
        drop_off = self.start.replace(hour=22)
        pick_up = (self.start + timedelta(days=1)).replace(hour=9)
        response = self.client.post(self.url, self.payload(
            drop_off_at=drop_off.isoformat(), pick_up_at=pick_up.isoformat(),
        ), format="json")
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data["total_price"], "6600.00")

    def test_handover_outside_opening_hours_is_rejected(self):
        self.assert_rejected(self.payload(
            drop_off_at=self.start.replace(hour=7).isoformat(),
        ), "drop_off_at")
        self.assert_rejected(self.payload(
            pick_up_at=self.start.replace(hour=23, minute=1).isoformat(),
        ), "pick_up_at")

    def test_pick_up_at_closing_is_allowed_but_drop_off_at_closing_is_not(self):
        response = self.client.post(self.url, self.payload(
            pick_up_at=self.start.replace(hour=23).isoformat(),
        ), format="json")
        self.assertEqual(response.status_code, 201, response.data)
        self.assert_rejected(self.payload(
            drop_off_at=self.start.replace(hour=23).isoformat(),
            pick_up_at=(self.start + timedelta(days=1)).isoformat(),
        ), "drop_off_at")

    def test_point_with_night_opening_hours(self):
        self.point.opens_at = time(20)
        self.point.closes_at = time(6)
        self.point.save(update_fields=["opens_at", "closes_at"])
        response = self.client.post(self.url, self.payload(
            drop_off_at=self.start.replace(hour=22).isoformat(),
            pick_up_at=(self.start + timedelta(days=1)).replace(hour=6).isoformat(),
        ), format="json")
        self.assertEqual(response.status_code, 201, response.data)
        self.assert_rejected(self.payload(), "drop_off_at")

    def test_equal_opening_and_closing_times_mean_open_all_day(self):
        self.point.opens_at = time(0)
        self.point.closes_at = time(0)
        self.point.save(update_fields=["opens_at", "closes_at"])
        response = self.client.post(self.url, self.payload(
            drop_off_at=self.start.replace(hour=2).isoformat(),
            pick_up_at=self.start.replace(hour=3).isoformat(),
        ), format="json")
        self.assertEqual(response.status_code, 201, response.data)

    def test_utc_input_is_checked_against_almaty_opening_hours(self):
        response = self.client.post(self.url, self.payload(
            drop_off_at=self.start.astimezone(datetime_timezone.utc).isoformat(),
            pick_up_at=self.end.astimezone(datetime_timezone.utc).isoformat(),
        ), format="json")
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data["total_price"], "1200.00")

    def test_price_overflow_is_a_validation_error_not_a_database_error(self):
        self.point.capacity_bags = 32767
        self.point.price_per_bag_per_hour = Decimal("999999.99")
        self.point.save(update_fields=["capacity_bags", "price_per_bag_per_hour"])
        self.assert_rejected(self.payload(
            bags_count=32767,
            pick_up_at=(self.start + timedelta(days=365)).isoformat(),
        ), "pick_up_at")

    def test_current_point_values_are_reloaded_after_input_validation(self):
        serializer = BookingSerializer(data=self.payload(bags_count=2))
        serializer.is_valid(raise_exception=True)
        StoragePoint.objects.filter(pk=self.point.pk).update(
            price_per_bag_per_hour=Decimal("400.00"), capacity_bags=1,
        )
        with self.assertRaises(ValidationError):
            serializer.save(traveler=self.traveler)
        self.assertEqual(Booking.objects.count(), 0)
        StoragePoint.objects.filter(pk=self.point.pk).update(capacity_bags=2)
        booking = serializer.save(traveler=self.traveler)
        self.assertEqual(booking.total_price, Decimal("1600.00"))

    def test_point_deactivated_after_validation_cannot_be_booked(self):
        serializer = BookingSerializer(data=self.payload())
        serializer.is_valid(raise_exception=True)
        StoragePoint.objects.filter(pk=self.point.pk).update(is_active=False)
        with self.assertRaises(ValidationError):
            serializer.save(traveler=self.traveler)
        self.assertEqual(Booking.objects.count(), 0)

    def test_start_time_is_rechecked_when_saving(self):
        serializer = BookingSerializer(data=self.payload())
        serializer.is_valid(raise_exception=True)
        with patch("bookings.services.timezone.now", return_value=self.start):
            with self.assertRaises(ValidationError):
                serializer.save(traveler=self.traveler)
        self.assertEqual(Booking.objects.count(), 0)
