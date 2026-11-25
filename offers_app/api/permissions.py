"""Permissions of the offers app."""

from rest_framework.permissions import BasePermission


class IsOfferOwner(BasePermission):
    """Only the creator of an offer may change or delete it."""

    message = "Only the creator of this offer can perform this action."

    def has_object_permission(self, request, view, obj):
        """Compare the offer creator with the requesting user."""
        return obj.user_id == request.user.id
