"""Management command that creates the guest accounts of the frontend."""

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from profile_app.models import UserProfile

GUEST_USERS = [
    {
        "username": "andrey",
        "password": "asdasd",
        "email": "andrey.guest@coderr.de",
        "first_name": "Andrey",
        "last_name": "Guest",
        "type": UserProfile.CUSTOMER,
    },
    {
        "username": "kevin",
        "password": "asdasd24",
        "email": "kevin.guest@coderr.de",
        "first_name": "Kevin",
        "last_name": "Guest",
        "type": UserProfile.BUSINESS,
    },
]


class Command(BaseCommand):
    """Create (or reset) the guest users used by the frontend guest login."""

    help = "Creates the customer and business guest users."

    def handle(self, *args, **options):
        """Create every guest user and report the result."""
        for guest in GUEST_USERS:
            created = self.create_guest(dict(guest))
            action = "created" if created else "updated"
            self.stdout.write(
                self.style.SUCCESS(f"Guest {guest['username']} {action}.")
            )

    def create_guest(self, guest):
        """Create the user and profile, reset the password."""
        password = guest.pop("password")
        profile_type = guest.pop("type")
        user, created = User.objects.get_or_create(
            username=guest.pop("username"), defaults=guest
        )
        user.set_password(password)
        user.save()
        UserProfile.objects.get_or_create(
            user=user, defaults={"type": profile_type}
        )
        return created
