"""Views of the reviews app."""

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, viewsets
from rest_framework.permissions import IsAuthenticated

from profile_app.api.permissions import IsCustomerUser
from reviews_app.models import Review

from .filters import ReviewFilter
from .permissions import IsReviewOwner
from .serializers import ReviewSerializer, ReviewUpdateSerializer


class ReviewViewSet(viewsets.ModelViewSet):
    """List, create, update and delete reviews."""

    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = ReviewFilter
    ordering_fields = ["updated_at", "rating"]
    http_method_names = ["get", "post", "patch", "delete", "options"]

    def get_permissions(self):
        """Choose the permissions depending on the action."""
        if self.action == "create":
            permission_classes = [IsAuthenticated & IsCustomerUser]
        elif self.action in ["partial_update", "destroy"]:
            permission_classes = [IsAuthenticated & IsReviewOwner]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_serializer_class(self):
        """Use the restricted serializer for updates."""
        if self.action == "partial_update":
            return ReviewUpdateSerializer
        return self.serializer_class

    def perform_create(self, serializer):
        """Save the requesting customer as reviewer."""
        serializer.save(reviewer=self.request.user)
