"""Tests for ProductFilter — category, product_type, skill_tag, and in_stock filters."""

import pytest
from decimal import Decimal

from apps.catalog.filters import ProductFilter
from apps.catalog.models import Category, Product


pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _slugs(qs):
    """Return a sorted list of product slugs from a queryset."""
    return sorted(qs.values_list("slug", flat=True))


def _apply(data):
    """Apply ProductFilter with the given data dict and return the filtered qs."""
    qs = Product.objects.filter(is_active=True).distinct()
    return ProductFilter(data=data, queryset=qs).qs


# ---------------------------------------------------------------------------
# Category filter — single slug
# ---------------------------------------------------------------------------

class TestCategoryFilterSingle:
    def test_single_grade_returns_matching_products(
        self, make_product, grade_k, grade_1, focus_phonics, format_readers,
    ):
        p1 = make_product("Reader A", "reader-a", [grade_k, focus_phonics, format_readers])
        p2 = make_product("Reader B", "reader-b", [grade_1, focus_phonics, format_readers])
        p3 = make_product("Reader C", "reader-c", [grade_k, grade_1, focus_phonics, format_readers])

        result = _apply({"category": "kindergarten"})
        assert _slugs(result) == ["reader-a", "reader-c"]

    def test_single_focus_returns_matching_products(
        self, make_product, grade_k, focus_phonics, focus_fluency, format_readers,
    ):
        p1 = make_product("Phonics Book", "phonics-book", [grade_k, focus_phonics, format_readers])
        p2 = make_product("Fluency Book", "fluency-book", [grade_k, focus_fluency, format_readers])

        result = _apply({"category": "phonics"})
        assert _slugs(result) == ["phonics-book"]

    def test_single_format_returns_matching_products(
        self, make_product, grade_1, focus_phonics, format_readers, format_workbooks,
    ):
        p1 = make_product("A Reader", "a-reader", [grade_1, focus_phonics, format_readers])
        p2 = make_product("A Workbook", "a-workbook", [grade_1, focus_phonics, format_workbooks])

        result = _apply({"category": "decodable-readers"})
        assert _slugs(result) == ["a-reader"]

    def test_unknown_slug_returns_all(
        self, make_product, grade_k, focus_phonics, format_readers,
    ):
        """Unknown slugs match no categories → no filter groups → all products returned."""
        make_product("Reader A", "reader-a", [grade_k, focus_phonics, format_readers])

        result = _apply({"category": "nonexistent-category"})
        assert result.count() == 1

    def test_empty_string_returns_all(
        self, make_product, grade_k, focus_phonics, format_readers,
    ):
        make_product("Reader A", "reader-a", [grade_k, focus_phonics, format_readers])

        result = _apply({"category": ""})
        assert result.count() == 1


# ---------------------------------------------------------------------------
# Category filter — OR within same parent group
# ---------------------------------------------------------------------------

class TestCategoryFilterORWithinGroup:
    def test_two_grades_return_union(
        self, make_product, grade_k, grade_1, grade_2, focus_phonics, format_readers,
    ):
        p_k = make_product("K Book", "k-book", [grade_k, focus_phonics, format_readers])
        p_1 = make_product("G1 Book", "g1-book", [grade_1, focus_phonics, format_readers])
        p_2 = make_product("G2 Book", "g2-book", [grade_2, focus_phonics, format_readers])

        result = _apply({"category": "kindergarten,grade-1"})
        assert _slugs(result) == ["g1-book", "k-book"]

    def test_all_grades_return_all_products(
        self, make_product, grade_k, grade_1, grade_2, focus_phonics, format_readers,
    ):
        make_product("K Book", "k-book", [grade_k, focus_phonics, format_readers])
        make_product("G1 Book", "g1-book", [grade_1, focus_phonics, format_readers])
        make_product("G2 Book", "g2-book", [grade_2, focus_phonics, format_readers])

        result = _apply({"category": "kindergarten,grade-1,grade-2"})
        assert result.count() == 3

    def test_overlapping_grades_no_duplicates(
        self, make_product, grade_k, grade_1, focus_phonics, format_readers,
    ):
        """A product in both Kindergarten and Grade 1 appears once."""
        make_product("Multi Grade", "multi-grade", [grade_k, grade_1, focus_phonics, format_readers])
        make_product("K Only", "k-only", [grade_k, focus_phonics, format_readers])

        result = _apply({"category": "kindergarten,grade-1"})
        assert _slugs(result) == ["k-only", "multi-grade"]

    def test_two_formats_return_union(
        self, make_product, grade_1, focus_phonics, format_readers, format_workbooks,
    ):
        make_product("A Reader", "a-reader", [grade_1, focus_phonics, format_readers])
        make_product("A Workbook", "a-workbook", [grade_1, focus_phonics, format_workbooks])

        result = _apply({"category": "decodable-readers,student-workbooks"})
        assert result.count() == 2


