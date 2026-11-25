"""Database models of the reviews app."""

from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Review(models.Model):
    """A rating of a business user written by a customer."""

    business_user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="reviews_received"
    )
    reviewer = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="reviews_written"
    )
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    description = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Review"
        verbose_name_plural = "Reviews"
        ordering = ["-updated_at"]
        constraints = [
            models.UniqueConstraint(fields=["business_user", "reviewer"],
                                    name="one_review_per_business_user"),
        ]

    def __str__(self):
        """Return reviewer, business user and rating."""
        return (f"{self.reviewer.username} -> {self.business_user.username}"
                f" ({self.rating})")
