"""Permissions of the orders app."""

from rest_framework.permissions import BasePermission


class IsOrderBusinessUser(BasePermission):
    """Only the business user of an order may change its status."""

    message = "Only the business user of this order can update it."

    def has_object_permission(self, request, view, obj):
        """Compare the business user of the order with the requester."""
        return obj.business_user_id == request.user.id
