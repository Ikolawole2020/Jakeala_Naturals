"""Commerce models: carts, orders and order lines.

Three decisions in this file are security decisions:

* ``Order.public_token`` is a bearer secret. A guest who has just checked out can
  read and pay for their own order with it, and it is the *only* thing that grants
  that access - a bare order id grants nothing. That is what closes the old
  "look up anyone's orders by typing their email" leak.
* ``Order.user`` links an order to an account when one exists, so the customer
  portal can show order history without any way to reach someone else's.
* ``OrderItem`` keeps a live ``product`` link *and* a snapshot of the name, sku
  and unit price at purchase time. Stock can therefore be decremented on payment
  while the historical record stays accurate even if the product is later renamed,
  repriced or deleted.
"""

import uuid

from django.conf import settings
from django.db import models


class Cart(models.Model):
    """A basket, identified by a random token (guests) or by user id (members).

    The session key is generated server-side and must be 16+ characters, so one
    shopper cannot read or edit another's cart by inventing a short key - the old
    ``"guest"`` fallback meant every anonymous visitor shared a single basket.
    """

    session_key = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart {self.session_key}"


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name="items", on_delete=models.CASCADE)
    product = models.ForeignKey("catalog.Product", on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    subscribe = models.BooleanField(default=False)

    class Meta:
        unique_together = ("cart", "product", "subscribe")

    def __str__(self):
        return f"{self.quantity} x {self.product_id}"


class Order(models.Model):
    PENDING = "pending"
    PAID = "paid"
    FULFILLED = "fulfilled"
    CANCELLED = "cancelled"
    STATUS = [
        (PENDING, "Pending"),
        (PAID, "Paid"),
        (FULFILLED, "Fulfilled"),
        (CANCELLED, "Cancelled"),
    ]

    # Set when the buyer is signed in, or when the email matches an account.
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="orders",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    # Bearer token for guest access to this one order. Never shown in lists.
    public_token = models.UUIDField(default=uuid.uuid4, editable=False, db_index=True)

    email = models.EmailField(db_index=True)
    full_name = models.CharField(max_length=140)
    phone = models.CharField(max_length=40, blank=True)
    address = models.CharField(max_length=240)
    city = models.CharField(max_length=80)
    state = models.CharField(max_length=80)
    country = models.CharField(max_length=80, default="Nigeria")
    notes = models.TextField(blank=True)

    status = models.CharField(max_length=20, choices=STATUS, default=PENDING, db_index=True)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    shipping = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2)

    # Payment trail. ``payment_reference`` is the unguessable Paystack reference
    # that the callback and the webhook are matched against.
    payment_provider = models.CharField(max_length=20, blank=True)
    payment_reference = models.CharField(max_length=120, blank=True, db_index=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    # Guards the one-way stock decrement so a duplicate webhook cannot subtract twice.
    stock_reduced = models.BooleanField(default=False)
    # The basket this order came from. Kept so the basket is only emptied once the
    # payment actually succeeds - abandoning Paystack must not lose the shopping.
    cart_key = models.CharField(max_length=64, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Order #{self.pk} - {self.email} ({self.status})"

    @property
    def is_settled(self):
        return self.status in {self.PAID, self.FULFILLED}


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)
    product = models.ForeignKey(
        "catalog.Product",
        related_name="order_items",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    # Snapshot taken at purchase time - these never change with the catalogue.
    product_name = models.CharField(max_length=200)
    sku = models.CharField(max_length=40)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    subscribe = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.quantity} x {self.product_name}"

