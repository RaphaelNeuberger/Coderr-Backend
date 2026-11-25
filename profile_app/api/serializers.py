"""Serializers of the profile app."""

from django.contrib.auth.models import User
from rest_framework import serializers

from profile_app.models import UserProfile

NON_NULL_FIELDS = ["first_name", "last_name", "location", "tel",
                   "description", "working_hours"]
USER_FIELDS = ["first_name", "last_name", "email"]


class EmptyStringMixin:
    """Replace ``None`` with an empty string in the text fields."""

    def to_representation(self, instance):
        """Return the data without ``None`` values in text fields."""
        data = super().to_representation(instance)
        for field in NON_NULL_FIELDS:
            if field in data and data[field] is None:
                data[field] = ""
        return data


class ProfileDetailSerializer(EmptyStringMixin, serializers.ModelSerializer):
    """Full profile of one user, used for reading and updating."""

    username = serializers.CharField(source="user.username", read_only=True)
    first_name = serializers.CharField(
        source="user.first_name", required=False, allow_blank=True
    )
    last_name = serializers.CharField(
        source="user.last_name", required=False, allow_blank=True
    )
    email = serializers.EmailField(source="user.email", required=False)

    class Meta:
        model = UserProfile
        fields = ["user", "username", "first_name", "last_name", "file",
                  "location", "tel", "description", "working_hours", "type",
                  "email", "created_at"]
        read_only_fields = ["user", "type", "created_at"]

    def validate_email(self, value):
        """Make sure that no other account uses this email address."""
        others = User.objects.exclude(pk=self.instance.user_id)
        if others.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Email is already in use.")
        return value

    def update(self, instance, validated_data):
        """Update the profile and the related user fields."""
        user_data = validated_data.pop("user", {})
        for field in USER_FIELDS:
            if field in user_data:
                setattr(instance.user, field, user_data[field])
        instance.user.save()
        return super().update(instance, validated_data)


class BusinessProfileListSerializer(EmptyStringMixin,
                                    serializers.ModelSerializer):
    """Short profile of a business user for the business list."""

    username = serializers.CharField(source="user.username", read_only=True)
    first_name = serializers.CharField(source="user.first_name",
                                       read_only=True)
    last_name = serializers.CharField(source="user.last_name",
                                      read_only=True)

    class Meta:
        model = UserProfile
        fields = ["user", "username", "first_name", "last_name", "file",
                  "location", "tel", "description", "working_hours", "type"]


class CustomerProfileListSerializer(EmptyStringMixin,
                                    serializers.ModelSerializer):
    """Short profile of a customer for the customer list."""

    username = serializers.CharField(source="user.username", read_only=True)
    first_name = serializers.CharField(source="user.first_name",
                                       read_only=True)
    last_name = serializers.CharField(source="user.last_name",
                                      read_only=True)

    class Meta:
        model = UserProfile
        fields = ["user", "username", "first_name", "last_name", "file",
                  "uploaded_at", "type"]
