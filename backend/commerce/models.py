from django.conf import settings
from django.db import models


class Cart(models.Model):
    session_key = models.CharField(max_length=64, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name="items", on_delete=models.CASCADE)
    product = models.ForeignKey("catalog.Product", on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    subscribe = models.BooleanField(default=False)

    class Meta:
        unique_together = ("cart", "product", "subscribe")


class Order(models.Model):
    STATUS = [
        ("pending", "Pending"),
        ("paid", "Paid"),
        ("fulfilled", "Fulfilled"),
        ("cancelled", "Cancelled"),
    ]
    email = models.EmailField()
    full_name = models.CharField(max_length=140)
    phone = models.CharField(max_length=40, blank=True)
    address = models.CharField(max_length=240)
    city = models.CharField(max_length=80)
    state = models.CharField(max_length=80)
    country = models.CharField(max_length=80, default="Nigeria")
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS, default="pending")
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    shipping = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)
    product_name = models.CharField(max_length=200)
    sku = models.CharField(max_length=40)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    subscribe = models.BooleanField(default=False)
