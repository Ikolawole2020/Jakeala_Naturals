"""Server-side Paystack client.

Only the HTTPS API is used here; the **secret key never reaches the browser**.
The public key is handed to the front end by ``/api/payments/config/`` because
Paystack's inline popup needs it, and it is safe there by design.

Every call funnels through ``_request`` and raises ``PaystackError`` on failure,
so a Paystack outage becomes a friendly message instead of a 500.

``api.paystack.co`` is on the PythonAnywhere free-tier allowlist, so this works
without a paid plan.
"""

import hashlib
import hmac
import json
import logging
import urllib.error
import urllib.parse
import urllib.request
from decimal import Decimal

from django.conf import settings

logger = logging.getLogger(__name__)

BASE_URL = "https://api.paystack.co"


class PaystackError(Exception):
    """Any failure talking to Paystack - network, auth or API-side."""

    def __init__(self, message, *, status_code=None):
        super().__init__(message)
        self.status_code = status_code


def is_configured():
    """True when a secret key is present."""
    return bool(settings.PAYSTACK_SECRET_KEY)


def amount_in_kobo(amount):
    """Convert naira to kobo as an int. Paystack rejects decimal amounts."""
    return int((Decimal(str(amount)) * 100).quantize(Decimal("1")))


def _request(method, path, payload=None):
    """Call the Paystack API and return the decoded JSON body."""
    if not is_configured():
        raise PaystackError("Paystack is not configured (PAYSTACK_SECRET_KEY is empty).")

    request = urllib.request.Request(
        f"{BASE_URL}{path}",
        data=json.dumps(payload).encode("utf-8") if payload is not None else None,
        method=method,
        headers={
            "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=settings.PAYSTACK_TIMEOUT) as response:
            raw = response.read().decode("utf-8", "replace")
            return json.loads(raw) if raw.strip() else {}
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")[:400]
        logger.error("Paystack %s %s failed: HTTP %s %s", method, path, exc.code, detail)
        raise PaystackError(
            "Paystack rejected that request. Please try again.", status_code=exc.code
        ) from exc
    except Exception as exc:  # network, DNS, timeout, bad JSON
        logger.error("Paystack %s %s failed: %s", method, path, exc)
        raise PaystackError("Could not reach Paystack. Please try again.") from exc


def initialize_transaction(*, email, amount, reference, callback_url, metadata=None):
    """Start a transaction and return where to send the shopper."""
    body = {
        "email": email,
        "amount": amount_in_kobo(amount),
        "currency": settings.PAYSTACK_CURRENCY,
        "reference": reference,
        "callback_url": callback_url,
    }
    if metadata:
        body["metadata"] = metadata

    response = _request("POST", "/transaction/initialize", body)
    if not response.get("status"):
        raise PaystackError(response.get("message") or "Paystack could not start the payment.")

    data = response.get("data") or {}
    return {
        "authorization_url": data.get("authorization_url", ""),
        "access_code": data.get("access_code", ""),
        "reference": data.get("reference", reference),
    }


def verify_transaction(reference):
    """Fetch the authoritative record of a transaction from Paystack."""
    quoted = urllib.parse.quote(str(reference), safe="")
    response = _request("GET", f"/transaction/verify/{quoted}")
    if not response.get("status"):
        raise PaystackError(response.get("message") or "Paystack could not verify that payment.")
    return response.get("data") or {}


def signature_is_valid(raw_body, signature):
    """Constant-time check of the ``x-paystack-signature`` header.

    The webhook is a public URL, so its payload is only trusted when it carries
    an HMAC-SHA512 of the raw body made with our secret key.
    """
    if not signature or not is_configured():
        return False

    expected = hmac.new(
        settings.PAYSTACK_SECRET_KEY.encode("utf-8"), raw_body, hashlib.sha512
    ).hexdigest()
    return hmac.compare_digest(expected, signature.strip())
