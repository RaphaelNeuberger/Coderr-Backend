"""Serializers for registration and login."""

from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.db import transaction
from rest_framework import serializers

from profile_app.models import UserProfile


class RegistrationSerializer(serializers.ModelSerializer):
    """Validate the registration data and create user plus profile."""

    repeated_password = serializers.CharField(write_only=True)
    type = serializers.ChoiceField(
        choices=UserProfile.TYPE_CHOICES, write_only=True
    )

    class Meta:
        model = User
        fields = ["username", "email", "password", "repeated_password",
                  "type"]
        extra_kwargs = {
            "password": {"write_only": True},
            "email": {"required": True, "allow_blank": False},
        }

    def validate_email(self, value):
        """Make sure that no other account uses this email address."""
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Email is already in use.")
        return value

    def validate(self, attrs):
        """Check that both passwords are identical."""
        if attrs["password"] != attrs["repeated_password"]:
            raise serializers.ValidationError(
                {"repeated_password": "Passwords do not match."}
            )
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        """Create the user with a hashed password and its profile."""
        profile_type = validated_data.pop("type")
        validated_data.pop("repeated_password")
        user = User.objects.create_user(**validated_data)
        UserProfile.objects.create(user=user, type=profile_type)
        return user


class LoginSerializer(serializers.Serializer):
    """Validate username and password of a login request."""

    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        """Authenticate the user and attach it to the validated data."""
        user = authenticate(
            username=attrs["username"], password=attrs["password"]
        )
        if user is None:
            raise serializers.ValidationError("Invalid username or password.")
        attrs["user"] = user
        return attrs
