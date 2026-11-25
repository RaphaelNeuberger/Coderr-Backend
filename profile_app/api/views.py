"""Views of the profile app."""

from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from profile_app.models import UserProfile

from .permissions import IsProfileOwnerOrReadOnly
from .serializers import (BusinessProfileListSerializer,
                          CustomerProfileListSerializer,
                          ProfileDetailSerializer)


class ProfileDetailView(generics.RetrieveUpdateAPIView):
    """Read (GET) or partially update (PATCH) the profile of a user."""

    queryset = UserProfile.objects.select_related("user")
    serializer_class = ProfileDetailSerializer
    permission_classes = [IsAuthenticated & IsProfileOwnerOrReadOnly]
    lookup_field = "user_id"
    lookup_url_kwarg = "pk"
    http_method_names = ["get", "patch", "options"]


class BusinessProfileListView(generics.ListAPIView):
    """List all business profiles."""

    queryset = UserProfile.objects.filter(
        type=UserProfile.BUSINESS
    ).select_related("user")
    serializer_class = BusinessProfileListSerializer
    permission_classes = [IsAuthenticated]


class CustomerProfileListView(generics.ListAPIView):
    """List all customer profiles."""

    queryset = UserProfile.objects.filter(
        type=UserProfile.CUSTOMER
    ).select_related("user")
    serializer_class = CustomerProfileListSerializer
    permission_classes = [IsAuthenticated]
