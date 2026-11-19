"""US-07: a partner adds a storage point."""

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase

from storage.models import StoragePoint


class StoragePointCreateTests(APITestCase):
    url = reverse("storage:storage-point-list")

    @classmethod
    def setUpTestData(cls):
        user_model = get_user_model()
        cls.partner = user_model.objects.create_user(
            email="create-partner@example.com", role="partner",
        )
        cls.other_partner = user_model.objects.create_user(
            email="create-other@example.com", role="partner",
        )
        cls.traveler = user_model.objects.create_user(email="create-traveler@example.com")

    def setUp(self):
        self.client.force_authenticate(self.partner)

    def payload(self, **overrides):
        data = {
            "name": "Hostel Almaty — reception",
            "address": "Abay ave 10",
            "district": "medeu",
            "price_per_bag_per_hour": "300.00",
            "capacity_bags": 10,
            "opens_at": "08:00",
            "closes_at": "22:00",
            "security_notes": "CCTV, locked room",
        }
        data.update(overrides)
        return data

    def assert_rejected(self, payload, field, expected_status=400):
        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, expected_status, response.data)
        self.assertIn(field, response.data)
        self.assertEqual(StoragePoint.objects.count(), 0)
        return response

    # Success

    def test_partner_creates_point_and_it_appears_in_district_list(self):
        response = self.client.post(self.url, self.payload(), format="json")
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data["partner"], self.partner.pk)
        self.assertEqual(response.data["district"], "medeu")
        self.assertEqual(response.data["price_per_bag_per_hour"], "300.00")
        self.assertEqual(response.data["capacity_bags"], 10)
        self.assertEqual(response.data["opens_at"], "08:00")
        self.assertEqual(response.data["closes_at"], "22:00")
        self.assertFalse(response.data["is_24_hours"])
        self.assertTrue(response.data["is_active"])

        # A traveler searching that district sees it.
        self.client.force_authenticate(self.traveler)
        listed = self.client.get(self.url, {"district": "medeu"})
        self.assertEqual(listed.status_code, 200)
        self.assertEqual([p["id"] for p in listed.data], [response.data["id"]])
        # ...and not in another district.
        other = self.client.get(self.url, {"district": "almaly"})
        self.assertEqual(other.data, [])

    def test_new_point_is_bookable_detail_page(self):
        response = self.client.post(self.url, self.payload(), format="json")
        self.client.force_authenticate(self.traveler)
        detail = self.client.get(
            reverse("storage:storage-point-detail", args=[response.data["id"]]),
        )
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(detail.data["security_notes"], "CCTV, locked room")

    def test_security_notes_are_optional(self):
        payload = self.payload()
        del payload["security_notes"]
        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(StoragePoint.objects.get().security_notes, "")

    def test_partner_comes_from_login_not_from_body(self):
        response = self.client.post(
            self.url, self.payload(partner=self.other_partner.pk), format="json",
        )
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(StoragePoint.objects.get().partner, self.partner)

    def test_body_cannot_create_hidden_point(self):
        response = self.client.post(self.url, self.payload(is_active=False), format="json")
        self.assertEqual(response.status_code, 201, response.data)
        self.assertTrue(StoragePoint.objects.get().is_active)

    def test_zero_price_is_allowed(self):
        response = self.client.post(
            self.url, self.payload(price_per_bag_per_hour="0"), format="json",
        )
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(StoragePoint.objects.get().price_per_bag_per_hour, Decimal("0"))

    # Permissions

    def test_traveler_gets_403(self):
        self.client.force_authenticate(self.traveler)
        self.assert_rejected(self.payload(), "detail", expected_status=403)

    def test_anonymous_gets_401(self):
        self.client.force_authenticate(None)
        self.assert_rejected(self.payload(), "detail", expected_status=401)

    # Validation

    def test_empty_price_is_rejected(self):
        for value in ("", None):
            with self.subTest(value=value):
                self.assert_rejected(
                    self.payload(price_per_bag_per_hour=value), "price_per_bag_per_hour",
                )

    def test_missing_price_is_rejected(self):
        payload = self.payload()
        del payload["price_per_bag_per_hour"]
        self.assert_rejected(payload, "price_per_bag_per_hour")

    def test_negative_price_is_rejected(self):
        self.assert_rejected(
            self.payload(price_per_bag_per_hour="-1.00"), "price_per_bag_per_hour",
        )

    def test_non_numeric_price_is_rejected(self):
        self.assert_rejected(
            self.payload(price_per_bag_per_hour="cheap"), "price_per_bag_per_hour",
        )

    def test_capacity_zero_is_rejected(self):
        self.assert_rejected(self.payload(capacity_bags=0), "capacity_bags")

    def test_capacity_negative_or_empty_is_rejected(self):
        for value in (-3, "", None):
            with self.subTest(value=value):
                self.assert_rejected(self.payload(capacity_bags=value), "capacity_bags")

    def test_unknown_district_is_rejected(self):
        self.assert_rejected(self.payload(district="downtown"), "district")

    def test_partner_can_create_overnight_schedule(self):
        response = self.client.post(
            self.url,
            self.payload(opens_at="20:00", closes_at="02:00"),
            format="json",
        )
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data["opens_at"], "20:00")
        self.assertEqual(response.data["closes_at"], "02:00")
        self.assertFalse(response.data["is_24_hours"])

    def test_equal_hours_require_explicit_24_hour_mode(self):
        self.assert_rejected(
            self.payload(opens_at="10:00", closes_at="10:00"), "closes_at",
        )

    def test_partner_can_create_24_hour_point_without_time_fields(self):
        payload = self.payload(is_24_hours=True)
        payload.pop("opens_at")
        payload.pop("closes_at")
        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, 201, response.data)
        point = StoragePoint.objects.get()
        self.assertTrue(point.is_24_hours)
        self.assertEqual(point.opens_at, point.closes_at)
        self.assertEqual(response.data["opens_at"], "00:00")
        self.assertEqual(response.data["closes_at"], "00:00")

    def test_invalid_time_is_rejected(self):
        self.assert_rejected(self.payload(opens_at="25:00"), "opens_at")

    def test_blank_name_and_address_are_rejected(self):
        response = self.assert_rejected(self.payload(name="  ", address=""), "name")
        self.assertIn("address", response.data)
