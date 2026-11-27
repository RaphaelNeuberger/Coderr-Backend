"""App configuration of the orders app."""

from django.apps import AppConfig


class OrdersAppConfig(AppConfig):
    """Configuration of the orders app."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'orders_app'
