"""Outbound transactional email via the Resend HTTPS API.

PythonAnywhere's free plan blocks outbound SMTP, so `smtplib`/`send_mail`
cannot reach the internet there. Resend exposes an HTTPS endpoint instead
(`api.resend.com`), which is on their free-tier allowlist, so the same code
works locally and on the free deployment.

Server-side sending needs the Resend **API key** (`Authorization: Bearer`).
The browser SDK would require that key in client JavaScript, where anyone
could read it and send mail as us - so all sending happens here, behind the
API. That is also why the verification codes are generated in Django and
never handed to the front end: a code that reaches the browser can be used
to verify an address the requester does not own.

Messages are built as inline-styled HTML in this module. Resend takes raw
HTML rather than a hosted template, so the markup lives next to the code
that fills it in - one file to change when the design moves.

If the API key is not configured, `send_email` logs the message and returns
False instead of raising. That keeps local development and the test suite
working before Resend is set up, without ever silently dropping mail in
production (where the missing-key case is logged as an error).
"""

import json
import logging
import urllib.error
import urllib.parse
import urllib.request

from django.conf import settings

logger = logging.getLogger(__name__)

RESEND_ENDPOINT = "https://api.resend.com/emails"

# Brand palette, kept in step with app/globals.css.
_BRAND = {
    "green": "#3d6244",
    "cream": "#fbf8f2",
    "border": "#d5e2d7",
    "gold": "#f3c56a",
    "ink": "#1c2b1e",
    "body": "#4a5a4c",
    "orange": "#e67e22",
}

# Resend's free plan allows 1 request/second. Every send in this project is a
# single request already, but callers that loop (order confirmations in a
# backfill) are expected to throttle themselves.


def is_configured():
    """True when the Resend API key is present."""
    return bool(settings.RESEND_API_KEY)


def send_email(*, to_email, subject, html, kind="email", text=""):
    """Send one HTML message through Resend. Returns True on success.

    Never raises: a mail outage must not roll back a registration or an order.
    Failures are logged with enough context to debug from the web-app error log.
    """
    if not to_email:
        logger.error("Resend: no recipient for %s", kind)
        return False

    if not is_configured():
        # Local development: log instead of send so sign-up can be tested.
        if settings.DEBUG:
            logger.warning(
                "Resend not configured - would have sent %r to %s (link: %s)",
                subject,
                to_email,
                kind,
            )
        else:
            logger.error(
                "Resend is not configured; %s to %s was NOT sent. "
                "Set RESEND_API_KEY in backend/.env.",
                kind,
                to_email,
            )
        return False

    payload = json.dumps(
        {
            "from": settings.RESEND_FROM_EMAIL,
            "to": [to_email],
            "subject": subject,
            "html": html,
            "text": text or "",
            "reply_to": settings.RESEND_REPLY_TO,
        }
    ).encode("utf-8")

    request = urllib.request.Request(
        RESEND_ENDPOINT,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {settings.RESEND_API_KEY}",
            # Cloudflare (which fronts api.resend.com) rejects requests with no
            # User-Agent as suspected automation, answering 403 with body
            # "error code: 1010" - the same error EmailJS gave us, for the same
            # reason. urllib sends a bare "Python-urllib/3.x" by default, which
            # trips that rule. Identifying the application is both accurate and
            # sufficient; a browser spoof is not needed.
            "User-Agent": "JakealaNaturals/1.0 (+https://jakeala.com)",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=settings.RESEND_TIMEOUT) as response:
            body = response.read().decode("utf-8", "replace").strip()
            if 200 <= response.status < 300:
                logger.info("Resend %s sent to %s", kind, to_email)
                return True
            logger.error("Resend %s send failed: HTTP %s %s", kind, response.status, body)
            return False
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")[:400]
        logger.error("Resend %s send failed: HTTP %s %s", kind, exc.code, detail)
        return False
    except Exception as exc:  # network/timeout/DNS - never fatal
        logger.error("Resend %s send failed: %s", kind, exc)
        return False


