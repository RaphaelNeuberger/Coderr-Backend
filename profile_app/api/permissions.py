"""Permissions of the profile app."""

from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsProfileOwnerOrReadOnly(BasePermission):
    """Everybody may read a profile, only its owner may change it."""

    def has_object_permission(self, request, view, obj):
        """Allow safe methods or requests of the profile owner."""
        if request.method in SAFE_METHODS:
            return True
        return obj.user_id == request.user.id
