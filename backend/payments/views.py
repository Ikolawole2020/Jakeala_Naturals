"""Payment endpoints: config, initialise, verify and the Paystack webhook.

The browser never sees the secret key. It receives only the **public** key from
``/api/payments/config/``, and every state change is decided server-side:

    checkout -> Order(status="pending")  +  POST /api/payments/initialize/
    shopper pays on Paystack
    Paystack redirects to /payment/verify  ->  POST /api/payments/verify/
    Paystack also calls  POST /api/payments/webhook/   (authoritative backup)

``initialize`` and ``verify`` are deliberately reachable by guests: the order
carries an unguessable ``public_token`` (and the Paystack reference is random),
and either that token or an authenticated owner is required to touch an order.
"""

import json
import logging

from django.conf import settings
from rest_framework import status
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
    throttle_classes,
)
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from commerce.models import Order
from commerce.serializers import OrderPublicSerializer
from config.throttles import CheckoutThrottle

from . import paystack
from .paystack import PaystackError
from .services import SettlementError, make_reference, settle_order

logger = logging.getLogger(__name__)


def accessible_order(request, *, order_id=None, token=None, reference=None):
    """Fetch an order the caller may act on, or ``None``.

    Access is granted by the order's unguessable ``public_token`` (so a guest who
    just checked out can pay and confirm) or by being the signed-in owner. A bare
    order id grants nothing, which is what stops order-enumeration leaks.
    """
    try:
        if reference:
            return Order.objects.filter(payment_reference=reference).first()
        if order_id in (None, ""):
            return None
        order = Order.objects.get(pk=int(order_id))
    except (Order.DoesNotExist, TypeError, ValueError):
        return None

    token = (token or "").strip()
    if token and str(order.public_token) == token:
        return order

    user = getattr(request, "user", None)
    if user is not None and user.is_authenticated and order.user_id == user.pk:
        return order
    return None


@api_view(["GET"])
@permission_classes([AllowAny])
def payments_config(request):
    """Public payment settings the front end needs to open Paystack."""
    return Response(
        {
            "provider": "paystack",
            "enabled": paystack.is_configured() and bool(settings.PAYSTACK_PUBLIC_KEY),
            "public_key": settings.PAYSTACK_PUBLIC_KEY,
            "currency": settings.PAYSTACK_CURRENCY,
            "free_shipping_threshold": str(settings.FREE_SHIPPING_THRESHOLD),
            "flat_shipping_fee": str(settings.FLAT_SHIPPING_FEE),
        }
    )


