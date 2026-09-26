"""Reusable DRF throttle classes.

Every rate is defined once in ``settings.REST_FRAMEWORK`` under
``DEFAULT_THROTTLE_RATES``, so limits can be tuned per deployment without
touching code.

``ScopedRateThrottle`` reads ``scope`` from the class (used with function-based
views) or from ``view.throttle_scope`` (used with viewsets). Throttle counters
are stored in the file-based cache configured in settings, so they survive
PythonAnywhere web-app reloads - a memory cache would hand an attacker a fresh
allowance on every restart.
"""

from rest_framework.throttling import ScopedRateThrottle


class AuthThrottle(ScopedRateThrottle):
    """Sign-in, registration and verification attempts."""

    scope = "auth"


class EmailThrottle(ScopedRateThrottle):
    """Per-address cap on outbound email.

    Keyed by the submitted email so one victim's inbox cannot be flooded, and
    paired with ``EmailIPThrottle`` so one caller cannot spray many addresses.
    """

    scope = "email"

    def get_cache_key(self, request, view):
        email = ""
        if isinstance(request.data, dict):
            email = str(request.data.get("email") or request.data.get("identifier") or "")
        self.rate = self.get_rate()
        self.num_requests, self.duration = self.parse_rate(self.rate)
        return self.cache_format % {"scope": self.scope, "ident": email.strip().lower() or self.get_ident(request)}


class EmailIPThrottle(ScopedRateThrottle):
    """Per-caller cap on outbound email."""

    scope = "email_ip"


class CheckoutThrottle(ScopedRateThrottle):
    """Order creation and payment initialisation."""

    scope = "checkout"


class ContactThrottle(ScopedRateThrottle):
    """Contact / wholesale enquiry form."""

    scope = "contact"


class NewsletterThrottle(ScopedRateThrottle):
    """Newsletter sign-up."""

    scope = "newsletter"


class AdminLoginThrottle(ScopedRateThrottle):
    """Staff dashboard sign-in.

    Without this, ``/api/admin/login/`` allowed unlimited password guessing
    against a known username.
    """

    scope = "admin_login"
