"""Views for registration and login."""

from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import LoginSerializer, RegistrationSerializer


def build_auth_response(user):
    """Return the token and the basic user data for a response."""
    token, _ = Token.objects.get_or_create(user=user)
    return {
        "token": token.key,
        "username": user.username,
        "email": user.email,
        "user_id": user.id,
    }


class RegistrationView(APIView):
    """Register a new customer or business user."""

    permission_classes = [AllowAny]

    def post(self, request):
        """Create the account and return its token."""
        serializer = RegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(build_auth_response(user),
                        status=status.HTTP_201_CREATED)


class LoginView(APIView):
    """Log in an existing user."""

    permission_classes = [AllowAny]

    def post(self, request):
        """Check the credentials and return the token."""
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        return Response(build_auth_response(user), status=status.HTTP_200_OK)
