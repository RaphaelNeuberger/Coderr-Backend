"""Tests for GET /api/base-info/."""

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from offers_app.tests.helpers import create_offer, create_user
from profile_app.models import UserProfile
from reviews_app.models import Review

URL = reverse("base-info")


class BaseInfoTests(APITestCase):
    """Tests for the platform statistics."""

    def test_empty_platform_returns_zeros(self):
        """Without data every value is zero."""
        response = self.client.get(URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {
            "review_count": 0, "average_rating": 0,
            "business_profile_count": 0, "offer_count": 0,
        })

    def test_statistics_are_public_and_rounded(self):
        """Counts are correct and the average has one decimal."""
        business = create_user("biz", UserProfile.BUSINESS)
        create_offer(business)
        for name, rating in [("a", 5), ("b", 4), ("c", 4)]:
            reviewer = create_user(name, UserProfile.CUSTOMER)
            Review.objects.create(business_user=business, reviewer=reviewer,
                                  rating=rating)
        response = self.client.get(URL)
        self.assertEqual(response.data["review_count"], 3)
        self.assertEqual(response.data["average_rating"], 4.3)
        self.assertEqual(response.data["business_profile_count"], 1)
        self.assertEqual(response.data["offer_count"], 1)
