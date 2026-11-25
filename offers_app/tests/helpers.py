"""Shared helpers to create test data for offers."""

from django.contrib.auth.models import User

from offers_app.models import Offer, OfferDetail
from profile_app.models import UserProfile

PACKAGES = [
    ("basic", 100, 5),
    ("standard", 200, 7),
    ("premium", 500, 10),
]


def create_user(username, profile_type):
    """Create a user with a profile of the given type."""
    user = User.objects.create_user(username, f"{username}@mail.de", "pw")
    UserProfile.objects.create(user=user, type=profile_type)
    return user


def detail_payload(offer_type, price, days):
    """Return the request data of one offer package."""
    return {
        "title": f"{offer_type.title()} Design",
        "revisions": 2,
        "delivery_time_in_days": days,
        "price": price,
        "features": ["Logo Design"],
        "offer_type": offer_type,
    }


def offer_payload(title="Grafikdesign-Paket"):
    """Return a valid request body to create an offer."""
    return {
        "title": title,
        "image": None,
        "description": "Ein umfassendes Paket.",
        "details": [detail_payload(*package) for package in PACKAGES],
    }


def create_offer(user, title="Website Design", base_price=100):
    """Create an offer with three packages directly in the database."""
    offer = Offer.objects.create(user=user, title=title,
                                 description="Professional work")
    for index, (offer_type, _, days) in enumerate(PACKAGES):
        OfferDetail.objects.create(
            offer=offer, title=offer_type, revisions=1,
            delivery_time_in_days=days, price=base_price * (index + 1),
            features=["Feature"], offer_type=offer_type,
        )
    return offer
