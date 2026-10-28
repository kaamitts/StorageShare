"""Tests for US-01 — register and log in as traveler or partner (IPM-8).

The three scenarios QA wrote for this story are covered first:
valid login, wrong password, email already taken.
"""

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import AccessToken

User = get_user_model()

PASSWORD = "StorageShare2026"


class RegisterTests(APITestCase):
    url = reverse("accounts:register")

    def test_traveler_can_register_and_gets_tokens(self):
        response = self.client.post(
            self.url,
            {"email": "aizhan@example.com", "password": PASSWORD, "full_name": "Aizhan T."},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["user"]["role"], User.Role.TRAVELER)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertNotIn("password", response.data["user"])

    def test_partner_can_register_with_the_partner_role(self):
        response = self.client.post(
            self.url,
            {"email": "hostel@example.com", "password": PASSWORD, "role": "partner"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["user"]["role"], User.Role.PARTNER)
        self.assertTrue(User.objects.get(email="hostel@example.com").is_partner)

    def test_email_already_taken_is_rejected(self):
        """QA scenario: email already taken."""
        User.objects.create_user(email="aizhan@example.com", password=PASSWORD)
        response = self.client.post(
            self.url, {"email": "aizhan@example.com", "password": PASSWORD}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            str(response.data["email"][0]), "A user with this email already exists."
        )
        self.assertEqual(User.objects.count(), 1)

    def test_email_already_taken_in_another_case_is_rejected(self):
        User.objects.create_user(email="aizhan@example.com", password=PASSWORD)
        response = self.client.post(
            self.url, {"email": "AIZHAN@Example.com", "password": PASSWORD}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(User.objects.count(), 1)

    def test_weak_password_is_rejected(self):
        response = self.client.post(
            self.url, {"email": "marco@example.com", "password": "12345678"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)
        self.assertFalse(User.objects.filter(email="marco@example.com").exists())

    def test_unknown_role_is_rejected(self):
        response = self.client.post(
            self.url,
            {"email": "root@example.com", "password": PASSWORD, "role": "admin"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("role", response.data)

    def test_password_is_stored_hashed(self):
        self.client.post(
            self.url, {"email": "aizhan@example.com", "password": PASSWORD}, format="json"
        )
        user = User.objects.get(email="aizhan@example.com")
        self.assertNotEqual(user.password, PASSWORD)
        self.assertTrue(user.check_password(PASSWORD))


class LoginTests(APITestCase):
    url = reverse("accounts:login")

    def setUp(self):
        self.user = User.objects.create_user(
            email="aizhan@example.com", password=PASSWORD, full_name="Aizhan T."
        )
        self.partner = User.objects.create_user(
            email="hostel@example.com", password=PASSWORD, role=User.Role.PARTNER
        )

    def test_valid_login_returns_tokens_and_user(self):
        """QA scenario: valid login."""
        response = self.client.post(
            self.url, {"email": "aizhan@example.com", "password": PASSWORD}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertEqual(response.data["user"]["email"], "aizhan@example.com")
        self.assertEqual(response.data["user"]["role"], User.Role.TRAVELER)

    def test_login_is_case_insensitive_on_the_email(self):
        response = self.client.post(
            self.url, {"email": "AIZHAN@example.com", "password": PASSWORD}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_wrong_password_is_rejected(self):
        """QA scenario: wrong password."""
        response = self.client.post(
            self.url, {"email": "aizhan@example.com", "password": "WrongPassword1"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(str(response.data["detail"]), "Invalid email or password.")
        self.assertNotIn("access", response.data)

    def test_unknown_email_gets_the_same_message(self):
        response = self.client.post(
            self.url, {"email": "nobody@example.com", "password": PASSWORD}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(str(response.data["detail"]), "Invalid email or password.")

    def test_disabled_account_cannot_log_in(self):
        self.user.is_active = False
        self.user.save(update_fields=["is_active"])
        response = self.client.post(
            self.url, {"email": "aizhan@example.com", "password": PASSWORD}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_access_token_carries_the_role_for_the_frontend(self):
        response = self.client.post(
            self.url, {"email": "hostel@example.com", "password": PASSWORD}, format="json"
        )
        token = AccessToken(response.data["access"])
        self.assertEqual(token["role"], User.Role.PARTNER)
        # simplejwt 5.5 puts the id in the token as a string
        self.assertEqual(str(token["user_id"]), str(self.partner.id))


class MeAndLogoutTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="aizhan@example.com", password=PASSWORD)
        response = self.client.post(
            reverse("accounts:login"),
            {"email": "aizhan@example.com", "password": PASSWORD},
            format="json",
        )
        self.access = response.data["access"]
        self.refresh = response.data["refresh"]

    def test_me_requires_a_token(self):
        self.assertEqual(
            self.client.get(reverse("accounts:me")).status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_me_returns_the_logged_in_user(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access}")
        response = self.client.get(reverse("accounts:me"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], "aizhan@example.com")

    def test_refresh_returns_a_new_access_token(self):
        response = self.client.post(
            reverse("accounts:refresh"), {"refresh": self.refresh}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)

    def test_logout_blacklists_the_refresh_token(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access}")
        response = self.client.post(
            reverse("accounts:logout"), {"refresh": self.refresh}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_205_RESET_CONTENT)

        reused = self.client.post(
            reverse("accounts:refresh"), {"refresh": self.refresh}, format="json"
        )
        self.assertEqual(reused.status_code, status.HTTP_401_UNAUTHORIZED)
