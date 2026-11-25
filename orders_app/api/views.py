"""Views of the orders app."""

from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import mixins, status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from offers_app.models import OfferDetail
from orders_app.models import Order
from profile_app.api.permissions import IsBusinessUser, IsCustomerUser
from profile_app.models import UserProfile

from .permissions import IsOrderBusinessUser
from .serializers import (OrderCreateSerializer, OrderSerializer,
                          OrderStatusSerializer)

ORDER_SNAPSHOT_FIELDS = ["title", "revisions", "delivery_time_in_days",
                         "price", "features", "offer_type"]


def create_order_from_detail(customer, detail):
    """Create an order that copies the data of an offer package."""
    snapshot = {field: getattr(detail, field)
                for field in ORDER_SNAPSHOT_FIELDS}
    return Order.objects.create(
        customer_user=customer, business_user=detail.offer.user,
        offer_detail=detail, **snapshot
    )


class OrderViewSet(mixins.ListModelMixin, mixins.CreateModelMixin,
                   mixins.UpdateModelMixin, viewsets.GenericViewSet):
    """List, create and update the status of orders."""

    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    http_method_names = ["get", "post", "patch", "options"]

    def get_queryset(self):
        """List only orders in which the requesting user takes part."""
        if self.action != "list":
            return super().get_queryset()
        user = self.request.user
        return super().get_queryset().filter(
            Q(customer_user=user) | Q(business_user=user)
        )

    def get_permissions(self):
        """Choose the permissions depending on the action."""
        if self.action == "create":
            permission_classes = [IsAuthenticated & IsCustomerUser]
        elif self.action == "partial_update":
            permission_classes = [IsAuthenticated & IsBusinessUser
                                  & IsOrderBusinessUser]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_serializer_class(self):
        """Use the status serializer for updates."""
        if self.action == "partial_update":
            return OrderStatusSerializer
        return self.serializer_class

    def create(self, request, *args, **kwargs):
        """Create an order based on the given offer package."""
        serializer = OrderCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        detail = get_object_or_404(
            OfferDetail.objects.select_related("offer"),
            pk=serializer.validated_data["offer_detail_id"],
        )
        order = create_order_from_detail(request.user, detail)
        return Response(OrderSerializer(order).data,
                        status=status.HTTP_201_CREATED)


class OrderCountView(APIView):
    """Count the orders of a business user with a given status."""

    permission_classes = [IsAuthenticated]
    order_status = Order.IN_PROGRESS
    response_key = "order_count"

    def get(self, request, business_user_id):
        """Return the number of matching orders."""
        get_object_or_404(UserProfile, user_id=business_user_id,
                          type=UserProfile.BUSINESS)
        count = Order.objects.filter(business_user_id=business_user_id,
                                     status=self.order_status).count()
        return Response({self.response_key: count})


class CompletedOrderCountView(OrderCountView):
    """Count the completed orders of a business user."""

    order_status = Order.COMPLETED
    response_key = "completed_order_count"
