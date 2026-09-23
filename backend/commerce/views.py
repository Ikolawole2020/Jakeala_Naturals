"""Cart, checkout and order endpoints.

This module holds the fixes for the most serious problems the store had:

=========================  =======================================================
Old behaviour              Now
=========================  =======================================================
A missing cart key fell    A key must be 16-64 URL-safe characters. Anything else
back to ``"guest"``, so     is replaced with a fresh server-generated token, which
every anonymous visitor     is returned in the cart payload for the browser to
shared one basket.          store. Two shoppers can never share a basket.
Any visitor could read or   Keys are unguessable, and once signed in the key is
edit another cart by        derived from the account (``user:<id>``) so it cannot
passing ``session=``.       be chosen at all.
``?email=``/``?status=``    ``/api/orders/`` requires a token and only ever
on ``/api/orders/`` gave    returns the caller's own orders. A guest reads a
out every customer's        single order with its unguessable ``public_token``.
name, phone and address.
Checkout marked orders      Checkout creates a ``pending`` order; only a verified
``paid`` without taking     Paystack payment (callback or signed webhook) can move
any money.                  it to ``paid``, and the amount is re-checked first.
No stock check, and         Untracked items are always sellable; tracked items are
``qty=-999`` accepted.      validated at checkout, and quantity is capped.
=========================  =======================================================
"""

import logging
import re
import secrets
from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from catalog.models import Product
from config.throttles import CheckoutThrottle

from .models import Cart, CartItem, Order, OrderItem
from .serializers import (
    CartSerializer,
    CheckoutSerializer,
    OrderPublicSerializer,
    OrderSerializer,
    line_price,
)

logger = logging.getLogger(__name__)

User = get_user_model()

# A cart token must look like something we issued: URL-safe and long enough that
# guessing one is not feasible. Anything shorter or malformed is rejected.
CART_KEY_RE = re.compile(r"^[A-Za-z0-9_-]{16,64}$")
CART_KEY_PREFIX = "g_"

# How long a pending order may be reused instead of creating a duplicate when a
# shopper presses "place order" twice.
PENDING_REUSE_MINUTES = 60


def new_cart_key():
    """A fresh, unguessable guest basket token."""
    return CART_KEY_PREFIX + secrets.token_urlsafe(24)


def resolve_cart_key(request, candidate=""):
    """Return ``(key, generated)`` for this request.

    Signed-in shoppers are keyed by account, so their basket follows them between
    devices and cannot be addressed with a made-up string. Guests must supply a
    well-formed token; if they cannot, we mint one and hand it back.
    """
    user = getattr(request, "user", None)
    if user is not None and user.is_authenticated:
        return f"user:{user.pk}", False

    candidate = (candidate or "").strip()
    if CART_KEY_RE.match(candidate):
        return candidate, False
    return new_cart_key(), True


def get_cart(key):
    """Fetch or create a basket, tolerating any legacy duplicate rows."""
    cart = Cart.objects.filter(session_key=key).order_by("id").first()
    if cart is None:
        cart = Cart.objects.create(session_key=key)
    return cart


def shipping_for(subtotal):
    """Delivery charge for a subtotal, from settings."""
    threshold = Decimal(str(settings.FREE_SHIPPING_THRESHOLD))
    flat = Decimal(str(settings.FLAT_SHIPPING_FEE))
    return Decimal("0") if subtotal >= threshold else flat