# ---------------------------------------------------------------------------
# Category filter — AND across different parent groups
# ---------------------------------------------------------------------------

class TestCategoryFilterANDAcrossGroups:
    def test_grade_and_focus(
        self, make_product, grade_k, grade_1, focus_phonics, focus_fluency, format_readers,
    ):
        make_product("K Phonics", "k-phonics", [grade_k, focus_phonics, format_readers])
        make_product("K Fluency", "k-fluency", [grade_k, focus_fluency, format_readers])
        make_product("G1 Phonics", "g1-phonics", [grade_1, focus_phonics, format_readers])

        # Kindergarten AND Phonics → only k-phonics
        result = _apply({"category": "kindergarten,phonics"})
        assert _slugs(result) == ["k-phonics"]

    def test_grade_and_format(
        self, make_product, grade_k, grade_1, focus_phonics, format_readers, format_workbooks,
    ):
        make_product("K Reader", "k-reader", [grade_k, focus_phonics, format_readers])
        make_product("K Workbook", "k-workbook", [grade_k, focus_phonics, format_workbooks])
        make_product("G1 Reader", "g1-reader", [grade_1, focus_phonics, format_readers])

        # Kindergarten AND Decodable Readers → only k-reader
        result = _apply({"category": "kindergarten,decodable-readers"})
        assert _slugs(result) == ["k-reader"]

    def test_two_grades_and_one_focus(
        self, make_product, grade_k, grade_1, grade_2, focus_phonics, focus_fluency, format_readers,
    ):
        make_product("K Phonics", "k-phonics", [grade_k, focus_phonics, format_readers])
        make_product("G1 Phonics", "g1-phonics", [grade_1, focus_phonics, format_readers])
        make_product("G2 Fluency", "g2-fluency", [grade_2, focus_fluency, format_readers])
        make_product("K Fluency", "k-fluency", [grade_k, focus_fluency, format_readers])

        # (Kindergarten OR Grade 1) AND Phonics
        result = _apply({"category": "kindergarten,grade-1,phonics"})
        assert _slugs(result) == ["g1-phonics", "k-phonics"]

    def test_three_groups(
        self, make_product, grade_k, grade_1, focus_phonics, focus_fluency,
        format_readers, format_workbooks,
    ):
        make_product("K Phonics Reader", "k-phonics-reader", [grade_k, focus_phonics, format_readers])
        make_product("K Phonics WB", "k-phonics-wb", [grade_k, focus_phonics, format_workbooks])
        make_product("K Fluency Reader", "k-fluency-reader", [grade_k, focus_fluency, format_readers])
        make_product("G1 Phonics Reader", "g1-phonics-reader", [grade_1, focus_phonics, format_readers])

        # Kindergarten AND Phonics AND Decodable Readers
        result = _apply({"category": "kindergarten,phonics,decodable-readers"})
        assert _slugs(result) == ["k-phonics-reader"]

    def test_and_across_groups_empty_intersection(
        self, make_product, grade_k, grade_1, focus_phonics, focus_fluency, format_readers,
    ):
        make_product("K Phonics", "k-phonics", [grade_k, focus_phonics, format_readers])
        make_product("G1 Fluency", "g1-fluency", [grade_1, focus_fluency, format_readers])

        # Kindergarten AND Fluency → nothing (k-phonics is phonics, g1-fluency is grade 1)
        result = _apply({"category": "kindergarten,fluency"})
        assert result.count() == 0


