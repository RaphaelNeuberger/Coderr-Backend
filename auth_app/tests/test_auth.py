"""Tests for registration, login and the guest user command."""

from io import StringIO

from django.contrib.auth.models import User
from django.core.management import call_command
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from profile_app.models import UserProfile


def registration_payload(**overrides):
    """Return a valid registration body, optionally changed."""
    payload = {
        "username": "max",
        "email": "max@mail.de",
        "password": "securePass123",
        "repeated_password": "securePass123",
        "type": "customer",
    }
    payload.update(overrides)
    return payload


class RegistrationTests(APITestCase):
    """Tests for POST /api/registration/."""

    url = reverse("registration")

    def test_registration_creates_user_and_profile(self):
        """A valid request creates the user, its profile and a token."""
        response = self.client.post(self.url, registration_payload())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            set(response.data), {"token", "username", "email", "user_id"}
        )
        profile = UserProfile.objects.get(user__username="max")
        self.assertEqual(profile.type, "customer")

    def test_registration_rejects_different_passwords(self):
        """Mismatching passwords lead to 400."""
        payload = registration_payload(repeated_password="other")
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_registration_rejects_duplicate_username(self):
        """An existing username leads to 400."""
        User.objects.create_user("max", "other@mail.de", "pw")
        response = self.client.post(self.url, registration_payload())
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_registration_rejects_duplicate_email(self):
        """An existing email address leads to 400."""
        User.objects.create_user("other", "max@mail.de", "pw")
        response = self.client.post(self.url, registration_payload())
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_registration_rejects_invalid_type(self):
        """An unknown profile type leads to 400."""
        response = self.client.post(self.url, registration_payload(type="x"))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class LoginTests(APITestCase):
    """Tests for POST /api/login/."""

    url = reverse("login")

    def setUp(self):
        """Create a user that can log in."""
        self.user = User.objects.create_user("max", "max@mail.de", "pw12345")

    def test_login_returns_token(self):
        """Correct credentials return the token and the user id."""
        data = {"username": "max", "password": "pw12345"}
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["user_id"], self.user.id)
        self.assertIn("token", response.data)

    def test_login_rejects_wrong_password(self):
        """Wrong credentials lead to 400."""
        data = {"username": "max", "password": "wrong"}
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_rejects_missing_fields(self):
        """An empty body leads to 400."""
        response = self.client.post(self.url, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class GuestUserCommandTests(APITestCase):
    """Tests for the create_guest_users management command."""

    def test_command_creates_guests_and_is_repeatable(self):
        """Running the command twice keeps exactly two guest profiles."""
        call_command("create_guest_users", stdout=StringIO())
        call_command("create_guest_users", stdout=StringIO())
        self.assertEqual(UserProfile.objects.count(), 2)
        response = self.client.post(
            reverse("login"), {"username": "kevin", "password": "asdasd24"}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
