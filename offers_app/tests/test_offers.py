"""Tests for the offer endpoints."""

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from offers_app.models import Offer
from profile_app.models import UserProfile

from .helpers import create_offer, create_user, detail_payload, offer_payload

LIST_URL = reverse("offer-list")


def detail_url(offer):
    """Return the URL of a single offer."""
    return reverse("offer-detail", args=[offer.id])


class OfferListTests(APITestCase):
    """Tests for GET /api/offers/."""

    def setUp(self):
        """Create two business users with offers."""
        self.business = create_user("biz", UserProfile.BUSINESS)
        self.other = create_user("other", UserProfile.BUSINESS)
        self.cheap = create_offer(self.business, "Logo", base_price=50)
        self.expensive = create_offer(self.other, "Website", base_price=300)

    def test_list_is_public_and_paginated(self):
        """Anonymous users get a paginated list with aggregates."""
        response = self.client.get(LIST_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 2)
        first = response.data["results"][0]
        self.assertEqual(first["details"][0]["url"],
                         f"/offerdetails/{first['details'][0]['id']}/")
        self.assertIn("user_details", first)

    def test_list_aggregates_min_values(self):
        """min_price and min_delivery_time are the lowest package values."""
        response = self.client.get(LIST_URL, {"creator_id": self.business.id})
        offer = response.data["results"][0]
        self.assertEqual(offer["min_price"], 50.0)
        self.assertEqual(offer["min_delivery_time"], 5)

    def test_list_filters_by_min_price(self):
        """Only offers with a minimum price above the value are returned."""
        response = self.client.get(LIST_URL, {"min_price": 100})
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["title"], "Website")

    def test_list_filters_by_delivery_time_and_search(self):
        """Delivery time filter and search work together."""
        params = {"max_delivery_time": 5, "search": "web"}
        response = self.client.get(LIST_URL, params)
        self.assertEqual(response.data["count"], 1)

    def test_list_orders_by_min_price(self):
        """Ordering by min_price returns the cheapest offer first."""
        response = self.client.get(LIST_URL, {"ordering": "-min_price"})
        self.assertEqual(response.data["results"][0]["title"], "Website")

    def test_list_ignores_empty_parameters(self):
        """Empty query parameters sent by the frontend are ignored."""
        params = {"creator_id": "", "max_delivery_time": "", "search": ""}
        response = self.client.get(LIST_URL, params)
        self.assertEqual(response.data["count"], 2)

    def test_list_rejects_invalid_parameters(self):
        """A non numeric filter value leads to 400."""
        response = self.client.get(LIST_URL, {"min_price": "abc"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_respects_page_size(self):
        """The page_size parameter limits the results."""
        response = self.client.get(LIST_URL, {"page_size": 1})
        self.assertEqual(len(response.data["results"]), 1)
        self.assertIsNotNone(response.data["next"])


class OfferCreateTests(APITestCase):
    """Tests for POST /api/offers/."""

    def setUp(self):
        """Create a business and a customer user."""
        self.business = create_user("biz", UserProfile.BUSINESS)
        self.customer = create_user("cust", UserProfile.CUSTOMER)

    def test_business_user_creates_offer(self):
        """A business user creates an offer with three packages."""
        self.client.force_authenticate(self.business)
        response = self.client.post(LIST_URL, offer_payload(), format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(response.data["details"]), 3)
        self.assertEqual(response.data["details"][0]["price"], 100.0)
        self.assertEqual(Offer.objects.get().user, self.business)

    def test_create_accepts_price_as_string(self):
        """A price given as string is accepted."""
        self.client.force_authenticate(self.business)
        payload = offer_payload()
        payload["details"][0]["price"] = "99.5"
        response = self.client.post(LIST_URL, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_requires_three_packages(self):
        """Less than three packages lead to 400."""
        self.client.force_authenticate(self.business)
        payload = offer_payload()
        payload["details"] = payload["details"][:2]
        response = self.client.post(LIST_URL, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_rejects_duplicate_types(self):
        """Two packages of the same type lead to 400."""
        self.client.force_authenticate(self.business)
        payload = offer_payload()
        payload["details"][1]["offer_type"] = "basic"
        response = self.client.post(LIST_URL, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_rejects_invalid_numbers(self):
        """Invalid revisions and delivery times lead to 400."""
        self.client.force_authenticate(self.business)
        payload = offer_payload()
        payload["details"][0]["revisions"] = -2
        payload["details"][1]["delivery_time_in_days"] = 0
        response = self.client.post(LIST_URL, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_customer_cannot_create_offer(self):
        """A customer gets 403."""
        self.client.force_authenticate(self.customer)
        response = self.client.post(LIST_URL, offer_payload(), format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_anonymous_cannot_create_offer(self):
        """An anonymous user gets 401."""
        response = self.client.post(LIST_URL, offer_payload(), format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class OfferDetailTests(APITestCase):
    """Tests for GET, PATCH and DELETE /api/offers/{id}/."""

    def setUp(self):
        """Create an offer and two more users."""
        self.business = create_user("biz", UserProfile.BUSINESS)
        self.other = create_user("other", UserProfile.BUSINESS)
        self.offer = create_offer(self.business)

    def test_retrieve_returns_absolute_detail_urls(self):
        """A single offer links to its packages with absolute URLs."""
        self.client.force_authenticate(self.other)
        response = self.client.get(detail_url(self.offer))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["details"][0]["url"].startswith("http"))
        self.assertEqual(response.data["min_price"], 100.0)

    def test_retrieve_requires_authentication(self):
        """Anonymous users get 401."""
        response = self.client.get(detail_url(self.offer))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_retrieve_unknown_offer_returns_404(self):
        """An unknown id leads to 404."""
        self.client.force_authenticate(self.other)
        response = self.client.get(reverse("offer-detail", args=[999]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_owner_patches_title_and_one_package(self):
        """Only the given package changes, its id stays the same."""
        self.client.force_authenticate(self.business)
        basic = self.offer.details.get(offer_type="basic")
        data = {"title": "Updated",
                "details": [detail_payload("basic", 120, 6)]}
        response = self.client.patch(detail_url(self.offer), data,
                                     format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "Updated")
        changed = next(d for d in response.data["details"]
                       if d["offer_type"] == "basic")
        self.assertEqual((changed["id"], changed["price"]), (basic.id, 120.0))

    def test_patch_package_without_type_returns_400(self):
        """A package without offer_type cannot be identified."""
        self.client.force_authenticate(self.business)
        data = {"details": [{"price": 10}]}
        response = self.client.patch(detail_url(self.offer), data,
                                     format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_other_user_cannot_patch_or_delete(self):
        """Somebody else gets 403."""
        self.client.force_authenticate(self.other)
        patch = self.client.patch(detail_url(self.offer), {"title": "X"})
        delete = self.client.delete(detail_url(self.offer))
        self.assertEqual(patch.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(delete.status_code, status.HTTP_403_FORBIDDEN)

    def test_anonymous_cannot_patch_or_delete(self):
        """Anonymous users get 401 and the offer stays."""
        patch = self.client.patch(detail_url(self.offer), {"title": "X"})
        delete = self.client.delete(detail_url(self.offer))
        self.assertEqual(patch.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(delete.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertTrue(Offer.objects.exists())

    def test_owner_deletes_offer(self):
        """The owner deletes the offer and gets 204."""
        self.client.force_authenticate(self.business)
        response = self.client.delete(detail_url(self.offer))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Offer.objects.exists())

    def test_delete_unknown_offer_returns_404(self):
        """Deleting an unknown offer leads to 404."""
        self.client.force_authenticate(self.business)
        response = self.client.delete(reverse("offer-detail", args=[999]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_str_methods(self):
        """Offer and package have readable string representations."""
        basic = self.offer.details.get(offer_type="basic")
        self.assertEqual(str(self.offer), "Website Design")
        self.assertEqual(str(basic), "Website Design (basic)")


class OfferPackageTests(APITestCase):
    """Tests for GET /api/offerdetails/{id}/."""

    def setUp(self):
        """Create an offer and pick its basic package."""
        self.business = create_user("biz", UserProfile.BUSINESS)
        self.detail = create_offer(self.business).details.first()
        self.url = reverse("offerdetail-detail", args=[self.detail.id])

    def test_package_returns_full_data(self):
        """An authenticated user sees all package fields."""
        self.client.force_authenticate(self.business)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["offer_type"], self.detail.offer_type)
        self.assertEqual(response.data["features"], ["Feature"])

    def test_package_requires_authentication(self):
        """Anonymous users get 401."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unknown_package_returns_404(self):
        """An unknown id leads to 404."""
        self.client.force_authenticate(self.business)
        response = self.client.get(reverse("offerdetail-detail", args=[999]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
