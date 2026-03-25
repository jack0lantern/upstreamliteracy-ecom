"""Shared pytest fixtures for the Upstream Literacy backend test suite."""

import pytest
from decimal import Decimal

from apps.catalog.models import Category, Product, ProductCategory, SKU, SkillTag
from apps.inventory.models import StockLevel


# ---------------------------------------------------------------------------
# Category fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def grade_parent(db):
    return Category.objects.create(name="By Grade", slug="by-grade", display_order=10)


@pytest.fixture
def focus_parent(db):
    return Category.objects.create(name="By Focus", slug="by-focus", display_order=20)


@pytest.fixture
def format_parent(db):
    return Category.objects.create(name="By Format", slug="by-format", display_order=30)


@pytest.fixture
def grade_k(grade_parent):
    return Category.objects.create(
        name="Kindergarten", slug="kindergarten", parent=grade_parent, display_order=20,
    )


@pytest.fixture
def grade_1(grade_parent):
    return Category.objects.create(
        name="Grade 1", slug="grade-1", parent=grade_parent, display_order=30,
    )


@pytest.fixture
def grade_2(grade_parent):
    return Category.objects.create(
        name="Grade 2", slug="grade-2", parent=grade_parent, display_order=40,
    )


@pytest.fixture
def focus_phonics(focus_parent):
    return Category.objects.create(
        name="Phonics", slug="phonics", parent=focus_parent, display_order=10,
    )


@pytest.fixture
def focus_fluency(focus_parent):
    return Category.objects.create(
        name="Fluency", slug="fluency", parent=focus_parent, display_order=30,
    )


@pytest.fixture
def format_readers(format_parent):
    return Category.objects.create(
        name="Decodable Readers", slug="decodable-readers", parent=format_parent, display_order=10,
    )


@pytest.fixture
def format_workbooks(format_parent):
    return Category.objects.create(
        name="Student Workbooks", slug="student-workbooks", parent=format_parent, display_order=30,
    )


@pytest.fixture
def format_guides(format_parent):
    return Category.objects.create(
        name="Teacher Guides", slug="teacher-guides", parent=format_parent, display_order=20,
    )


# ---------------------------------------------------------------------------
# Skill tag fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def tag_cvc(db):
    return SkillTag.objects.create(name="CVC Words", slug="cvc-words")


@pytest.fixture
def tag_blending(db):
    return SkillTag.objects.create(name="Blending", slug="blending")


# ---------------------------------------------------------------------------
# Helper to create a product with categories, SKU, and stock
# ---------------------------------------------------------------------------

def _make_product(
    title,
    slug,
    categories,
    *,
    product_type="physical",
    base_price="19.99",
    skill_tags=None,
    stock_qty=10,
    is_active=True,
):
    product = Product.objects.create(
        title=title,
        slug=slug,
        product_type=product_type,
        base_price=Decimal(base_price),
        description=f"Description for {title}",
        short_description=f"Short desc for {title}",
        is_active=is_active,
    )
    for cat in categories:
        ProductCategory.objects.create(product=product, category=cat)
    if skill_tags:
        product.skill_tags.set(skill_tags)
    sku = SKU.objects.create(product=product, sku_code=f"SKU-{slug.upper()}")
    # The post_save signal auto-creates a StockLevel; update it to desired values.
    is_digital = product_type == "digital"
    StockLevel.objects.filter(sku=sku).update(
        quantity_on_hand=0 if is_digital else stock_qty,
        is_unlimited=is_digital,
    )
    return product


@pytest.fixture
def make_product():
    """Factory fixture – call with (title, slug, categories, **kwargs)."""
    return _make_product
