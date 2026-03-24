from django.contrib import admin

from .models import (
    BundleComponent,
    Category,
    Product,
    ProductCategory,
    ProductImage,
    SKU,
    SkillTag,
)


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ["image", "alt_text", "is_primary", "display_order"]
    ordering = ["display_order"]


class SKUInline(admin.TabularInline):
    model = SKU
    extra = 1
    fields = ["sku_code", "variant_label", "price_override", "is_active"]
    readonly_fields = ["created_at"]
    show_change_link = True


class BundleComponentInline(admin.TabularInline):
    model = BundleComponent
    fk_name = "bundle_product"
    extra = 1
    fields = ["component_sku", "quantity"]
    autocomplete_fields = ["component_sku"]


class ProductCategoryInline(admin.TabularInline):
    model = ProductCategory
    extra = 1
    fields = ["category", "display_order"]
    autocomplete_fields = ["category"]


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "product_type",
        "base_price",
        "is_active",
        "is_featured",
        "created_at",
    ]
    list_filter = ["product_type", "is_active", "is_featured", "categories"]
    search_fields = ["title", "description", "skus__sku_code"]
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ["created_at", "updated_at"]
    inlines = [ProductCategoryInline, ProductImageInline, SKUInline, BundleComponentInline]
    fieldsets = [
        (
            "Core",
            {
                "fields": [
                    "title",
                    "slug",
                    "product_type",
                    "base_price",
                    "is_active",
                    "is_featured",
                ],
            },
        ),
        (
            "Content",
            {
                "fields": ["short_description", "description", "skill_tags", "format_specs"],
            },
        ),
        (
            "SEO",
            {
                "fields": ["seo_title", "seo_description"],
                "classes": ["collapse"],
            },
        ),
        (
            "Timestamps",
            {
                "fields": ["created_at", "updated_at"],
                "classes": ["collapse"],
            },
        ),
    ]
    filter_horizontal = ["skill_tags"]
    date_hierarchy = "created_at"
    ordering = ["-created_at"]


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "parent", "display_order", "is_active"]
    list_filter = ["is_active", "parent"]
    search_fields = ["name", "slug"]
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ["created_at", "updated_at"]
    ordering = ["display_order", "name"]


@admin.register(SkillTag)
class SkillTagAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "curriculum_standard"]
    search_fields = ["name", "slug", "curriculum_standard"]
    prepopulated_fields = {"slug": ("name",)}
    ordering = ["name"]


@admin.register(SKU)
class SKUAdmin(admin.ModelAdmin):
    list_display = ["sku_code", "product", "variant_label", "price_override", "is_active"]
    list_filter = ["is_active"]
    search_fields = ["sku_code", "product__title"]
    raw_id_fields = ["product"]
    readonly_fields = ["created_at"]
    ordering = ["sku_code"]
