from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector
from django.db.models import Count, Prefetch
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, mixins, status, viewsets
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .filters import ProductFilter
from .models import Category, Product, ProductImage, SKU
from .serializers import (
    CategorySerializer,
    ProductDetailSerializer,
    ProductListSerializer,
)


class CategoryViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """
    List all active categories as a tree, or retrieve one by slug.
    """

    serializer_class = CategorySerializer
    permission_classes = [AllowAny]
    lookup_field = "slug"

    def get_queryset(self):
        from django.db.models import Q

        return (
            Category.objects.filter(is_active=True)
            .annotate(
                product_count=Count(
                    "products", distinct=True,
                    filter=Q(products__is_active=True),
                ) + Count(
                    "children__products", distinct=True,
                    filter=Q(children__products__is_active=True),
                )
            )
            .prefetch_related("children")
            .order_by("display_order", "name")
        )

    def list(self, request, *args, **kwargs):
        """Return only root-level categories; children are nested via serializer."""
        queryset = self.get_queryset().filter(parent__isnull=True)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class ProductViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """
    List active products with filtering, or retrieve one by slug.
    """

    permission_classes = [AllowAny]
    lookup_field = "slug"
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ProductFilter
    search_fields = ["title", "description"]
    ordering_fields = ["base_price", "created_at", "title"]
    ordering = ["-created_at"]

    def get_queryset(self):
        qs = (
            Product.objects.filter(is_active=True)
            .prefetch_related(
                Prefetch(
                    "images",
                    queryset=ProductImage.objects.order_by("display_order"),
                ),
                Prefetch(
                    "skus",
                    queryset=SKU.objects.filter(is_active=True).select_related("stock_level"),
                ),
                "skill_tags",
                "categories",
            )
            .distinct()
        )
        return qs

    def get_serializer_class(self):
        if self.action == "retrieve":
            return ProductDetailSerializer
        return ProductListSerializer

    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class SearchView(APIView):
    """
    Full-text search across product title, description, and short_description.
    GET /search/?q=<query>
    """

    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        query_str = request.query_params.get("q", "").strip()
        if not query_str:
            return Response(
                {"detail": "Query parameter 'q' is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        search_vector = SearchVector("title", weight="A") + SearchVector(
            "short_description", weight="B"
        ) + SearchVector("description", weight="C")

        search_query = SearchQuery(query_str, search_type="websearch")

        qs = (
            Product.objects.filter(is_active=True)
            .annotate(rank=SearchRank(search_vector, search_query))
            .filter(rank__gte=0.01)
            .prefetch_related(
                Prefetch(
                    "images",
                    queryset=ProductImage.objects.order_by("display_order"),
                ),
                Prefetch(
                    "skus",
                    queryset=SKU.objects.filter(is_active=True).select_related("stock_level"),
                ),
                "skill_tags",
                "categories",
            )
            .distinct()
            .order_by("-rank", "-is_featured", "-created_at")
        )

        serializer = ProductListSerializer(qs, many=True, context={"request": request})
        return Response(
            {
                "count": qs.count(),
                "query": query_str,
                "results": serializer.data,
            }
        )
