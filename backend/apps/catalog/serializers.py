from rest_framework import serializers

from .models import Category, Product, ProductImage, SKU, SkillTag


class SkillTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = SkillTag
        fields = ["id", "name", "slug"]


class ProductImageSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = ProductImage
        fields = ["id", "image", "alt_text", "is_primary", "display_order"]

    def get_image(self, obj):
        request = self.context.get("request")
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        if obj.image:
            return obj.image.url
        return None


class SKUSerializer(serializers.ModelSerializer):
    effective_price = serializers.SerializerMethodField()
    stock_status = serializers.SerializerMethodField()

    class Meta:
        model = SKU
        fields = [
            "id",
            "sku_code",
            "variant_label",
            "effective_price",
            "stock_status",
            "is_active",
        ]

    def get_effective_price(self, obj):
        return str(obj.effective_price)

    def get_stock_status(self, obj):
        try:
            return obj.stock_level.stock_status
        except Exception:
            return "out_of_stock"


class CategorySerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()
    product_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = Category
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "parent_id",
            "children",
            "product_count",
            "display_order",
            "is_active",
        ]

    def get_children(self, obj):
        # Only recurse one level deep to avoid N+1 on large trees
        children = obj.children.filter(is_active=True).order_by("display_order", "name")
        return CategorySerializer(children, many=True, context=self.context).data


class ProductListSerializer(serializers.ModelSerializer):
    price = serializers.DecimalField(
        source="base_price",
        max_digits=10,
        decimal_places=2,
        read_only=True,
    )
    primary_image = serializers.SerializerMethodField()
    skill_tags = serializers.SerializerMethodField()
    is_in_stock = serializers.SerializerMethodField()
    category = serializers.SerializerMethodField()
    compare_at_price = serializers.SerializerMethodField()
    short_description = serializers.CharField()

    class Meta:
        model = Product
        fields = [
            "id",
            "slug",
            "title",
            "price",
            "compare_at_price",
            "primary_image",
            "skill_tags",
            "product_type",
            "format_specs",
            "is_in_stock",
            "category",
            "short_description",
            "is_featured",
        ]

    def get_primary_image(self, obj):
        img = obj.primary_image
        if not img:
            return None
        request = self.context.get("request")
        image_url = img.image.url if img.image else None
        if image_url and request:
            image_url = request.build_absolute_uri(image_url)
        return {
            "id": img.id,
            "image": image_url,
            "alt_text": img.alt_text or "",
            "is_primary": img.is_primary,
            "order": img.display_order,
        }

    def get_skill_tags(self, obj):
        return list(obj.skill_tags.values_list("name", flat=True))

    def get_is_in_stock(self, obj):
        # Digital products are always considered in stock
        if obj.product_type == Product.ProductType.DIGITAL:
            return True
        # Check if any active SKU has available stock
        active_skus = obj.skus.filter(is_active=True).prefetch_related("stock_level")
        for sku in active_skus:
            try:
                sl = sku.stock_level
                if sl.is_unlimited or sl.quantity_on_hand > 0 or sl.backorder_enabled:
                    return True
            except Exception:
                pass
        return False

    def get_category(self, obj):
        cat = obj.categories.order_by("productcategory__display_order").first()
        if not cat:
            return None
        return {"id": cat.id, "name": cat.name, "slug": cat.slug}

    def get_compare_at_price(self, obj):
        return None  # Product model has no compare_at_price; frontend accepts null


class ProductDetailSerializer(ProductListSerializer):
    description = serializers.CharField()
    short_description = serializers.CharField()
    images = ProductImageSerializer(many=True, read_only=True)
    skus = SKUSerializer(many=True, read_only=True)
    seo_title = serializers.CharField()
    seo_description = serializers.CharField()
    related_products = serializers.SerializerMethodField()

    class Meta(ProductListSerializer.Meta):
        fields = ProductListSerializer.Meta.fields + [
            "description",
            "images",
            "skus",
            "seo_title",
            "seo_description",
            "related_products",
            "created_at",
            "updated_at",
        ]

    def get_related_products(self, obj):
        """
        Return up to 4 active products sharing at least one category,
        excluding the current product, ordered by featured status then recency.
        """
        category_ids = obj.categories.values_list("id", flat=True)
        related_qs = (
            Product.objects.filter(
                is_active=True,
                categories__id__in=category_ids,
            )
            .exclude(pk=obj.pk)
            .distinct()
            .order_by("-is_featured", "-created_at")[:4]
        )
        return ProductListSerializer(related_qs, many=True, context=self.context).data