@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([CheckoutThrottle])
def initialize_payment(request):
    """Create a Paystack transaction for a pending order and return its URL."""
    order = accessible_order(
        request,
        order_id=request.data.get("order_id"),
        token=request.data.get("token"),
    )
    if order is None:
        return Response({"detail": "Order not found."}, status=status.HTTP_404_NOT_FOUND)

    if order.status != Order.PENDING:
        return Response(
            {"detail": f"This order is already {order.get_status_display().lower()}."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if not paystack.is_configured():
        return Response(
            {
                "detail": (
                    "Payments are not configured yet. Add PAYSTACK_SECRET_KEY and "
                    "PAYSTACK_PUBLIC_KEY to the backend environment."
                )
            },
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    # A fresh reference per attempt: an old one can never be replayed onto
    # another order, and Paystack rejects duplicate references.
    order.payment_reference = make_reference(order)
    order.payment_provider = "paystack"
    order.save(update_fields=["payment_reference", "payment_provider"])

    try:
        result = paystack.initialize_transaction(
            email=order.email,
            amount=order.total,
            reference=order.payment_reference,
            callback_url=settings.PAYSTACK_CALLBACK_URL,
            metadata={"order_id": order.pk, "full_name": order.full_name},
        )
    except PaystackError as exc:
        return Response({"detail": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)

    return Response(
        {
            "order_id": order.pk,
            "reference": result["reference"],
            "authorization_url": result["authorization_url"],
            "access_code": result["access_code"],
            "amount_kobo": paystack.amount_in_kobo(order.total),
        }
    )


@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([CheckoutThrottle])
def verify_payment(request):
    """Confirm a payment with Paystack and settle the order.

    This is the call the shopper's browser makes when Paystack sends them back.
    It is idempotent: repeat calls return the current state instead of
    re-performing the transition, and the amount is re-checked against the total.
    """
    reference = str(request.data.get("reference") or "").strip()
    if not reference:
        return Response(
            {"detail": "A payment reference is required."}, status=status.HTTP_400_BAD_REQUEST
        )

    order = accessible_order(
        request,
        reference=reference,
        order_id=request.data.get("order_id"),
        token=request.data.get("token"),
    )
    if order is None:
        return Response(
            {"detail": "We could not find an order for that payment reference."},
            status=status.HTTP_404_NOT_FOUND,
        )

    if order.status != Order.PENDING:
        # Already settled - the webhook beat us here, or this is a repeat visit.
        return Response(
            {"order": OrderPublicSerializer(order).data, "settled": True, "already_paid": True}
        )

    try:
        data = paystack.verify_transaction(reference)
    except PaystackError as exc:
        return Response(
            {"detail": str(exc), "order": OrderPublicSerializer(order).data},
            status=status.HTTP_502_BAD_GATEWAY,
        )

    if str(data.get("status", "")).lower() != "success":
        return Response(
            {
                "detail": "That payment was not completed.",
                "payment_status": data.get("status", "unknown"),
                "order": OrderPublicSerializer(order).data,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        settled = settle_order(
            order,
            reference=str(data.get("reference") or reference),
            amount_kobo=data.get("amount"),
            currency=data.get("currency") or "",
            source="callback",
        )
    except SettlementError as exc:
        logger.error("Refusing payment for order %s: %s", order.pk, exc)
        return Response({"detail": str(exc)}, status=status.HTTP_409_CONFLICT)

    order.refresh_from_db()
    return Response(
        {
            "settled": settled,
            "order": OrderPublicSerializer(order).data,
            "payment_status": data.get("status"),
        }
    )


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@throttle_classes([])
def paystack_webhook(request):
    """Authoritative payment notification from Paystack.

    Public by necessity, so the payload is trusted **only** when the
    ``x-paystack-signature`` HMAC matches. Paystack retries non-2xx responses, so
    anything we have handled still answers 200 to stop the retries.
    """
    raw_body = request.body or b""
    signature = request.headers.get("x-paystack-signature")

    if not paystack.signature_is_valid(raw_body, signature):
        logger.warning("Rejected Paystack webhook with an invalid signature.")
        return Response({"detail": "Invalid signature."}, status=status.HTTP_401_UNAUTHORIZED)

    try:
        payload = json.loads(raw_body.decode("utf-8") or "{}")
    except (ValueError, UnicodeDecodeError):
        return Response({"detail": "Malformed payload."}, status=status.HTTP_400_BAD_REQUEST)

    event = payload.get("event", "")
    data = payload.get("data") or {}
    reference = str(data.get("reference") or "").strip()

    if event != "charge.success" or not reference:
        # Acknowledge everything we do not act on so it is not retried.
        return Response({"ok": True, "ignored": event})

    order = Order.objects.filter(payment_reference=reference).first()
    if order is None:
        logger.warning("Paystack webhook for unknown reference %s", reference)
        return Response({"ok": True, "ignored": "unknown reference"})

    try:
        settle_order(
            order,
            reference=reference,
            amount_kobo=data.get("amount"),
            currency=data.get("currency") or "",
            source="webhook",
        )
    except SettlementError as exc:
        logger.error("Webhook refused for order %s: %s", order.pk, exc)
        return Response({"ok": True, "ignored": "amount mismatch"})

    return Response({"ok": True})