# --------------------------------------------------------------------------- #
#  HTML shell                                                                 #
# --------------------------------------------------------------------------- #
def _shell(title, intro, cta_label, action_url, footnote, tint=None):
    """Wrap body content in the Jakeala Naturals email chrome.

    Every style is inline and the layout is a single column: Gmail and Outlook
    strip `<style>` blocks and mangle floats and tables, so inline styles on
    simple block elements are the only reliable combination. No logo image -
    most inboxes block remote images by default, and a broken box looks worse
    than the coloured header doing the branding on its own.
    """
    c = _BRAND
    button_bg = tint or c["orange"]
    return f"""<div style="margin:0;padding:0;background:{c['cream']};font-family:Arial,Helvetica,sans-serif;">
  <div style="max-width:560px;margin:0 auto;padding:32px 18px;">
    <div style="background:#ffffff;border:1px solid {c['border']};border-radius:16px;overflow:hidden;">
      <div style="background:{c['green']};padding:28px 30px;text-align:center;">
        <p style="margin:0;color:{c['gold']};font-size:12px;letter-spacing:2px;text-transform:uppercase;">Where every skin is our priority</p>
        <h1 style="margin:8px 0 0;color:#ffffff;font-size:25px;">Jakeala Naturals</h1>
      </div>
      <div style="padding:30px;">
        <p style="margin:0 0 12px;color:{c['ink']};font-size:16px;">{intro}</p>
        <p style="margin:0 0 24px;color:{c['body']};font-size:15px;line-height:1.6;">{title}</p>
        <div style="text-align:center;margin:28px 0;">
          <a href="{action_url}" style="display:inline-block;background:{button_bg};color:#ffffff;text-decoration:none;padding:15px 32px;border-radius:10px;font-size:16px;font-weight:bold;">{cta_label}</a>
        </div>
        <p style="margin:0 0 8px;color:{c['body']};font-size:14px;line-height:1.6;text-align:center;">This secure link can be used once and expires shortly.</p>
        <p style="margin:20px 0 0;color:{c['body']};font-size:13px;line-height:1.6;">{footnote}</p>
      </div>
      <div style="background:#f4f8f4;padding:20px 32px;text-align:center;border-top:1px solid {c['border']};">
        <p style="margin:0;color:{c['body']};font-size:13px;">With care,<br><strong style="color:{c['green']};">Jakeala Naturals</strong></p>
        <p style="margin:8px 0 0;font-size:12px;"><a href="{settings.SITE_URL}" style="color:{c['orange']};text-decoration:none;">{settings.SITE_URL}</a></p>
      </div>
    </div>
  </div>
</div>"""

# The browser opens ``action_url``; the code remains hashed, expiring and
# single-use on the server, so it is never a password and never reusable.
def account_action_url(user, code, purpose):
    """Build a frontend link carrying the email and one-time code safely."""
    query = urllib.parse.urlencode(
        {"email": user.email, "code": code, "purpose": purpose}
    )
    return f"{settings.SITE_URL.rstrip('/')}/account?{query}"


def _greet(user):
    return f"Hi {user.first_name or user.username},"


def send_verification_code(user, code):
    """Email the secure sign-up verification link."""
    url = account_action_url(user, code, "verify")
    return send_email(
        to_email=user.email,
        subject="Verify your Jakeala Naturals email address",
        html=_shell(
            title=(
                "Thank you for creating your Jakeala Naturals account. "
                "Please confirm your email address to activate your account."
            ),
            intro=_greet(user),
            cta_label="Verify My Email",
            action_url=url,
            footnote="If you didn't create an account with us, you can safely ignore this email.",
            tint=_BRAND["orange"],
        ),
        text=(
            f"{_greet(user)}\n\nThank you for creating your Jakeala Naturals account. "
            "Please confirm your email address to activate your account:\n\n"
            f"{url}\n\n"
            "This secure link can be used once and expires shortly.\n\n"
            "If you didn't create an account with us, you can safely ignore this email."
        ),
        kind="signup verification",
    )


def send_password_reset_code(user, code):
    """Email the secure password-reset link."""
    url = account_action_url(user, code, "reset")
    return send_email(
        to_email=user.email,
        subject="Reset your Jakeala Naturals password",
        html=_shell(
            title=(
                "We received a request to reset your Jakeala Naturals password. "
                "Click the button below to choose a new password."
            ),
            intro=_greet(user),
            cta_label="Reset My Password",
            action_url=url,
            footnote=(
                "If you didn't request a password reset, you can safely ignore this "
                "email. Your current password will remain unchanged."
            ),
            tint=_BRAND["green"],
        ),
        text=(
            f"{_greet(user)}\n\nWe received a request to reset your Jakeala Naturals "
            f"password. Choose a new password here:\n\n{url}\n\n"
            "This secure link can be used once and expires shortly.\n\n"
            "If you didn't request a password reset, you can safely ignore this email. "
            "Your current password will remain unchanged."
        ),
        kind="password reset",
    )


