"""Filters and pagination of the offer list."""

import django_filters
from rest_framework.pagination import PageNumberPagination

from offers_app.models import Offer


class OfferFilter(django_filters.FilterSet):
    """Query parameters to filter the offer list."""

    creator_id = django_filters.NumberFilter(field_name="user_id")
    min_price = django_filters.NumberFilter(field_name="min_price",
                                            lookup_expr="gte")
    max_delivery_time = django_filters.NumberFilter(
        field_name="min_delivery_time", lookup_expr="lte"
    )

    class Meta:
        model = Offer
        fields = ["creator_id", "min_price", "max_delivery_time"]


class OfferPagination(PageNumberPagination):
    """Page number pagination matching the frontend page size."""

    page_size = 6
    page_size_query_param = "page_size"
    max_page_size = 100
