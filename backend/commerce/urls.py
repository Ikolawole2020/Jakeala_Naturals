from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import CartViewSet, OrderViewSet, checkout

router = DefaultRouter()
router.register("cart", CartViewSet, basename="cart")
router.register("orders", OrderViewSet, basename="order")

urlpatterns = router.urls + [path("checkout/", checkout, name="checkout")]

