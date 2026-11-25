"""Permissions of the profile app."""

from rest_framework.permissions import SAFE_METHODS, BasePermission

from profile_app.models import UserProfile


def has_profile_type(user, profile_type):
    """Return True if the user has a profile of the given type."""
    profile = getattr(user, "profile", None)
    return profile is not None and profile.type == profile_type


class IsBusinessUser(BasePermission):
    """Only users with a business profile are allowed."""

    message = "Only business users can perform this action."

    def has_permission(self, request, view):
        """Check the profile type of the requesting user."""
        return has_profile_type(request.user, UserProfile.BUSINESS)


class IsCustomerUser(BasePermission):
    """Only users with a customer profile are allowed."""

    message = "Only customer users can perform this action."

    def has_permission(self, request, view):
        """Check the profile type of the requesting user."""
        return has_profile_type(request.user, UserProfile.CUSTOMER)


class IsProfileOwnerOrReadOnly(BasePermission):
    """Everybody may read a profile, only its owner may change it."""

    def has_object_permission(self, request, view, obj):
        """Allow safe methods or requests of the profile owner."""
        if request.method in SAFE_METHODS:
            return True
        return obj.user_id == request.user.id
