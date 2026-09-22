from rest_framework.routers import DefaultRouter
from .views import ArticleViewSet, NewsletterViewSet, ContactViewSet

router = DefaultRouter()
router.register("articles", ArticleViewSet)
router.register("newsletter", NewsletterViewSet, basename="newsletter")
router.register("contact", ContactViewSet, basename="contact")
urlpatterns = router.urls
