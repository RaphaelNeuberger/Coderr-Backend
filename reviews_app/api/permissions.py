"""Permissions of the reviews app."""

from rest_framework.permissions import BasePermission


class IsReviewOwner(BasePermission):
    """Only the author of a review may change or delete it."""

    message = "Only the author of this review can perform this action."

    def has_object_permission(self, request, view, obj):
        """Compare the reviewer with the requesting user."""
        return obj.reviewer_id == request.user.id
