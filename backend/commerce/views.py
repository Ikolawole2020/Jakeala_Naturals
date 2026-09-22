from decimal import Decimal
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from catalog.models import Product
from .models import Cart, CartItem, Order, OrderItem
from .serializers import CartSerializer, CheckoutSerializer, OrderSerializer


def get_cart(session_key):
    cart, _ = Cart.objects.get_or_create(session_key=session_key)
    return cart


class CartViewSet(viewsets.ViewSet):
    def list(self, request):
        key = request.query_params.get("session") or request.session.session_key or "guest"
        return Response(CartSerializer(get_cart(key)).data)

    @action(detail=False, methods=["post"])
    def add(self, request):
        key = request.data.get("session") or "guest"
        product = Product.objects.get(pk=request.data["product_id"])
        qty = int(request.data.get("quantity", 1))
        subscribe = bool(request.data.get("subscribe", False))
        cart = get_cart(key)
        item, created = CartItem.objects.get_or_create(
            cart=cart, product=product, subscribe=subscribe, defaults={"quantity": qty}
        )
        if not created:
            item.quantity += qty
            item.save()
        return Response(CartSerializer(cart).data)

    @action(detail=False, methods=["post"])
    def update_item(self, request):
        key = request.data.get("session") or "guest"
        item = CartItem.objects.get(pk=request.data["item_id"], cart__session_key=key)
        qty = int(request.data.get("quantity", 1))
        if qty <= 0:
            item.delete()
        else:
            item.quantity = qty
            item.save()
        return Response(CartSerializer(get_cart(key)).data)

    @action(detail=False, methods=["post"])
    def clear(self, request):
        key = request.data.get("session") or "guest"
        CartItem.objects.filter(cart__session_key=key).delete()
        return Response(CartSerializer(get_cart(key)).data)


@api_view(["POST"])
def checkout(request):
    ser = CheckoutSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    data = ser.validated_data
    cart = get_cart(data["session_key"])
    items = list(cart.items.select_related("product"))
    if not items:
        return Response({"detail": "Cart is empty"}, status=400)
    subtotal = Decimal("0")
    for item in items:
        price = item.product.price
        if item.subscribe:
            price = price * Decimal("0.90")
        subtotal += price * item.quantity
    shipping = Decimal("0") if subtotal >= 15000 else Decimal("2500")
    order = Order.objects.create(
        email=data["email"],
        full_name=data["full_name"],
        phone=data.get("phone", ""),
        address=data["address"],
        city=data["city"],
        state=data["state"],
        country=data.get("country", "Nigeria"),
        notes=data.get("notes", ""),
        status="paid",
        subtotal=subtotal,
        shipping=shipping,
        total=subtotal + shipping,
    )
    for item in items:
        price = item.product.price
        if item.subscribe:
            price = price * Decimal("0.90")
        OrderItem.objects.create(
            order=order,
            product_name=item.product.name,
            sku=item.product.sku,
            quantity=item.quantity,
            unit_price=price,
            subscribe=item.subscribe,
        )
    cart.items.all().delete()
    return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)


class OrderViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Order.objects.prefetch_related("items")
    serializer_class = OrderSerializer
    filterset_fields = ("email", "status")
