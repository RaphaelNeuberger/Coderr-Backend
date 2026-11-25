"""Views of the offers app."""

from django.db.models import Min
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated

from offers_app.models import Offer, OfferDetail
from profile_app.api.permissions import IsBusinessUser

from .filters import OfferFilter, OfferPagination
from .permissions import IsOfferOwner
from .serializers import (OfferDetailSerializer, OfferListSerializer,
                          OfferRetrieveSerializer, OfferWriteSerializer)

READ_SERIALIZERS = {
    "list": OfferListSerializer,
    "retrieve": OfferRetrieveSerializer,
}


class OfferViewSet(viewsets.ModelViewSet):
    """List, create, read, update and delete offers."""

    queryset = Offer.objects.select_related("user").prefetch_related(
        "details"
    )
    serializer_class = OfferWriteSerializer
    pagination_class = OfferPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter,
                       filters.OrderingFilter]
    filterset_class = OfferFilter
    search_fields = ["title", "description"]
    ordering_fields = ["updated_at", "min_price"]
    ordering = ["-updated_at"]
    http_method_names = ["get", "post", "patch", "delete", "options"]

    def get_queryset(self):
        """Add the lowest price and delivery time of every offer."""
        return super().get_queryset().annotate(
            min_price=Min("details__price"),
            min_delivery_time=Min("details__delivery_time_in_days"),
        )

    def get_permissions(self):
        """Choose the permissions depending on the action."""
        if self.action == "list":
            permission_classes = [AllowAny]
        elif self.action == "create":
            permission_classes = [IsAuthenticated & IsBusinessUser]
        elif self.action == "retrieve":
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAuthenticated & IsOfferOwner]
        return [permission() for permission in permission_classes]

    def get_serializer_class(self):
        """Use read serializers for list and retrieve."""
        return READ_SERIALIZERS.get(self.action, self.serializer_class)

    def get_serializer_context(self):
        """Request absolute package URLs for a single offer."""
        context = super().get_serializer_context()
        context["absolute_urls"] = self.action == "retrieve"
        return context

    def perform_create(self, serializer):
        """Save the requesting business user as creator."""
        serializer.save(user=self.request.user)


class OfferDetailView(generics.RetrieveAPIView):
    """Read a single offer package."""

    queryset = OfferDetail.objects.all()
    serializer_class = OfferDetailSerializer
    permission_classes = [IsAuthenticated]
