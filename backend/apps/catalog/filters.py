import django_filters
from django.db.models import Q

from .models import Product


class ProductFilter(django_filters.FilterSet):
    category = django_filters.CharFilter(method="filter_by_category_slug")
    product_type = django_filters.ChoiceFilter(choices=Product.ProductType.choices)
    skill_tag = django_filters.CharFilter(method="filter_by_skill_tag_slug")
    in_stock = django_filters.BooleanFilter(method="filter_in_stock")

    class Meta:
        model = Product
        fields = ["product_type"]

    def filter_by_category_slug(self, queryset, name, value):
        return queryset.filter(categories__slug=value)

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