class CartViewSet(viewsets.ViewSet):
    """A guest cart must work without signing in, so access is explicitly open.

    The project default is ``IsAuthenticatedOrReadOnly``; without this override
    POSTs (add / update / clear) would demand a token.
    """

    permission_classes = [AllowAny]

    def list(self, request):
        key, _ = resolve_cart_key(request, request.query_params.get("session"))
        return Response(CartSerializer(get_cart(key)).data)

    @action(detail=False, methods=["post"])
    def add(self, request):
        """Add a product, clamping quantity to something sane."""
        product = get_object_or_404(Product, pk=request.data.get("product_id"))

        if not product.in_stock:
            return Response(
                {"detail": f"{product.name} is currently out of stock."},
                status=status.HTTP_409_CONFLICT,
            )

        try:
            qty = int(request.data.get("quantity", 1))
        except (TypeError, ValueError):
            return Response(
                {"detail": "Quantity must be a whole number."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        limit = int(settings.CART_MAX_QUANTITY)
        if qty < 1:
            # A negative or zero quantity is nonsense input, not a request to add
            # one. Removing a line is what the update endpoint is for.
            return Response(
                {"detail": "Quantity must be at least 1."}, status=status.HTTP_400_BAD_REQUEST
            )
        if qty > limit:
            return Response(
                {"detail": f"You can order at most {limit} of one item."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        subscribe = bool(request.data.get("subscribe", False))
        key, _ = resolve_cart_key(request, request.data.get("session"))

        with transaction.atomic():
            cart = get_cart(key)
            item, created = CartItem.objects.get_or_create(
                cart=cart, product=product, subscribe=subscribe, defaults={"quantity": qty}
            )
            if not created:
                item.quantity = min(limit, item.quantity + qty)
                item.save(update_fields=["quantity"])

        return Response(CartSerializer(cart).data)

    @action(detail=False, methods=["post"])
    def update_item(self, request):
        """Set a line's quantity. Zero or less removes it."""
        try:
            qty = int(request.data.get("quantity", 1))
        except (TypeError, ValueError):
            return Response(
                {"detail": "Quantity must be a whole number."}, status=status.HTTP_400_BAD_REQUEST
            )

        limit = int(settings.CART_MAX_QUANTITY)
        if qty > limit:
            return Response(
                {"detail": f"You can order at most {limit} of one item."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        key, _ = resolve_cart_key(request, request.data.get("session"))
        # Scoped to this key, so an item id from someone else's basket cannot be
        # touched - and a missing item is a 404 rather than a 500.
        item = get_object_or_404(CartItem, pk=request.data.get("item_id"), cart__session_key=key)

        if qty <= 0:
            item.delete()
        else:
            item.quantity = qty
            item.save(update_fields=["quantity"])

        return Response(CartSerializer(get_cart(key)).data)

    @action(detail=False, methods=["post"])
    def clear(self, request):
        key, _ = resolve_cart_key(request, request.data.get("session"))
        CartItem.objects.filter(cart__session_key=key).delete()
        return Response(CartSerializer(get_cart(key)).data)

    @action(detail=False, methods=["post"])
    def merge(self, request):
        """Fold a guest basket into the signed-in account's basket.

        Called by the front end right after a shopper signs in, so the shopping
        they did as a guest is not lost.
        """
        if not request.user.is_authenticated:
            return Response({"detail": "Sign in first."}, status=status.HTTP_401_UNAUTHORIZED)

        guest_key = (request.data.get("session") or "").strip()
        target, _ = resolve_cart_key(request, "")
        cart = get_cart(target)

        if not guest_key or guest_key == target or not CART_KEY_RE.match(guest_key):
            return Response(CartSerializer(cart).data)

        source = Cart.objects.filter(session_key=guest_key).order_by("id").first()
        if source is None:
            return Response(CartSerializer(cart).data)

        limit = int(settings.CART_MAX_QUANTITY)
        with transaction.atomic():
            for item in source.items.select_related("product"):
                existing = CartItem.objects.filter(
                    cart=cart, product=item.product, subscribe=item.subscribe
                ).first()
                if existing is None:
                    CartItem.objects.create(
                        cart=cart,
                        product=item.product,
                        quantity=min(limit, item.quantity),
                        subscribe=item.subscribe,
                    )
                else:
                    existing.quantity = min(limit, existing.quantity + item.quantity)
                    existing.save(update_fields=["quantity"])
            source.delete()

        return Response(CartSerializer(cart).data)



def reuse_or_create_order(data, cart_key, user, subtotal, shipping, total, items):
    """Create - or refresh - the pending order for this basket.

    Pressing "place order" twice must not leave two pending orders behind, so a
    recent pending order with the same email and total is reused and its lines are
    rewritten from the current basket. The basket itself is left alone and only
    emptied once payment succeeds.
    """
    cutoff = timezone.now() - timedelta(minutes=PENDING_REUSE_MINUTES)
    order = (
        Order.objects.filter(
            email=data["email"], status=Order.PENDING, total=total, created_at__gte=cutoff
        )
        .order_by("-id")
        .first()
    )
    if order is None:
        order = Order(email=data["email"], subtotal=subtotal, shipping=shipping, total=total)

    order.user = user or order.user
    order.full_name = data["full_name"]
    order.phone = data.get("phone", "") or ""
    order.address = data["address"]
    order.city = data["city"]
    order.state = data["state"]
    order.country = data.get("country") or "Nigeria"
    order.notes = data.get("notes", "") or ""
    order.cart_key = cart_key
    order.save()

    order.items.all().delete()
    for item in items:
        OrderItem.objects.create(
            order=order,
            product=item.product,
            product_name=item.product.name,
            sku=item.product.sku,
            quantity=item.quantity,
            unit_price=line_price(item),
            subscribe=item.subscribe,
        )
    return order


@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([CheckoutThrottle])
def checkout(request):
    """Create a pending order for the current basket.

    Prices, shipping and the total are all computed here from the catalogue, so a
    tampered request cannot choose its own price. The order starts ``pending``:
    only a verified Paystack payment may move it to ``paid``.
    """
    ser = CheckoutSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    data = ser.validated_data

    key, _ = resolve_cart_key(request, data.get("session_key"))
    cart = get_cart(key)
    items = list(cart.items.select_related("product"))
    if not items:
        return Response({"detail": "Your basket is empty."}, status=status.HTTP_409_CONFLICT)

    # Stock is checked against the live catalogue, not the cart's memory of it.
    problems = []
    for item in items:
        product = item.product
        if not product.in_stock:
            problems.append(f"{product.name} is out of stock.")
        elif product.stock_quantity is not None and product.stock_quantity < item.quantity:
            problems.append(f"Only {product.stock_quantity} x {product.name} left in stock.")
    if problems:
        return Response({"detail": " ".join(problems)}, status=status.HTTP_409_CONFLICT)

    subtotal = sum((line_price(item) * item.quantity for item in items), Decimal("0"))
    shipping = shipping_for(subtotal)
    total = subtotal + shipping

    # Link the order to an account when we can - the signed-in user, or whoever
    # owns the email address. Guests can still check out; they track by token.
    user = request.user if request.user.is_authenticated else None
    if user is None:
        user = User.objects.filter(email__iexact=data["email"]).first()

    with transaction.atomic():
        order = reuse_or_create_order(data, key, user, subtotal, shipping, total, items)

    logger.info("Order %s created (pending) for %s", order.pk, order.email)
    return Response(
        {
            "order": OrderPublicSerializer(order).data,
            "payment_required": order.total > 0,
        },
        status=status.HTTP_201_CREATED,
    )


class OrderViewSet(viewsets.ReadOnlyModelViewSet):
    """Order history, and single-order lookup by token.

    ``/api/orders/`` requires a token and is scoped to the caller, which closes
    the hole where ``?email=someone@else.com`` returned a stranger's full name,
    phone number and delivery address.

    ``/api/orders/<id>/`` also answers to the order's unguessable ``public_token``
    so a guest who has just paid can see their confirmation. The signed-in owner
    gets the full record; a token holder gets the reduced one; anybody else gets
    the same 404 they would get for an order that does not exist.
    """

    queryset = Order.objects.prefetch_related("items")

    def get_permissions(self):
        if self.action == "retrieve":
            return [AllowAny()]
        return [IsAuthenticated()]

    def list(self, request, *args, **kwargs):
        """Only ever the caller's own orders."""
        queryset = Order.objects.filter(user=request.user).prefetch_related("items")

        wanted = request.query_params.get("status")
        if wanted in dict(Order.STATUS):
            queryset = queryset.filter(status=wanted)

        page = self.paginate_queryset(queryset)
        if page is not None:
            return self.get_paginated_response(OrderSerializer(page, many=True).data)
        return Response(OrderSerializer(queryset, many=True).data)

    def retrieve(self, request, *args, **kwargs):
        order = get_object_or_404(Order.objects.prefetch_related("items"), pk=kwargs["pk"])

        is_owner = request.user.is_authenticated and order.user_id == request.user.pk
        token = (request.query_params.get("token") or "").strip()
        has_token = bool(token) and str(order.public_token) == token

        if not is_owner and not has_token:
            # Same answer as a genuinely missing order: no id enumeration.
            return Response({"detail": "Order not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = OrderSerializer if is_owner else OrderPublicSerializer
        return Response(serializer(order).data)

