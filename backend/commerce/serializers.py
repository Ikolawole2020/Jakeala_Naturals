"""Commerce serializers.

Two rules apply here:

* **No ``fields = "__all__"``.** Every serializer lists its fields explicitly, so
  adding a model field can never silently publish it through the public API. That
  is what turned the old order endpoint into a full PII dump.
* **Two order serializers, on purpose.** ``OrderSerializer`` is for the signed-in
  owner (address, notes, payment trail). ``OrderPublicSerializer`` is the reduced
  view a guest gets back from checkout and payment verification: enough to show a
  confirmation page, with the email masked and no address or payment internals.
"""

from decimal import Decimal

from rest_framework import serializers

from catalog.serializers import ProductListSerializer

from .models import Cart, CartItem, Order, OrderItem

SUBSCRIPTION_DISCOUNT = Decimal("0.90")


def line_price(item):
    """Unit price for a cart line, applying the subscription discount."""
    price = item.product.price
    return price * SUBSCRIPTION_DISCOUNT if item.subscribe else price


class CartItemSerializer(serializers.ModelSerializer):
    product = ProductListSerializer(read_only=True)
    product_id = serializers.IntegerField(write_only=True)
    line_total = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = ("id", "product", "product_id", "quantity", "subscribe", "line_total")

    def get_line_total(self, obj):
        return str(line_price(obj) * obj.quantity)


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    subtotal = serializers.SerializerMethodField()
    item_count = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ("id", "session_key", "items", "subtotal", "item_count")

    def get_subtotal(self, obj):
        total = Decimal("0")
        for item in obj.items.select_related("product"):
            total += line_price(item) * item.quantity
        return str(total)

    def get_item_count(self, obj):
        return sum(item.quantity for item in obj.items.all())


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = (
            "id",
            "product",
            "product_name",
            "sku",
            "quantity",
            "unit_price",
            "subscribe",
        )


class OrderSerializer(serializers.ModelSerializer):
    """Full order detail, for the signed-in owner only."""

    items = OrderItemSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Order
        fields = (
            "id",
            "status",
            "status_display",
            "email",
            "full_name",
            "phone",
            "address",
            "city",
            "state",
            "country",
            "notes",
            "subtotal",
            "shipping",
            "total",
            "payment_provider",
            "payment_reference",
            "paid_at",
            "created_at",
            "items",
        )
        read_only_fields = fields


class OrderPublicSerializer(serializers.ModelSerializer):
    """The reduced order view a guest receives after checkout or payment.

    Reachable with the order's ``public_token`` or by the signed-in owner, so it
    reveals only what a confirmation page needs: the email is masked and the
    delivery address and payment internals are omitted.
    """

    items = OrderItemSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    email_masked = serializers.SerializerMethodField()
    public_token = serializers.UUIDField(read_only=True)

    class Meta:
        model = Order
        fields = (
            "id",
            "status",
            "status_display",
            "email_masked",
            "full_name",
            "subtotal",
            "shipping",
            "total",
            "created_at",
            "public_token",
            "items",
        )

    def get_email_masked(self, obj):
        """``ada@example.com`` -> ``a**@example.com``."""
        email = obj.email or ""
        local, _, domain = email.partition("@")
        if not domain:
            return email
        visible = local[:1]
        return f"{visible}{'*' * max(len(local) - 1, 1)}@{domain}"


class CheckoutSerializer(serializers.Serializer):
    """Checkout input.

    Totals are **never** taken from this payload - the server prices the basket
    from the catalogue, so a tampered request cannot set its own price. Field
    lengths mirror the model so a huge string cannot be stored.
    """

    session_key = serializers.CharField(
        required=False, allow_blank=True, max_length=64, trim_whitespace=True
    )
    email = serializers.EmailField()
    full_name = serializers.CharField(max_length=140)
    phone = serializers.CharField(required=False, allow_blank=True, max_length=40)
    address = serializers.CharField(max_length=240)
    city = serializers.CharField(max_length=80)
    state = serializers.CharField(max_length=80)
    country = serializers.CharField(required=False, allow_blank=True, max_length=80, default="Nigeria")
    notes = serializers.CharField(required=False, allow_blank=True, max_length=1000)

    def validate_email(self, value):
        return value.strip().lower()

    def validate_session_key(self, value):
        return (value or "").strip()

