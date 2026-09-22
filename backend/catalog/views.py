from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Category, Product
from .serializers import CategorySerializer, ProductListSerializer, ProductDetailSerializer


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    lookup_field = "slug"


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Product.objects.select_related("category").prefetch_related("reviews")
    lookup_field = "slug"
    filterset_fields = ("category__slug", "is_featured", "is_supplement", "in_stock")
    search_fields = ("name", "short_benefit", "description", "ingredients")
    ordering_fields = ("price", "name", "rating", "created_at")

    def get_serializer_class(self):
        if self.action == "retrieve":
            return ProductDetailSerializer
        return ProductListSerializer

    @action(detail=True)
    def related(self, request, slug=None):
        product = self.get_object()
        qs = Product.objects.filter(category=product.category).exclude(pk=product.pk)[:4]
        return Response(ProductListSerializer(qs, many=True).data)

    @action(detail=False)
    def featured(self, request):
        qs = self.get_queryset().filter(is_featured=True)[:8]
        return Response(ProductListSerializer(qs, many=True).data)
