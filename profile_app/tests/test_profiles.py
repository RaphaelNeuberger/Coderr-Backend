"""Tests for the profile endpoints."""

import shutil
import tempfile

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from profile_app.api.serializers import ProfileDetailSerializer
from profile_app.models import UserProfile

TEMP_MEDIA = tempfile.mkdtemp()
GIF_BYTES = (b"GIF89a\x01\x00\x01\x00\x00\x00\x00!\xf9\x04\x01\x00\x00\x00"
             b"\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;")


def create_profile(username, profile_type):
    """Create a user with a profile of the given type."""
    user = User.objects.create_user(username, f"{username}@mail.de", "pw")
    UserProfile.objects.create(user=user, type=profile_type)
    return user


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class ProfileDetailTests(APITestCase):
    """Tests for GET and PATCH /api/profile/{pk}/."""

    @classmethod
    def tearDownClass(cls):
        """Remove the uploaded test files."""
        shutil.rmtree(TEMP_MEDIA, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        """Create a business and a customer user."""
        self.business = create_profile("biz", UserProfile.BUSINESS)
        self.customer = create_profile("cust", UserProfile.CUSTOMER)
        self.url = reverse("profile-detail", args=[self.business.id])

    def test_get_profile_returns_empty_strings(self):
        """Empty text fields are returned as empty strings."""
        self.client.force_authenticate(self.customer)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["location"], "")
        self.assertEqual(response.data["first_name"], "")
        self.assertEqual(response.data["type"], "business")

    def test_get_profile_requires_authentication(self):
        """Anonymous users get 401."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_unknown_profile_returns_404(self):
        """An unknown user id leads to 404."""
        self.client.force_authenticate(self.customer)
        response = self.client.get(reverse("profile-detail", args=[999]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_owner_can_patch_profile(self):
        """The owner can change profile and user fields."""
        self.client.force_authenticate(self.business)
        data = {"first_name": "Max", "location": "Berlin",
                "email": "new@mail.de"}
        response = self.client.patch(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["first_name"], "Max")
        self.assertEqual(response.data["email"], "new@mail.de")
        self.business.refresh_from_db()
        self.assertEqual(self.business.email, "new@mail.de")

    def test_owner_can_upload_profile_picture(self):
        """A multipart PATCH stores the uploaded file."""
        self.client.force_authenticate(self.business)
        image = SimpleUploadedFile("pic.gif", GIF_BYTES, "image/gif")
        response = self.client.patch(self.url, {"file": image},
                                     format="multipart")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("profile_pictures/", response.data["file"])

    def test_other_user_cannot_patch_profile(self):
        """Somebody else gets 403."""
        self.client.force_authenticate(self.customer)
        response = self.client.patch(self.url, {"location": "Hamburg"})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_patch_rejects_used_email(self):
        """An email address of another account leads to 400."""
        self.client.force_authenticate(self.business)
        response = self.client.patch(self.url, {"email": "cust@mail.de"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class ProfileListTests(APITestCase):
    """Tests for the business and customer profile lists."""

    def setUp(self):
        """Create one profile of each type."""
        self.business = create_profile("biz", UserProfile.BUSINESS)
        self.customer = create_profile("cust", UserProfile.CUSTOMER)
        self.client.force_authenticate(self.customer)

    def test_business_list_contains_only_business_users(self):
        """Only business profiles are listed."""
        response = self.client.get(reverse("profile-business-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["user"], self.business.id)
        self.assertEqual(response.data[0]["tel"], "")

    def test_customer_list_contains_only_customers(self):
        """Only customer profiles are listed."""
        response = self.client.get(reverse("profile-customer-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertIn("uploaded_at", response.data[0])

    def test_lists_require_authentication(self):
        """Anonymous users get 401."""
        self.client.force_authenticate(None)
        response = self.client.get(reverse("profile-customer-list"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_serializer_replaces_none_with_empty_string(self):
        """Text fields that hold ``None`` are returned as empty strings."""
        profile = self.business.profile
        profile.location = None
        profile.user.first_name = None
        data = ProfileDetailSerializer(profile).data
        self.assertEqual(data["location"], "")
        self.assertEqual(data["first_name"], "")

    def test_profile_str_contains_username(self):
        """The string representation shows username and type."""
        self.assertEqual(str(self.business.profile), "biz (business)")
