from collections import defaultdict

import django_filters
from django.db.models import Q

from .models import Category, Product


class ProductFilter(django_filters.FilterSet):
    category = django_filters.CharFilter(method="filter_by_category_slug")
    product_type = django_filters.ChoiceFilter(choices=Product.ProductType.choices)
    skill_tag = django_filters.CharFilter(method="filter_by_skill_tag_slug")
    in_stock = django_filters.BooleanFilter(method="filter_in_stock")

    class Meta:
        model = Product
        fields = ["product_type"]

    def filter_by_category_slug(self, queryset, name, value):
        """Accept comma-separated slugs. OR within a parent group, AND across groups."""
        slugs = [s.strip() for s in value.split(",") if s.strip()]
        if not slugs:
            return queryset

        # Look up the requested categories with their parents
        cats = Category.objects.filter(slug__in=slugs, is_active=True).select_related("parent")

        # Group by parent (None for root categories)
        groups: dict[int | None, list[str]] = defaultdict(list)
        for cat in cats:
            parent_id = cat.parent_id
            groups[parent_id].append(cat.slug)

        # AND across groups: each group must match at least one slug (OR within group)
        for _parent_id, group_slugs in groups.items():
            queryset = queryset.filter(categories__slug__in=group_slugs)

        return queryset

    def filter_by_skill_tag_slug(self, queryset, name, value):
        return queryset.filter(skill_tags__slug=value)

    def filter_in_stock(self, queryset, name, value):
        if value is True:
            return queryset.filter(
                Q(product_type=Product.ProductType.DIGITAL)
                | Q(
                    skus__is_active=True,
                    skus__stock_level__quantity_on_hand__gt=0,
                )
                | Q(
                    skus__is_active=True,
                    skus__stock_level__is_unlimited=True,
                )
                | Q(
                    skus__is_active=True,
                    skus__stock_level__backorder_enabled=True,
                )
            ).distinct()
        elif value is False:
            # Products that have no in-stock SKUs and are not digital
            in_stock_ids = queryset.filter(
                Q(product_type=Product.ProductType.DIGITAL)
                | Q(
                    skus__is_active=True,
                    skus__stock_level__quantity_on_hand__gt=0,
                )
                | Q(
                    skus__is_active=True,
                    skus__stock_level__is_unlimited=True,
                )
            ).distinct().values_list("id", flat=True)
            return queryset.exclude(id__in=in_stock_ids)
        return queryset
