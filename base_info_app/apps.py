"""App configuration of the base info app."""

from django.apps import AppConfig


class BaseInfoAppConfig(AppConfig):
    """Configuration of the base info app."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'base_info_app'
