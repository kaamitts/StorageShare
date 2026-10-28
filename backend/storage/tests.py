"""Tests for US-02 — district filter and result cards.

The acceptance criteria of US-02 come first: a district with points returns
only those points, and a district without points returns an empty list.
"""

from datetime import time

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from storage.models import District, StoragePoint

User = get_user_model()
PASSWORD = "StorageShare2026"


class StoragePointListTests(APITestCase):
    url = reverse("storage:storage-point-list")

    @classmethod
    def setUpTestData(cls):
        cls.partner = User.objects.create_user(
            email="hostel@example.com", password=PASSWORD, role=User.Role.PARTNER
        )
        cls.traveler = User.objects.create_user(
            email="aizhan@example.com", password=PASSWORD
        )

        def point(name, district, price="300.00", active=True):
            return StoragePoint.objects.create(
                partner=cls.partner,
                name=name,
                address="Some street 1",
                district=district,
                price_per_bag_per_hour=price,
                capacity_bags=10,
                opens_at=time(8, 0),
                closes_at=time(23, 0),
                is_active=active,
            )

        point("Medeu Hostel", District.MEDEU)
        point("Medeu Cafe", District.MEDEU, price="250.00")
        point("Medeu Closed", District.MEDEU, active=False)
        point("Almaly Hostel", District.ALMALY)

    def authenticate(self, user=None):
        self.client.force_authenticate(user or self.traveler)

    # --- acceptance criteria of US-02 ------------------------------------
    def test_district_with_points_returns_only_that_district(self):
        self.authenticate()
        response = self.client.get(self.url, {"district": "medeu"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        names = [row["name"] for row in response.data]
        self.assertEqual(names, ["Medeu Cafe", "Medeu Hostel"])  # ordered by name
        self.assertTrue(all(row["district"] == "Medeu" for row in response.data))

    def test_district_without_points_returns_an_empty_list(self):
        self.authenticate()
        response = self.client.get(self.url, {"district": "turksib"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    # --- the card itself --------------------------------------------------
    def test_card_carries_name_district_and_price(self):
        self.authenticate()
        card = self.client.get(self.url, {"district": "almaly"}).data[0]
        self.assertEqual(
            set(card),
            {"id", "name", "district", "district_code", "price_per_bag_per_hour"},
        )
        self.assertEqual(card["name"], "Almaly Hostel")
        self.assertEqual(card["district"], "Almaly")
        self.assertEqual(card["district_code"], "almaly")
        self.assertEqual(card["price_per_bag_per_hour"], "300.00")

    def test_card_does_not_leak_the_partner_or_the_address(self):
        self.authenticate()
        card = self.client.get(self.url, {"district": "almaly"}).data[0]
        self.assertNotIn("partner", card)
        self.assertNotIn("address", card)

    # --- filtering rules --------------------------------------------------
    def test_inactive_points_are_hidden(self):
        self.authenticate()
        names = [row["name"] for row in self.client.get(self.url, {"district": "medeu"}).data]
        self.assertNotIn("Medeu Closed", names)

    def test_without_the_parameter_all_active_points_are_returned(self):
        self.authenticate()
        response = self.client.get(self.url)
        self.assertEqual(len(response.data), 3)

    def test_district_value_is_case_insensitive(self):
        self.authenticate()
        response = self.client.get(self.url, {"district": "  MEDEU "})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_unknown_district_is_rejected(self):
        self.authenticate()
        response = self.client.get(self.url, {"district": "narnia"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("district", response.data)

    # --- access -----------------------------------------------------------
    def test_anonymous_user_cannot_list_points(self):
        response = self.client.get(self.url, {"district": "medeu"})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_a_partner_sees_the_same_list(self):
        self.authenticate(self.partner)
        response = self.client.get(self.url, {"district": "medeu"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)


class StoragePointDetailTests(APITestCase):
    """US-03 — the storage point page."""

    @classmethod
    def setUpTestData(cls):
        cls.partner = User.objects.create_user(
            email="hostel@example.com", password=PASSWORD, role=User.Role.PARTNER
        )
        cls.traveler = User.objects.create_user(email="aizhan@example.com", password=PASSWORD)
        cls.point = StoragePoint.objects.create(
            partner=cls.partner,
            name="Almaty Hostel — reception",
            address="Dostyk ave 85",
            district=District.MEDEU,
            price_per_bag_per_hour="300.00",
            capacity_bags=10,
            opens_at=time(8, 0),
            closes_at=time(23, 0),
            security_notes="Locked room behind the reception desk, camera.",
        )
        cls.hidden = StoragePoint.objects.create(
            partner=cls.partner,
            name="Hidden point",
            address="Somewhere 1",
            district=District.MEDEU,
            price_per_bag_per_hour="300.00",
            capacity_bags=5,
            opens_at=time(9, 0),
            closes_at=time(20, 0),
            is_active=False,
        )

    def url(self, pk):
        return reverse("storage:storage-point-detail", args=[pk])

    def test_returns_every_field_the_page_needs(self):
        self.client.force_authenticate(self.traveler)
        response = self.client.get(self.url(self.point.pk))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            set(response.data),
            {
                "id", "name", "district", "district_code", "address",
                "opens_at", "closes_at", "security_notes", "price_per_bag_per_hour",
            },
        )
        self.assertEqual(response.data["name"], "Almaty Hostel — reception")
        self.assertEqual(response.data["district"], "Medeu")
        self.assertEqual(response.data["address"], "Dostyk ave 85")
        self.assertEqual(response.data["opens_at"], "08:00")
        self.assertEqual(response.data["closes_at"], "23:00")
        self.assertEqual(response.data["price_per_bag_per_hour"], "300.00")
        self.assertIn("camera", response.data["security_notes"])

    def test_does_not_leak_the_partner(self):
        self.client.force_authenticate(self.traveler)
        response = self.client.get(self.url(self.point.pk))
        self.assertNotIn("partner", response.data)

    def test_unknown_id_returns_404(self):
        self.client.force_authenticate(self.traveler)
        response = self.client.get(self.url(999999))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_hidden_point_returns_404(self):
        self.client.force_authenticate(self.traveler)
        response = self.client.get(self.url(self.hidden.pk))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_anonymous_user_cannot_open_the_page(self):
        response = self.client.get(self.url(self.point.pk))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_the_id_from_the_list_opens_the_page(self):
        """The card and the page agree: the id in the list is the id in the URL."""
        self.client.force_authenticate(self.traveler)
        card = self.client.get(
            reverse("storage:storage-point-list"), {"district": "medeu"}
        ).data[0]
        response = self.client.get(self.url(card["id"]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], card["name"])


class DistrictListTests(APITestCase):
    url = reverse("storage:district-list")

    def setUp(self):
        self.user = User.objects.create_user(email="aizhan@example.com", password=PASSWORD)

    def test_returns_the_fixed_district_list(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), len(District.choices))
        self.assertIn({"code": "medeu", "name": "Medeu"}, response.data)
