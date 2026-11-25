"""Serializers of the reviews app."""

from rest_framework import serializers

from profile_app.models import UserProfile
from reviews_app.models import Review

REVIEW_FIELDS = ["id", "business_user", "reviewer", "rating", "description",
                 "created_at", "updated_at"]


class ReviewSerializer(serializers.ModelSerializer):
    """Create and read reviews."""

    class Meta:
        model = Review
        fields = REVIEW_FIELDS
        read_only_fields = ["reviewer", "created_at", "updated_at"]
        validators = []

    def validate_business_user(self, value):
        """Only business users can be reviewed."""
        profile = getattr(value, "profile", None)
        if profile is None or profile.type != UserProfile.BUSINESS:
            raise serializers.ValidationError("User is not a business user.")
        return value

    def validate(self, attrs):
        """Allow only one review per reviewer and business user."""
        reviewer = self.context["request"].user
        if Review.objects.filter(business_user=attrs["business_user"],
                                 reviewer=reviewer).exists():
            raise serializers.ValidationError(
                "You have already reviewed this business user."
            )
        return attrs


class ReviewUpdateSerializer(serializers.ModelSerializer):
    """Update only rating and description of a review."""

    class Meta:
        model = Review
        fields = REVIEW_FIELDS
        read_only_fields = ["business_user", "reviewer", "created_at",
                            "updated_at"]
