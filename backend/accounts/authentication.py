"""Token authentication with an expiry.

DRF ships ``TokenAuthentication``, whose tokens live until they are explicitly
deleted. A leaked token would therefore grant permanent access to the store
admin. This subclass rejects (and deletes) any token older than
``settings.AUTH_TOKEN_TTL`` seconds, so a stolen token stops working and the
owner simply signs in again to get a fresh one.
"""

from datetime import timedelta

from django.conf import settings
from django.utils import timezone
from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import AuthenticationFailed


class ExpiringTokenAuthentication(TokenAuthentication):
    """``Authorization: Token <key>`` authentication with a maximum age."""

    def authenticate_credentials(self, key):
        user, token = super().authenticate_credentials(key)

        ttl = getattr(settings, "AUTH_TOKEN_TTL", 0)
        if ttl and token.created < timezone.now() - timedelta(seconds=ttl):
            # Burn the token so the rejected key can never work again.
            token.delete()
            raise AuthenticationFailed(
                "Your session has expired. Please sign in again.", code="token_expired"
            )

        return user, token
