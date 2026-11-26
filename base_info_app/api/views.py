"""Views of the base info app."""

from django.db.models import Avg
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from offers_app.models import Offer
from profile_app.models import UserProfile
from reviews_app.models import Review


def get_average_rating():
    """Return the average of all ratings rounded to one decimal."""
    average = Review.objects.aggregate(value=Avg("rating"))["value"]
    return round(average, 1) if average is not None else 0


class BaseInfoView(APIView):
    """Public statistics about the platform."""

    permission_classes = [AllowAny]

    def get(self, request):
        """Return review, rating, business profile and offer numbers."""
        return Response({
            "review_count": Review.objects.count(),
            "average_rating": get_average_rating(),
            "business_profile_count": UserProfile.objects.filter(
                type=UserProfile.BUSINESS
            ).count(),
            "offer_count": Offer.objects.count(),
        })
