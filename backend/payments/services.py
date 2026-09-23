"""Turning a verified Paystack payment into an order state change.

Both entry points - the browser callback (``/api/payments/verify/``) and the
webhook (``/api/payments/webhook/``) - go through ``settle_order``, so an order
can only ever be marked paid **once**, only from ``pending``, and only when the
amount Paystack reports matches what the order was created for.

The transition is guarded by a conditional ``UPDATE ... WHERE status='pending'``
rather than ``select_for_update()``: SQLite (what PythonAnywhere uses) does not
support row locking, and the conditional update is atomic on every backend - if
two notifications race, exactly one of them sees ``rowcount == 1``.
"""

import logging
import secrets

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from accounts.services import send_order_confirmation
from commerce.models import CartItem, Order

from .paystack import amount_in_kobo

logger = logging.getLogger(__name__)


class SettlementError(Exception):
    """The payment does not match the order and must not be accepted."""


def make_reference(order):
    """Build an unguessable, unique Paystack reference for an order.

    Paystack echoes this back on the callback and in the webhook, which is how a
    notification is matched to an order. It must therefore be hard to guess: the
    random suffix means knowing an order id is not enough.
    """
    return f"JN{order.pk}T{secrets.token_hex(4).upper()}"


def reduce_stock(order):
    """Decrement tracked stock for each paid line item.

    ``stock_quantity`` of ``None`` means "not tracked" (a service or a made-to-
    order item), which is left alone. A product that reaches zero is marked out
    of stock so the storefront stops offering it.
    """
    for item in order.items.select_related("product"):
        product = item.product
        if product is None or product.stock_quantity is None:
            continue

        product.stock_quantity = max(0, product.stock_quantity - item.quantity)
        fields = ["stock_quantity"]
        if product.stock_quantity == 0 and product.in_stock:
            product.in_stock = False
            fields.append("in_stock")
        product.save(update_fields=fields)


@transaction.atomic
def settle_order(order, *, reference, amount_kobo=None, currency="", source="callback"):
    """Mark ``order`` as paid, exactly once, after checking the amount.

    Returns ``True`` when this call performed the transition and ``False`` when
    the order was already settled (a duplicate webhook, or a callback for a
    payment already confirmed).

    Raises ``SettlementError`` when the payment must not be accepted, which keeps
    a tampered callback from marking an order paid.
    """
    if order.payment_reference and reference and order.payment_reference != reference:
        raise SettlementError(
            f"Reference {reference} does not belong to order {order.pk}."
        )

    if currency and currency.upper() != settings.PAYSTACK_CURRENCY.upper():
        raise SettlementError(
            f"Payment was made in {currency}, not {settings.PAYSTACK_CURRENCY}."
        )

    if order.total > 0 and amount_kobo is not None:
        expected = amount_in_kobo(order.total)
        if int(amount_kobo) < expected:
            raise SettlementError(
                f"Order {order.pk} costs {expected} kobo but only {amount_kobo} was paid."
            )

    settled_at = timezone.now()
    updated = Order.objects.filter(pk=order.pk, status=Order.PENDING).update(
        status=Order.PAID,
        paid_at=settled_at,
        payment_provider="paystack",
        payment_reference=reference or order.payment_reference,
    )

    if not updated:
        logger.info("Order %s was already settled; ignoring duplicate notification.", order.pk)
        return False

    order.refresh_from_db()

    if not order.stock_reduced:
        reduce_stock(order)
        order.stock_reduced = True
        order.save(update_fields=["stock_reduced"])

    empty_basket(order)

    logger.info("Order %s paid via Paystack (%s).", order.pk, source)
    send_order_confirmation(order)
    return True


def empty_basket(order):
    """Empty the basket the order came from.

    Done here rather than at checkout so an abandoned or failed Paystack attempt
    leaves the shopper's basket intact.
    """
    if not order.cart_key:
        return
    CartItem.objects.filter(cart__session_key=order.cart_key).delete()

