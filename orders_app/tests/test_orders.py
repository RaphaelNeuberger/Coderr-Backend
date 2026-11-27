"""Tests for the order endpoints."""

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from offers_app.tests.helpers import create_offer, create_user
from orders_app.models import Order
from profile_app.models import UserProfile

LIST_URL = reverse("order-list")


class OrderTestCase(APITestCase):
    """Base class creating users, an offer and an order."""

    def setUp(self):
        """Create business, customer, a stranger and one order."""
        self.business = create_user("biz", UserProfile.BUSINESS)
        self.customer = create_user("cust", UserProfile.CUSTOMER)
        self.stranger = create_user("other", UserProfile.CUSTOMER)
        self.detail = create_offer(self.business).details.get(
            offer_type="basic"
        )
        self.order = Order.objects.create(
            customer_user=self.customer, business_user=self.business,
            offer_detail=self.detail, title="Logo", revisions=1,
            delivery_time_in_days=5, price=100, offer_type="basic",
        )

    def order_url(self, order_id=None):
        """Return the URL of the order or of the given id."""
        return reverse("order-detail", args=[order_id or self.order.id])


class OrderListCreateTests(OrderTestCase):
    """Tests for GET and POST /api/orders/."""

    def test_list_contains_own_orders_only(self):
        """Customer and business user see the order, a stranger not."""
        for user, expected in [(self.customer, 1), (self.business, 1),
                               (self.stranger, 0)]:
            self.client.force_authenticate(user)
            response = self.client.get(LIST_URL)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(len(response.data), expected)

    def test_list_timestamps_use_utc_format(self):
        """Timestamps end with ``Z`` like in the API documentation."""
        self.client.force_authenticate(self.customer)
        order = self.client.get(LIST_URL).data[0]
        self.assertTrue(order["created_at"].endswith("Z"))
        self.assertTrue(order["updated_at"].endswith("Z"))

    def test_list_requires_authentication(self):
        """Anonymous users get 401."""
        response = self.client.get(LIST_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_customer_creates_order_from_package(self):
        """The order copies the package data and both users."""
        self.client.force_authenticate(self.stranger)
        response = self.client.post(LIST_URL,
                                    {"offer_detail_id": self.detail.id})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["business_user"], self.business.id)
        self.assertEqual(response.data["customer_user"], self.stranger.id)
        self.assertEqual(response.data["price"], 100.0)
        self.assertEqual(response.data["status"], "in_progress")

    def test_create_without_id_returns_400(self):
        """A missing offer_detail_id leads to 400."""
        self.client.force_authenticate(self.customer)
        response = self.client.post(LIST_URL, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_with_unknown_id_returns_404(self):
        """An unknown package leads to 404."""
        self.client.force_authenticate(self.customer)
        response = self.client.post(LIST_URL, {"offer_detail_id": 999})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_business_user_cannot_create_order(self):
        """A business user gets 403."""
        self.client.force_authenticate(self.business)
        response = self.client.post(LIST_URL,
                                    {"offer_detail_id": self.detail.id})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class OrderUpdateTests(OrderTestCase):
    """Tests for PATCH /api/orders/{id}/."""

    def test_business_user_updates_status(self):
        """The business user of the order can complete it."""
        self.client.force_authenticate(self.business)
        response = self.client.patch(self.order_url(),
                                     {"status": "completed"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "completed")
        self.assertEqual(response.data["title"], "Logo")

    def test_invalid_status_returns_400(self):
        """An unknown status leads to 400."""
        self.client.force_authenticate(self.business)
        response = self.client.patch(self.order_url(), {"status": "done"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_other_fields_return_400(self):
        """Fields other than status lead to 400."""
        self.client.force_authenticate(self.business)
        data = {"status": "completed", "price": 1}
        response = self.client.patch(self.order_url(), data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_customer_cannot_update_status(self):
        """The customer of the order gets 403."""
        self.client.force_authenticate(self.customer)
        response = self.client.patch(self.order_url(),
                                     {"status": "completed"})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_other_business_user_cannot_update_status(self):
        """A business user of another order gets 403."""
        other_business = create_user("biz2", UserProfile.BUSINESS)
        self.client.force_authenticate(other_business)
        response = self.client.patch(self.order_url(),
                                     {"status": "completed"})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_requires_authentication(self):
        """Anonymous users get 401."""
        response = self.client.patch(self.order_url(),
                                     {"status": "completed"})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unknown_order_returns_404(self):
        """An unknown order leads to 404."""
        self.client.force_authenticate(self.business)
        response = self.client.patch(self.order_url(999),
                                     {"status": "completed"})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_order_str(self):
        """The string representation shows title and status."""
        self.assertEqual(str(self.order), "Logo (in_progress)")


class OrderCountTests(OrderTestCase):
    """Tests for the order count endpoints."""

    def test_counts_orders_by_status(self):
        """Running and completed orders are counted separately."""
        self.client.force_authenticate(self.customer)
        running = self.client.get(reverse("order-count",
                                          args=[self.business.id]))
        completed = self.client.get(reverse("completed-order-count",
                                            args=[self.business.id]))
        self.assertEqual(running.data, {"order_count": 1})
        self.assertEqual(completed.data, {"completed_order_count": 0})

    def test_count_for_unknown_business_user_returns_404(self):
        """A customer id or unknown id leads to 404."""
        self.client.force_authenticate(self.customer)
        response = self.client.get(reverse("order-count",
                                           args=[self.customer.id]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_count_requires_authentication(self):
        """Anonymous users get 401."""
        response = self.client.get(reverse("completed-order-count",
                                           args=[self.business.id]))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
