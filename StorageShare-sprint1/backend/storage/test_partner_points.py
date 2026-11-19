"""Access and ownership tests for the partner's storage point list."""

from datetime import time, timedelta

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from bookings.models import Booking
from storage.models import District, StoragePoint

User = get_user_model()


class PartnerStoragePointListTests(APITestCase):
    url = reverse("partner:partner-storage-points")

    @classmethod
    def setUpTestData(cls):
        cls.partner = User.objects.create_user(
            email="partner-points@example.com", password="StorageShare2026",
            role=User.Role.PARTNER,
        )
        cls.other_partner = User.objects.create_user(
            email="other-partner-points@example.com", password="StorageShare2026",
            role=User.Role.PARTNER,
        )
        cls.traveler = User.objects.create_user(
            email="traveler-points@example.com", password="StorageShare2026",
        )
        cls.active = cls.create_point(cls.partner, "Active point", active=True)
        cls.inactive = cls.create_point(cls.partner, "Inactive point", active=False)
        cls.other = cls.create_point(cls.other_partner, "Other partner point", active=True)

    @staticmethod
    def create_point(partner, name, *, active):
        return StoragePoint.objects.create(
            partner=partner,
            name=name,
            address="Test address 1",
            district=District.MEDEU,
            price_per_bag_per_hour="250.00",
            capacity_bags=8,
            opens_at=time(20),
            closes_at=time(2),
            is_active=active,
        )

    def test_partner_receives_own_active_and_inactive_points(self):
        self.client.force_authenticate(self.partner)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            {row["name"] for row in response.data},
            {"Active point", "Inactive point"},
        )
        statuses = {row["name"]: row["is_active"] for row in response.data}
        self.assertTrue(statuses["Active point"])
        self.assertFalse(statuses["Inactive point"])

    def test_response_includes_schedule_and_24_hour_fields(self):
        self.client.force_authenticate(self.partner)

        point = self.client.get(self.url).data[0]

        self.assertEqual(point["opens_at"], "20:00")
        self.assertEqual(point["closes_at"], "02:00")
        self.assertFalse(point["is_24_hours"])
        self.assertIn("is_active", point)
        self.assertIn("district_code", point)

    def test_response_preserves_explicit_24_hour_mode(self):
        point = self.create_point(self.partner, "Always open", active=True)
        point.is_24_hours = True
        point.opens_at = time(0)
        point.closes_at = time(0)
        point.save(update_fields=["is_24_hours", "opens_at", "closes_at"])
        self.client.force_authenticate(self.partner)

        response = self.client.get(self.url)

        always_open = next(item for item in response.data if item["id"] == point.id)
        self.assertTrue(always_open["is_24_hours"])
        self.assertEqual(always_open["opens_at"], "00:00")
        self.assertEqual(always_open["closes_at"], "00:00")

    def test_points_of_other_partners_are_never_returned(self):
        self.client.force_authenticate(self.partner)

        names = {row["name"] for row in self.client.get(self.url).data}

        self.assertNotIn(self.other.name, names)

    def test_anonymous_user_is_denied(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_without_partner_role_is_denied(self):
        self.client.force_authenticate(self.traveler)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class PartnerStoragePointDeleteTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.partner = User.objects.create_user(
            email="delete-partner@example.com", password="StorageShare2026",
            role=User.Role.PARTNER,
        )
        cls.other_partner = User.objects.create_user(
            email="delete-other@example.com", password="StorageShare2026",
            role=User.Role.PARTNER,
        )
        cls.traveler = User.objects.create_user(
            email="delete-traveler@example.com", password="StorageShare2026",
        )
        cls.point = PartnerStoragePointListTests.create_point(
            cls.partner, "Deletable point", active=True,
        )
        cls.other_point = PartnerStoragePointListTests.create_point(
            cls.other_partner, "Another partner point", active=True,
        )

    def url(self, point_id):
        return reverse("partner:partner-storage-point-detail", args=[point_id])

    def test_partner_can_delete_own_point_without_bookings(self):
        self.client.force_authenticate(self.partner)

        response = self.client.delete(self.url(self.point.pk))

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(StoragePoint.objects.filter(pk=self.point.pk).exists())

    def test_partner_cannot_delete_another_partners_point(self):
        self.client.force_authenticate(self.partner)

        response = self.client.delete(self.url(self.other_point.pk))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(StoragePoint.objects.filter(pk=self.other_point.pk).exists())

    def test_anonymous_user_cannot_delete_a_point(self):
        response = self.client.delete(self.url(self.point.pk))

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_without_partner_role_cannot_delete_a_point(self):
        self.client.force_authenticate(self.traveler)

        response = self.client.delete(self.url(self.point.pk))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_point_with_booking_history_is_preserved(self):
        start = timezone.now() + timedelta(days=2)
        Booking.objects.create(
            traveler=self.traveler,
            storage_point=self.point,
            drop_off_at=start,
            pick_up_at=start + timedelta(hours=2),
            bags_count=1,
            total_price="500.00",
        )
        self.client.force_authenticate(self.partner)

        response = self.client.delete(self.url(self.point.pk))

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertTrue(StoragePoint.objects.filter(pk=self.point.pk).exists())
