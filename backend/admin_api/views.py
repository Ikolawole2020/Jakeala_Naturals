from decimal import Decimal

from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from rest_framework import status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response

from catalog.models import Category, Product, Review
from commerce.models import Order
from config.throttles import AdminLoginThrottle
from content.models import Article, ContactMessage, NewsletterSubscriber

from .serializers import (
    AdminArticleSerializer,
    AdminCategorySerializer,
    AdminContactSerializer,
    CustomerAdminSerializer,
    OrderAdminSerializer,
    ProductAdminSerializer,
    ReviewAdminSerializer,
    SubscriberAdminSerializer,
)


@api_view(["POST"])
@permission_classes([])
@throttle_classes([AdminLoginThrottle])
def admin_login(request):
    """Staff sign-in.

    Rate limited per caller: without it this endpoint allowed unlimited password
    guessing against a known username.
    """
    username = request.data.get("username", "").strip()
    password = request.data.get("password", "")
    user = authenticate(request, username=username, password=password)
    if user is None or not user.is_staff:
        return Response({"detail": "Invalid credentials or not a staff account."}, status=status.HTTP_401_UNAUTHORIZED)
    # Refresh the expiry clock on every sign-in (see AUTH_TOKEN_TTL).
    token, created = Token.objects.get_or_create(user=user)
    if not created:
        token.delete()
        token = Token.objects.create(user=user)
    return Response({"token": token.key, "username": user.username})



@api_view(["POST"])
@permission_classes([IsAuthenticated, IsAdminUser])
def admin_logout(request):
    Token.objects.filter(user=request.user).delete()
    return Response({"ok": True})


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsAdminUser])
def admin_me(request):
    return Response({"username": request.user.username, "email": request.user.email})


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsAdminUser])
def admin_stats(request):
    fulfilled = Order.objects.filter(status__in=["paid", "fulfilled"])
    paid_total = sum((o.total for o in fulfilled), Decimal("0"))
    return Response(
        {
            "products": Product.objects.count(),
            "categories": Category.objects.count(),
            "orders": Order.objects.count(),
            "pending_orders": Order.objects.filter(status="pending").count(),
            "revenue": str(paid_total),
            "subscribers": NewsletterSubscriber.objects.count(),
            "messages": ContactMessage.objects.count(),
            "articles": Article.objects.count(),
            "customers": User.objects.filter(is_staff=False).count(),
        }
    )


class _IsStaffModelViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsAdminUser]


class ProductAdminViewSet(_IsStaffModelViewSet):
    queryset = Product.objects.select_related("category").all()
    serializer_class = ProductAdminSerializer
    filterset_fields = ("category", "is_featured", "is_supplement")
    search_fields = ("name", "slug", "sku")
    ordering = ("-id",)


class CategoryAdminViewSet(_IsStaffModelViewSet):
    queryset = Category.objects.all()
    serializer_class = AdminCategorySerializer
    search_fields = ("name", "slug")
    ordering = ("sort_order",)


class OrderAdminViewSet(_IsStaffModelViewSet):
    queryset = Order.objects.prefetch_related("items").all()
    serializer_class = OrderAdminSerializer
    filterset_fields = ("status",)
    search_fields = ("email", "full_name", "id")
    ordering = ("-id",)


class ReviewAdminViewSet(_IsStaffModelViewSet):
    queryset = Review.objects.select_related("product").all()
    serializer_class = ReviewAdminSerializer
    ordering = ("-id",)


class ArticleAdminViewSet(_IsStaffModelViewSet):
    queryset = Article.objects.all()
    serializer_class = AdminArticleSerializer
    search_fields = ("title", "slug")
    ordering = ("-id",)


class SubscriberAdminViewSet(_IsStaffModelViewSet):
    http_method_names = ["get", "delete", "options", "head"]
    queryset = NewsletterSubscriber.objects.all()
    serializer_class = SubscriberAdminSerializer
    ordering = ("-id",)


class ContactMessageAdminViewSet(_IsStaffModelViewSet):
    http_method_names = ["get", "delete", "options", "head"]
    queryset = ContactMessage.objects.all()
    serializer_class = AdminContactSerializer
    filterset_fields = ("kind",)
    ordering = ("-id",)


class CustomerAdminViewSet(_IsStaffModelViewSet):
    """List, edit and delete customer accounts.

    Two safeguards, both deliberate:

    * **Staff cannot be deleted through here.** If a superuser removed themselves
      (or the only other admin) by accident, the dashboard would lock everyone out
      with no way back in short of the Django shell. The last remaining superuser
      is protected outright.
    * **Django's own ``/admin/`` remains the escape hatch** for the rare case a
      lockout is genuinely wanted - it has its own confirmation flow.
    """

    queryset = User.objects.all()
    serializer_class = CustomerAdminSerializer
    search_fields = ("username", "email", "first_name", "last_name")
    filterset_fields = ("is_active", "is_staff")
    ordering = ("-date_joined",)

    def _protected(self, user):
        """A superuser must not be removed, and never the last one."""
        if not user.is_superuser:
            return False
        return User.objects.filter(is_superuser=True).count() <= 1

    def perform_destroy(self, instance):
        if self._protected(instance):
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied(
                "This is the last superuser. Promote another staff member first, "
                "or delete the account from Django's own admin at /admin/."
            )
        # Cascade: profile, verification codes and any auth tokens.
        instance.delete()

    def perform_update(self, serializer):
        instance = self.get_object()
        if self._protected(instance) and not serializer.validated_data.get("is_staff", True):
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied(
                "This is the last superuser, so it cannot be demoted. "
                "Promote another staff member first."
            )
        serializer.save()
