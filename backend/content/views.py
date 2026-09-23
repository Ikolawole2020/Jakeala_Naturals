from rest_framework import mixins, status, viewsets
from rest_framework.response import Response
from .models import Article, NewsletterSubscriber, ContactMessage
from .serializers import ArticleSerializer, NewsletterSerializer, ContactSerializer


class ArticleViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Article.objects.filter(published=True)
    serializer_class = ArticleSerializer
    lookup_field = "slug"
    search_fields = ("title", "excerpt", "body")


class NewsletterViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    queryset = NewsletterSubscriber.objects.all()
    serializer_class = NewsletterSerializer
    # Sign-up only, and capped per caller so the form cannot be used to spam the
    # subscriber list.
    throttle_scope = "newsletter"

    def create(self, request, *args, **kwargs):
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        NewsletterSubscriber.objects.get_or_create(email=ser.validated_data["email"])
        return Response({"ok": True, "message": "Welcome to the Jakeala Naturals community."}, status=status.HTTP_201_CREATED)


class ContactViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    queryset = ContactMessage.objects.all()
    serializer_class = ContactSerializer
    # The enquiry form writes to the database and can trigger email, so it is
    # rate limited rather than open to unlimited automated posts.
    throttle_scope = "contact"