# ---------------------------------------------------------------------------
# Category filter — edge cases
# ---------------------------------------------------------------------------

class TestCategoryFilterEdgeCases:
    def test_whitespace_in_slugs_is_trimmed(
        self, make_product, grade_k, focus_phonics, format_readers,
    ):
        make_product("Reader", "reader", [grade_k, focus_phonics, format_readers])

        result = _apply({"category": " kindergarten , phonics "})
        assert result.count() == 1

    def test_trailing_comma_ignored(
        self, make_product, grade_k, focus_phonics, format_readers,
    ):
        make_product("Reader", "reader", [grade_k, focus_phonics, format_readers])

        result = _apply({"category": "kindergarten,"})
        assert result.count() == 1

    def test_inactive_category_ignored_by_filter(
        self, make_product, grade_parent, grade_k, focus_phonics, format_readers,
    ):
        """An inactive category slug is ignored; only active categories filter."""
        inactive_grade = Category.objects.create(
            name="Inactive Grade", slug="inactive-grade",
            parent=grade_parent, is_active=False,
        )
        make_product("In Active Cat", "in-active-cat", [grade_k, focus_phonics, format_readers])
        make_product("In Inactive Cat", "in-inactive-cat", [inactive_grade, focus_phonics, format_readers])

        # Filtering by inactive slug alone → no active categories match → no-op → all returned
        result = _apply({"category": "inactive-grade"})
        assert result.count() == 2

        # Filtering by active grade excludes the product only in the inactive category
        result = _apply({"category": "kindergarten"})
        assert _slugs(result) == ["in-active-cat"]

    def test_inactive_product_excluded(
        self, make_product, grade_k, focus_phonics, format_readers,
    ):
        make_product("Active", "active", [grade_k, focus_phonics, format_readers])
        make_product("Inactive", "inactive", [grade_k, focus_phonics, format_readers], is_active=False)

        result = _apply({"category": "kindergarten"})
        assert _slugs(result) == ["active"]

    def test_no_filter_returns_all(self, make_product, grade_k, focus_phonics, format_readers):
        make_product("A", "a", [grade_k, focus_phonics, format_readers])
        make_product("B", "b", [grade_k, focus_phonics, format_readers])

        result = _apply({})
        assert result.count() == 2


# ---------------------------------------------------------------------------
# Product type filter
# ---------------------------------------------------------------------------

class TestProductTypeFilter:
    def test_physical_only(
        self, make_product, grade_k, focus_phonics, format_readers,
    ):
        make_product("Physical", "physical", [grade_k, focus_phonics, format_readers], product_type="physical")
        make_product("Digital", "digital", [grade_k, focus_phonics, format_readers], product_type="digital")

        result = _apply({"product_type": "physical"})
        assert _slugs(result) == ["physical"]

    def test_digital_only(
        self, make_product, grade_k, focus_phonics, format_readers,
    ):
        make_product("Physical", "physical", [grade_k, focus_phonics, format_readers], product_type="physical")
        make_product("Digital", "digital", [grade_k, focus_phonics, format_readers], product_type="digital")

        result = _apply({"product_type": "digital"})
        assert _slugs(result) == ["digital"]


# ---------------------------------------------------------------------------
# Skill tag filter
# ---------------------------------------------------------------------------

class TestSkillTagFilter:
    def test_filter_by_skill_tag(
        self, make_product, grade_k, focus_phonics, format_readers, tag_cvc, tag_blending,
    ):
        make_product("CVC Book", "cvc-book", [grade_k, focus_phonics, format_readers], skill_tags=[tag_cvc])
        make_product("Blend Book", "blend-book", [grade_k, focus_phonics, format_readers], skill_tags=[tag_blending])
        make_product("Both Tags", "both-tags", [grade_k, focus_phonics, format_readers], skill_tags=[tag_cvc, tag_blending])

        result = _apply({"skill_tag": "cvc-words"})
        assert _slugs(result) == ["both-tags", "cvc-book"]

    def test_unknown_skill_tag_returns_nothing(
        self, make_product, grade_k, focus_phonics, format_readers,
    ):
        make_product("Book", "book", [grade_k, focus_phonics, format_readers])
        result = _apply({"skill_tag": "nonexistent"})
        assert result.count() == 0


