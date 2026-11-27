"""App configuration of the reviews app."""

from django.apps import AppConfig


class ReviewsAppConfig(AppConfig):
    """Configuration of the reviews app."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'reviews_app'
