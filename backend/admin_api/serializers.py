from rest_framework import serializers

from catalog.models import Product, Review
from catalog.serializers import CategorySerializer, ReviewSerializer
from commerce.models import Order, OrderItem
from commerce.serializers import OrderItemSerializer
from content.models import Article, ContactMessage, NewsletterSubscriber
from content.serializers import ArticleSerializer, ContactSerializer
from django.contrib.auth.models import User

from accounts.models import Profile


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


class CustomerAdminSerializer(serializers.ModelSerializer):
    """A staff-facing view of a customer account.

    The password is write-only: an admin can *set* a new one to help a locked-out
    customer, but can never read the stored hash back. Deleting a customer cascades
    to their profile, verification codes and auth tokens, which is the behaviour
    the dashboard's Delete button relies on.
    """

    username = serializers.CharField(required=False)
    password = serializers.CharField(write_only=True, required=False, min_length=8)
    email_verified = serializers.SerializerMethodField()
    marketing_opt_in = serializers.SerializerMethodField()
    phone = serializers.SerializerMethodField()
    order_count = serializers.SerializerMethodField()
    orders = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "password",
            "is_active",
            "is_staff",
            "date_joined",
            "last_login",
            "email_verified",
            "marketing_opt_in",
            "phone",
            "order_count",
            "orders",
        )
        read_only_fields = ("id", "date_joined", "last_login")

    # The profile and order rows are created by signals / the order pipeline, so
    # they are read through the relation rather than accepted as writable input.
    def _profile(self, obj):
        # get_or_create keeps this safe for users created before a Profile existed.
        profile, _ = Profile.objects.get_or_create(user=obj)
        return profile

    def get_email_verified(self, obj):
        return self._profile(obj).email_verified

    def get_marketing_opt_in(self, obj):
        return self._profile(obj).marketing_opt_in

    def get_phone(self, obj):
        return self._profile(obj).phone

    def _orders(self, obj):
        """Orders belonging to this customer.

        ``Order.user`` is only set when the buyer was signed in, so a guest who
        then created an account still has a row carrying only their email. Matching
        on the address as well means the dashboard shows the real order history
        rather than an empty list, and keeps a signed-out order visible to the
        account it belongs to.
        """
        return (
            Order.objects.filter(user=obj)
            | Order.objects.filter(user__isnull=True, email__iexact=obj.email)
        ).distinct()

    def get_orders(self, obj):
        return [
            {
                "id": order.id,
                "reference": order.payment_reference or "",
                "total": str(order.total),
                "status": order.status,
                "created_at": order.created_at.isoformat(),
            }
            for order in self._orders(obj)[:10]
        ]

    def get_order_count(self, obj):
        return self._orders(obj).count()

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        # first_name/last_name may be absent on a PATCH; ignore blank strings so an
        # empty form field does not wipe the name.
        instance = super().update(
            instance,
            {k: v for k, v in validated_data.items() if v not in ("", None)},
        )
        if password:
            instance.set_password(password)
            instance.save(update_fields=["password"])
        if "email" in validated_data and validated_data["email"]:
            # Keep the username aligned with the address people actually type.
            if not instance.username or instance.username.startswith("user"):
                base = validated_data["email"].split("@")[0]
                instance.username = f"{base}{instance.pk}"
                instance.save(update_fields=["username"])
        return instance


# Re-export reused serializers for the router wiring
AdminCategorySerializer = CategorySerializer
AdminArticleSerializer = ArticleSerializer
AdminContactSerializer = ContactSerializer