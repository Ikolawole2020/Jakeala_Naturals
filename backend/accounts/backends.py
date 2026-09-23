"""Authentication backend that accepts an email address *or* a username."""

from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q


class EmailOrUsernameBackend(ModelBackend):
    """Let shoppers sign in with the email they registered with.

    Django's default backend only matches ``username``. Rather than force people
    to remember a generated username, this matches either field (case-insensitive)
    while still running the standard ``check_password`` and the
    ``user_can_authenticate`` active-user gate.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        UserModel = get_user_model()

        identifier = username or kwargs.get("email") or kwargs.get(UserModel.USERNAME_FIELD)
        if not identifier or password is None:
            return None

        matches = (
            UserModel.objects.filter(
                Q(username__iexact=identifier) | Q(email__iexact=identifier)
            )
            .order_by("id")
        )

        user = matches.first()
        if user is None:
            # Run the hasher once anyway so a missing account and a wrong
            # password take a similar amount of time (timing-attack hygiene).
            UserModel().set_password(password)
            return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