def send_order_confirmation(order):
    """Email the customer after a payment is confirmed."""
    if not order.email:
        return False

    items = ", ".join(
        f"{item.quantity} x {item.product_name}" for item in order.items.all()
    )
    track_url = (
        f"{settings.SITE_URL.rstrip('/')}/account?email="
        f"{urllib.parse.quote(order.email)}"
    )
    c = _BRAND
    summary_rows = (
        f"<p style=\"margin:0 0 6px;color:{c['body']};font-size:14px;line-height:1.6;\">"
        f"<strong style=\"color:{c['ink']};\">Reference:</strong> {order.payment_reference or order.id}</p>"
        f"<p style=\"margin:0 0 6px;color:{c['body']};font-size:14px;line-height:1.6;\">"
        f"<strong style=\"color:{c['ink']};\">Items:</strong> {items}</p>"
        f"<p style=\"margin:0 0 6px;color:{c['body']};font-size:14px;line-height:1.6;\">"
        f"<strong style=\"color:{c['ink']};\">Status:</strong> {order.get_status_display()}</p>"
        f"<p style=\"margin:0;color:{c['ink']};font-size:16px;font-weight:bold;\">Total: {order.total}</p>"
    )
    return send_email(
        to_email=order.email,
        subject=(
            f"Your Jakeala Naturals order {order.payment_reference or order.id} is confirmed"
        ),
        html=f"""<div style="margin:0;padding:0;background:{c['cream']};font-family:Arial,Helvetica,sans-serif;">
  <div style="max-width:560px;margin:0 auto;padding:32px 18px;">
    <div style="background:#ffffff;border:1px solid {c['border']};border-radius:16px;overflow:hidden;">
      <div style="background:{c['green']};padding:28px 30px;text-align:center;">
        <p style="margin:0;color:{c['gold']};font-size:12px;letter-spacing:2px;text-transform:uppercase;">Where every skin is our priority</p>
        <h1 style="margin:8px 0 0;color:#ffffff;font-size:25px;">Jakeala Naturals</h1>
      </div>
      <div style="padding:30px;">
        <p style="margin:0 0 12px;color:{c['ink']};font-size:16px;">Hi {order.full_name or 'there'},</p>
        <p style="margin:0 0 22px;color:{c['body']};font-size:15px;line-height:1.6;">Thank you for shopping with us. Your order is confirmed and we are preparing it now.</p>
        <div style="background:#f4f8f4;border:1px solid {c['border']};border-radius:12px;padding:18px 20px;margin:0 0 22px;">
          <p style="margin:0 0 10px;color:{c['ink']};font-size:15px;font-weight:bold;">Order summary</p>
          {summary_rows}
        </div>
        <div style="text-align:center;margin:26px 0;">
          <a href="{track_url}" style="display:inline-block;background:{c['green']};color:#ffffff;text-decoration:none;padding:15px 32px;border-radius:10px;font-size:16px;font-weight:bold;">Track my order</a>
        </div>
        <p style="margin:0;color:{c['body']};font-size:13px;line-height:1.6;">We will contact you about delivery shortly. Questions? Just reply to this email.</p>
      </div>
      <div style="background:#f4f8f4;padding:20px 32px;text-align:center;border-top:1px solid {c['border']};">
        <p style="margin:0;color:{c['body']};font-size:13px;">With care,<br><strong style="color:{c['green']};">Jakeala Naturals</strong></p>
        <p style="margin:8px 0 0;font-size:12px;"><a href="{settings.SITE_URL}" style="color:{c['orange']};text-decoration:none;">{settings.SITE_URL}</a></p>
      </div>
    </div>
  </div>
</div>""",
        text=(
            f"Hi {order.full_name or 'there'},\n\n"
            "Thank you for shopping with Jakeala Naturals. Your order is confirmed.\n\n"
            f"Reference: {order.payment_reference or order.id}\n"
            f"Items: {items}\n"
            f"Status: {order.get_status_display()}\n"
            f"Total: {order.total}\n\n"
            f"Track your order: {track_url}\n\n"
            "We will contact you about delivery shortly."
        ),
        kind="order confirmation",
    )
