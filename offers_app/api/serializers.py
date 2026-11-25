"""Serializers of the offers app."""

from django.db import transaction
from django.urls import reverse
from rest_framework import serializers

from offers_app.models import Offer, OfferDetail

REQUIRED_TYPES = {OfferDetail.BASIC, OfferDetail.STANDARD,
                  OfferDetail.PREMIUM}
DETAIL_FIELDS = ["title", "revisions", "delivery_time_in_days", "price",
                 "features"]


class OfferDetailSerializer(serializers.ModelSerializer):
    """Full data of one offer package."""

    price = serializers.DecimalField(max_digits=10, decimal_places=2,
                                     min_value=0, coerce_to_string=False)
    features = serializers.ListField(child=serializers.CharField())

    class Meta:
        model = OfferDetail
        fields = ["id", "title", "revisions", "delivery_time_in_days",
                  "price", "features", "offer_type"]

    def validate_revisions(self, value):
        """Allow -1 (unlimited) or any non negative number."""
        if value < -1:
            raise serializers.ValidationError("Use -1 for unlimited.")
        return value

    def validate_delivery_time_in_days(self, value):
        """The delivery time must be a positive number of days."""
        if value < 1:
            raise serializers.ValidationError("Must be at least 1 day.")
        return value


class OfferDetailLinkSerializer(serializers.ModelSerializer):
    """Id and URL of an offer package."""

    url = serializers.SerializerMethodField()

    class Meta:
        model = OfferDetail
        fields = ["id", "url"]

    def get_url(self, obj):
        """Return the relative or absolute URL of the package."""
        path = reverse("offerdetail-detail", args=[obj.id])
        request = self.context.get("request")
        if self.context.get("absolute_urls") and request:
            return request.build_absolute_uri(path)
        return path.removeprefix("/api")


class OfferListSerializer(serializers.ModelSerializer):
    """Offer as shown in the paginated offer list."""

    details = OfferDetailLinkSerializer(many=True, read_only=True)
    min_price = serializers.FloatField(read_only=True)
    min_delivery_time = serializers.IntegerField(read_only=True)
    user_details = serializers.SerializerMethodField()

    class Meta:
        model = Offer
        fields = ["id", "user", "title", "image", "description",
                  "created_at", "updated_at", "details", "min_price",
                  "min_delivery_time", "user_details"]

    def get_user_details(self, obj):
        """Return the public name data of the offer creator."""
        return {
            "first_name": obj.user.first_name,
            "last_name": obj.user.last_name,
            "username": obj.user.username,
        }


class OfferRetrieveSerializer(OfferListSerializer):
    """Single offer with absolute URLs to its packages."""

    class Meta(OfferListSerializer.Meta):
        fields = ["id", "user", "title", "image", "description",
                  "created_at", "updated_at", "details", "min_price",
                  "min_delivery_time"]


class OfferWriteSerializer(serializers.ModelSerializer):
    """Create an offer with three packages or update parts of it."""

    details = OfferDetailSerializer(many=True)

    class Meta:
        model = Offer
        fields = ["id", "title", "image", "description", "details"]

    def validate_details(self, value):
        """Check the package types for create and update requests."""
        types = [detail.get("offer_type") for detail in value]
        if None in types or len(types) != len(set(types)):
            raise serializers.ValidationError(
                "Every detail needs a unique offer_type."
            )
        if self.instance is None and set(types) != REQUIRED_TYPES:
            raise serializers.ValidationError(
                "An offer needs exactly one basic, standard and premium "
                "detail."
            )
        return value

    @transaction.atomic
    def create(self, validated_data):
        """Create the offer together with its three packages."""
        details = validated_data.pop("details")
        offer = Offer.objects.create(**validated_data)
        OfferDetail.objects.bulk_create(
            [OfferDetail(offer=offer, **detail) for detail in details]
        )
        return offer

    @transaction.atomic
    def update(self, instance, validated_data):
        """Update the offer and the packages identified by offer_type."""
        details = validated_data.pop("details", [])
        for detail_data in details:
            self.update_detail(instance, detail_data)
        return super().update(instance, validated_data)

    def update_detail(self, offer, detail_data):
        """Update one package of the offer, keeping its id."""
        detail = offer.details.get(offer_type=detail_data["offer_type"])
        for field in DETAIL_FIELDS:
            if field in detail_data:
                setattr(detail, field, detail_data[field])
        detail.save()
