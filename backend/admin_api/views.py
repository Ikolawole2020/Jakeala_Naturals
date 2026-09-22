from decimal import Decimal

from django.contrib.auth import authenticate
from rest_framework import status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response

from catalog.models import Category, Product, Review
from commerce.models import Order
from content.models import Article, ContactMessage, NewsletterSubscriber

from .serializers import (
    AdminArticleSerializer,
    AdminCategorySerializer,
    AdminContactSerializer,
    OrderAdminSerializer,
    ProductAdminSerializer,
    ReviewAdminSerializer,
    SubscriberAdminSerializer,
)


@api_view(["POST"])
@permission_classes([])
def admin_login(request):
    username = request.data.get("username", "").strip()
    password = request.data.get("password", "")
    user = authenticate(request, username=username, password=password)
    if user is None or not user.is_staff:
        return Response({"detail": "Invalid credentials or not a staff account."}, status=status.HTTP_401_UNAUTHORIZED)
    token, _ = Token.objects.get_or_create(user=user)
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
