"""Admin configuration of the offers app."""

from django.contrib import admin

from .models import Offer, OfferDetail


class OfferDetailInline(admin.TabularInline):
    """Show the three packages directly inside an offer."""

    model = OfferDetail
    extra = 0


@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    """Admin view listing all offers."""

    list_display = ["title", "user", "created_at", "updated_at"]
    search_fields = ["title", "description", "user__username"]
    inlines = [OfferDetailInline]


@admin.register(OfferDetail)
class OfferDetailAdmin(admin.ModelAdmin):
    """Admin view listing all offer packages."""

    list_display = ["offer", "offer_type", "price", "delivery_time_in_days"]
    list_filter = ["offer_type"]
