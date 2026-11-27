"""App configuration of the profile app."""

from django.apps import AppConfig


class ProfileAppConfig(AppConfig):
    """Configuration of the profile app."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'profile_app'