# ---------------------------------------------------------------------------
# In-stock filter
# ---------------------------------------------------------------------------

class TestInStockFilter:
    def test_in_stock_true_includes_stocked_products(
        self, make_product, grade_k, focus_phonics, format_readers,
    ):
        make_product("Stocked", "stocked", [grade_k, focus_phonics, format_readers], stock_qty=10)
        make_product("Empty", "empty", [grade_k, focus_phonics, format_readers], stock_qty=0)

        result = _apply({"in_stock": "true"})
        assert _slugs(result) == ["stocked"]

    def test_in_stock_true_includes_digital(
        self, make_product, grade_k, focus_phonics, format_readers,
    ):
        make_product("Digital", "digital", [grade_k, focus_phonics, format_readers], product_type="digital")
        make_product("Empty Physical", "empty-phys", [grade_k, focus_phonics, format_readers], stock_qty=0)

        result = _apply({"in_stock": "true"})
        assert _slugs(result) == ["digital"]

    def test_in_stock_true_includes_unlimited(
        self, make_product, grade_k, focus_phonics, format_readers,
    ):
        p = make_product("Unlimited", "unlimited", [grade_k, focus_phonics, format_readers], stock_qty=0)
        sl = p.skus.first().stock_level
        sl.is_unlimited = True
        sl.save()

        result = _apply({"in_stock": "true"})
        assert _slugs(result) == ["unlimited"]

    def test_in_stock_true_includes_backorder(
        self, make_product, grade_k, focus_phonics, format_readers,
    ):
        p = make_product("Backorder", "backorder", [grade_k, focus_phonics, format_readers], stock_qty=0)
        sl = p.skus.first().stock_level
        sl.backorder_enabled = True
        sl.save()

        result = _apply({"in_stock": "true"})
        assert _slugs(result) == ["backorder"]

    def test_in_stock_false_returns_out_of_stock(
        self, make_product, grade_k, focus_phonics, format_readers,
    ):
        make_product("Stocked", "stocked", [grade_k, focus_phonics, format_readers], stock_qty=10)
        make_product("Empty", "empty", [grade_k, focus_phonics, format_readers], stock_qty=0)

        result = _apply({"in_stock": "false"})
        assert _slugs(result) == ["empty"]


# ---------------------------------------------------------------------------
# Combined filters — category + other filters
# ---------------------------------------------------------------------------

class TestCombinedFilters:
    def test_category_and_product_type(
        self, make_product, grade_k, grade_1, focus_phonics, format_readers,
    ):
        make_product("K Physical", "k-physical", [grade_k, focus_phonics, format_readers], product_type="physical")
        make_product("K Digital", "k-digital", [grade_k, focus_phonics, format_readers], product_type="digital")
        make_product("G1 Physical", "g1-physical", [grade_1, focus_phonics, format_readers], product_type="physical")

        result = _apply({"category": "kindergarten", "product_type": "physical"})
        assert _slugs(result) == ["k-physical"]

    def test_category_and_in_stock(
        self, make_product, grade_k, grade_1, focus_phonics, format_readers,
    ):
        make_product("K Stocked", "k-stocked", [grade_k, focus_phonics, format_readers], stock_qty=10)
        make_product("K Empty", "k-empty", [grade_k, focus_phonics, format_readers], stock_qty=0)
        make_product("G1 Stocked", "g1-stocked", [grade_1, focus_phonics, format_readers], stock_qty=10)

        result = _apply({"category": "kindergarten", "in_stock": "true"})
        assert _slugs(result) == ["k-stocked"]

    def test_category_and_skill_tag(
        self, make_product, grade_k, grade_1, focus_phonics, format_readers, tag_cvc,
    ):
        make_product("K CVC", "k-cvc", [grade_k, focus_phonics, format_readers], skill_tags=[tag_cvc])
        make_product("K No Tag", "k-no-tag", [grade_k, focus_phonics, format_readers])
        make_product("G1 CVC", "g1-cvc", [grade_1, focus_phonics, format_readers], skill_tags=[tag_cvc])

        result = _apply({"category": "kindergarten", "skill_tag": "cvc-words"})
        assert _slugs(result) == ["k-cvc"]
