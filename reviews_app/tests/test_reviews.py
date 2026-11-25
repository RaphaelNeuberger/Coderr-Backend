"""Tests for the review endpoints."""

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from offers_app.tests.helpers import create_user
from profile_app.models import UserProfile
from reviews_app.models import Review

LIST_URL = reverse("review-list")


class ReviewTestCase(APITestCase):
    """Base class creating users and one review."""

    def setUp(self):
        """Create two business users, two customers and one review."""
        self.business = create_user("biz", UserProfile.BUSINESS)
        self.business2 = create_user("biz2", UserProfile.BUSINESS)
        self.customer = create_user("cust", UserProfile.CUSTOMER)
        self.customer2 = create_user("cust2", UserProfile.CUSTOMER)
        self.review = Review.objects.create(
            business_user=self.business, reviewer=self.customer, rating=4,
            description="Very professional.",
        )
        self.url = reverse("review-detail", args=[self.review.id])


class ReviewListCreateTests(ReviewTestCase):
    """Tests for GET and POST /api/reviews/."""

    def test_list_filters_and_orders(self):
        """Reviews can be filtered by business user and reviewer."""
        Review.objects.create(business_user=self.business2,
                              reviewer=self.customer, rating=5)
        self.client.force_authenticate(self.customer2)
        params = {"reviewer_id": self.customer.id, "ordering": "-rating"}
        response = self.client.get(LIST_URL, params)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([r["rating"] for r in response.data], [5, 4])
        response = self.client.get(LIST_URL,
                                   {"business_user_id": self.business.id})
        self.assertEqual(len(response.data), 1)

    def test_list_requires_authentication(self):
        """Anonymous users get 401."""
        response = self.client.get(LIST_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_customer_creates_review(self):
        """A customer reviews a business user once."""
        self.client.force_authenticate(self.customer2)
        data = {"business_user": self.business.id, "rating": 5,
                "description": "Great!"}
        response = self.client.post(LIST_URL, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["reviewer"], self.customer2.id)

    def test_second_review_returns_400(self):
        """A second review for the same business user leads to 400."""
        self.client.force_authenticate(self.customer)
        data = {"business_user": self.business.id, "rating": 3}
        response = self.client.post(LIST_URL, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_review_of_customer_or_invalid_rating_returns_400(self):
        """Only business users with ratings from 1 to 5 can be reviewed."""
        self.client.force_authenticate(self.customer2)
        for data in [{"business_user": self.customer.id, "rating": 3},
                     {"business_user": self.business.id, "rating": 6}]:
            response = self.client.post(LIST_URL, data)
            self.assertEqual(response.status_code,
                             status.HTTP_400_BAD_REQUEST)

    def test_business_user_cannot_create_review(self):
        """A business user gets 403."""
        self.client.force_authenticate(self.business2)
        data = {"business_user": self.business.id, "rating": 5}
        response = self.client.post(LIST_URL, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class ReviewUpdateDeleteTests(ReviewTestCase):
    """Tests for PATCH and DELETE /api/reviews/{id}/."""

    def test_reviewer_updates_rating_and_description(self):
        """Only rating and description change."""
        self.client.force_authenticate(self.customer)
        data = {"rating": 5, "description": "Even better!",
                "business_user": self.business2.id}
        response = self.client.patch(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["rating"], 5)
        self.assertEqual(response.data["business_user"], self.business.id)

    def test_other_user_cannot_update_or_delete(self):
        """Somebody else gets 403."""
        self.client.force_authenticate(self.customer2)
        patch = self.client.patch(self.url, {"rating": 1})
        delete = self.client.delete(self.url)
        self.assertEqual(patch.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(delete.status_code, status.HTTP_403_FORBIDDEN)

    def test_reviewer_deletes_review(self):
        """The reviewer deletes the review and gets 204."""
        self.client.force_authenticate(self.customer)
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Review.objects.exists())

    def test_unknown_review_returns_404(self):
        """An unknown id leads to 404."""
        self.client.force_authenticate(self.customer)
        response = self.client.patch(reverse("review-detail", args=[999]),
                                     {"rating": 2})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_review_str(self):
        """The string representation shows both users and the rating."""
        self.assertEqual(str(self.review), "cust -> biz (4)")
