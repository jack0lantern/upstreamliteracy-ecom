from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=120)
    slug = models.SlugField(unique=True)
    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="children",
    )
    description = models.TextField(blank=True)
    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["display_order", "name"]
        verbose_name_plural = "categories"

    def __str__(self):
        return self.name


class SkillTag(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    curriculum_standard = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.name


class Product(models.Model):
    class ProductType(models.TextChoices):
        PHYSICAL = "physical", "Physical"
        DIGITAL = "digital", "Digital"
        BUNDLE = "bundle", "Bundle"

    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, max_length=255)
    product_type = models.CharField(
        max_length=10,
        choices=ProductType.choices,
        default=ProductType.PHYSICAL,
    )
    description = models.TextField()
    short_description = models.TextField(blank=True)
    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    categories = models.ManyToManyField(
        Category,
        through="ProductCategory",
        related_name="products",
    )
    skill_tags = models.ManyToManyField(SkillTag, blank=True, related_name="products")
    format_specs = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    seo_title = models.CharField(max_length=160, blank=True)
    seo_description = models.CharField(max_length=320, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    @property
    def primary_image(self):
        return self.images.filter(is_primary=True).first() or self.images.first()


class ProductCategory(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = [("product", "category")]
        ordering = ["display_order"]


class ProductImage(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="images",
    )
    image = models.ImageField(upload_to="products/")
    alt_text = models.CharField(max_length=255, blank=True)
    is_primary = models.BooleanField(default=False)
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["display_order"]

    def __str__(self):
        return f"{self.product.title} - Image {self.display_order}"


class SKU(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="skus",
    )
    sku_code = models.CharField(max_length=64, unique=True)
    variant_label = models.CharField(max_length=100, blank=True)
    price_override = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.sku_code

    @property
    def effective_price(self):
        return self.price_override if self.price_override is not None else self.product.base_price


class BundleComponent(models.Model):
    bundle_product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="bundle_components",
        limit_choices_to={"product_type": Product.ProductType.BUNDLE},
    )
    component_sku = models.ForeignKey(SKU, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = [("bundle_product", "component_sku")]

    def __str__(self):
        return f"{self.bundle_product.title} → {self.component_sku.sku_code} x{self.quantity}"
