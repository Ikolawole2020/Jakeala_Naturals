from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    ArticleAdminViewSet,
    CategoryAdminViewSet,
    ContactMessageAdminViewSet,
    CustomerAdminViewSet,
    OrderAdminViewSet,
    ProductAdminViewSet,
    ReviewAdminViewSet,
    SubscriberAdminViewSet,
    admin_login,
    admin_logout,
    admin_me,
    admin_stats,
)

router = DefaultRouter()
router.register("products", ProductAdminViewSet, basename="adm-product")
router.register("categories", CategoryAdminViewSet, basename="adm-category")
router.register("orders", OrderAdminViewSet, basename="adm-order")
router.register("reviews", ReviewAdminViewSet, basename="adm-review")
router.register("articles", ArticleAdminViewSet, basename="adm-article")
router.register("subscribers", SubscriberAdminViewSet, basename="adm-subscriber")
router.register("messages", ContactMessageAdminViewSet, basename="adm-message")
router.register("customers", CustomerAdminViewSet, basename="adm-customer")

urlpatterns = [
    path("login/", admin_login, name="admin-login"),
    path("logout/", admin_logout, name="admin-logout"),
    path("me/", admin_me, name="admin-me"),
    path("stats/", admin_stats, name="admin-stats"),
] + router.urls