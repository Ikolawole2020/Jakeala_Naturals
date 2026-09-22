from decimal import Decimal
from rest_framework import serializers
from catalog.serializers import ProductListSerializer
from .models import Cart, CartItem, Order, OrderItem


class CartItemSerializer(serializers.ModelSerializer):
    product = ProductListSerializer(read_only=True)
    product_id = serializers.IntegerField(write_only=True)
    line_total = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = ("id", "product", "product_id", "quantity", "subscribe", "line_total")

    def get_line_total(self, obj):
        price = obj.product.price
        if obj.subscribe:
            price = price * (1 - Decimal("0.10"))
        return str(price * obj.quantity)


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    subtotal = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ("id", "session_key", "items", "subtotal")

    def get_subtotal(self, obj):
        total = Decimal("0")
        for item in obj.items.select_related("product"):
            price = item.product.price
            if item.subscribe:
                price = price * Decimal("0.90")
            total += price * item.quantity
        return str(total)


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = "__all__"


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = "__all__"


class CheckoutSerializer(serializers.Serializer):
    session_key = serializers.CharField()
    email = serializers.EmailField()
    full_name = serializers.CharField()
    phone = serializers.CharField(required=False, allow_blank=True)
    address = serializers.CharField()
    city = serializers.CharField()
    state = serializers.CharField()
    country = serializers.CharField(default="Nigeria")
    notes = serializers.CharField(required=False, allow_blank=True)
