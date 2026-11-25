"""URL routes of the offers app."""

from django.urls import include, path
from rest_framework.routers import SimpleRouter

from .views import OfferDetailView, OfferViewSet

router = SimpleRouter()
router.register("offers", OfferViewSet, basename="offer")

urlpatterns = [
    path("", include(router.urls)),
    path("offerdetails/<int:pk>/", OfferDetailView.as_view(),
         name="offerdetail-detail"),
]
