from rest_framework import serializers

from catalog.models import Product, Review
from catalog.serializers import CategorySerializer, ReviewSerializer
from commerce.models import Order, OrderItem
from commerce.serializers import OrderItemSerializer
from content.models import Article, ContactMessage, NewsletterSubscriber
from content.serializers import ArticleSerializer, ContactSerializer


class ProductAdminSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)
    category_slug = serializers.CharField(source="category.slug", read_only=True)

    class Meta:
        model = Product
        fields = "__all__"


class OrderAdminSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = "__all__"
        read_only_fields = ("subtotal", "shipping", "total", "created_at")


class ReviewAdminSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)

    class Meta:
        model = Review
        fields = ("id", "product", "product_name", "author", "rating", "title", "body", "verified", "created_at")
        read_only_fields = ("created_at",)


class SubscriberAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = NewsletterSubscriber
        fields = ("id", "email", "created_at")


# Re-export reused serializers for the router wiring
AdminCategorySerializer = CategorySerializer
AdminArticleSerializer = ArticleSerializer
AdminContactSerializer = ContactSerializer