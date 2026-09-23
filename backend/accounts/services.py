"""Outbound email via the EmailJS HTTP API.

PythonAnywhere's free plan blocks outbound SMTP, so `smtplib`/`send_mail` cannot
reach the internet there. EmailJS exposes an HTTPS endpoint instead, which works
on every plan.

Server-side sending requires the **private** key (`accessToken`). The browser SDK
would need that key in client JavaScript, where anyone could read it and send mail
as us - so all sending happens here, behind the API.

If the keys are not configured, `send_template` logs the message and returns
False instead of raising. That keeps local development and the test suite working
before EmailJS is set up, without ever silently dropping mail in production
(where the missing-key case is logged as an error).
"""

import json
import logging
import urllib.error
import urllib.request

from django.conf import settings

logger = logging.getLogger(__name__)

EMAILJS_ENDPOINT = "https://api.emailjs.com/api/v1.0/email/send"


def is_configured():
    """True when every value needed for a server-side send is present."""
    return bool(
        settings.EMAILJS_SERVICE_ID
        and settings.EMAILJS_PUBLIC_KEY
        and settings.EMAILJS_PRIVATE_KEY
    )


def send_template(template_id, params, *, to_email="", kind="email"):
    """Send one EmailJS template. Returns True on success, False otherwise.

    Never raises: a mail outage must not roll back a registration or an order.
    Failures are logged with enough context to debug from the web-app error log.
    """
    if not template_id:
        logger.error("EmailJS: no template id configured for %s (to=%s)", kind, to_email)
        return False

    if not is_configured():
        # Local development: print instead of send so sign-up can be tested.
        if settings.DEBUG:
            logger.warning(
                "EmailJS not configured - would have sent %s to %s with %s",
                kind,
                to_email,
                json.dumps(params, default=str),
            )
        else:
            logger.error(
                "EmailJS is not configured; %s to %s was NOT sent. "
                "Set EMAILJS_SERVICE_ID / EMAILJS_PUBLIC_KEY / EMAILJS_PRIVATE_KEY.",
                kind,
                to_email,
            )
        return False

    payload = json.dumps(
        {
            "service_id": settings.EMAILJS_SERVICE_ID,
            "template_id": template_id,
            "user_id": settings.EMAILJS_PUBLIC_KEY,
            "accessToken": settings.EMAILJS_PRIVATE_KEY,
            "template_params": params,
        }
    ).encode("utf-8")

    request = urllib.request.Request(
        EMAILJS_ENDPOINT,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=settings.EMAILJS_TIMEOUT) as response:
            body = response.read().decode("utf-8", "replace").strip()
            if response.status == 200:
                return True
            logger.error("EmailJS %s send failed: HTTP %s %s", kind, response.status, body)
            return False
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")[:400]
        logger.error("EmailJS %s send failed: HTTP %s %s", kind, exc.code, detail)
        return False
    except Exception as exc:  # network/timeout/DNS - never fatal
        logger.error("EmailJS %s send failed: %s", kind, exc)
        return False


# --------------------------------------------------------------------------- #
#  Message builders                                                            #
# --------------------------------------------------------------------------- #
# Template params are matched by name in the EmailJS template, e.g. {{code}}.
# Keep these names stable or the emails will render blank variables.
def send_verification_code(user, code):
    """Send the 6-digit sign-up code."""
    name = user.first_name or user.username
    return send_template(
        settings.EMAILJS_TEMPLATE_VERIFY,
        {
            "to_email": user.email,
            "to_name": name,
            "code": code,
            "expiry_minutes": settings.VERIFICATION_CODE_TTL_MINUTES,
            "site_url": settings.SITE_URL,
        },
        to_email=user.email,
        kind="signup verification",
    )


def send_password_reset_code(user, code):
    """Send the 6-digit password-reset code."""
    name = user.first_name or user.username
    return send_template(
        settings.EMAILJS_TEMPLATE_RESET or settings.EMAILJS_TEMPLATE_VERIFY,
        {
            "to_email": user.email,
            "to_name": name,
            "code": code,
            "expiry_minutes": settings.VERIFICATION_CODE_TTL_MINUTES,
            "site_url": settings.SITE_URL,
        },
        to_email=user.email,
        kind="password reset",
    )


def send_order_confirmation(order):
    """Email the customer after a payment is confirmed."""
    if not order.email:
        return False
    return send_template(
        settings.EMAILJS_TEMPLATE_ORDER,
        {
            "to_email": order.email,
            "to_name": order.full_name,
            "order_id": str(order.id),
            "reference": order.payment_reference or "",
            "total": str(order.total),
            "status": order.get_status_display(),
            "site_url": settings.SITE_URL,
            "items": ", ".join(
                f"{item.quantity} x {item.product_name}" for item in order.items.all()
            ),
        },
        to_email=order.email,
        kind="order confirmation",
    )
