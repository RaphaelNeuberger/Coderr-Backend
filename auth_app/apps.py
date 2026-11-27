"""App configuration of the authentication app."""

from django.apps import AppConfig


class AuthAppConfig(AppConfig):
    """Configuration of the authentication app."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'auth_app'
