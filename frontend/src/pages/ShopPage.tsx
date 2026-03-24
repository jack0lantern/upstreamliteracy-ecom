import { useState } from 'react';
import { Helmet } from 'react-helmet-async';
import { useQuery } from '@tanstack/react-query';
import { useSearchParams } from 'react-router-dom';
import { productsApi } from '@/lib/api/products';
import { categoriesApi } from '@/lib/api/categories';
import { queryKeys } from '@/lib/queryKeys';
import { ProductGridSkeleton } from '@/components/ui/LoadingSkeleton';
import { ProductCard } from '@/components/product/ProductCard';
import { useAddToCart } from '@/hooks/useAddToCart';
import type { Category } from '@/types';

const SORT_OPTIONS = [
  { label: 'Featured', value: '' },
  { label: 'Price: Low to High', value: 'base_price' },
  { label: 'Price: High to Low', value: '-base_price' },
  { label: 'Newest', value: '-created_at' },
  { label: 'Name A\u2013Z', value: 'title' },
] as const;

/** Read comma-separated slugs from a search param */
function getFilterSlugs(params: URLSearchParams, key: string): Set<string> {
  const raw = params.get(key);
  if (!raw) return new Set();
  return new Set(raw.split(',').filter(Boolean));
}

/** Merge all selected filter slugs into a single comma-separated string for the API */
function buildCategoryParam(searchParams: URLSearchParams): string | undefined {
  const all: string[] = [];
  for (const key of ['grade', 'focus', 'format']) {
    const slugs = getFilterSlugs(searchParams, key);
    slugs.forEach((s) => all.push(s));
  }
  return all.length > 0 ? all.join(',') : undefined;
}

function FilterGroup({
  title,
  paramKey,
  children,
  searchParams,
  onToggle,
}: {
  title: string;
  paramKey: string;
  children: Category[];
  searchParams: URLSearchParams;
  onToggle: (paramKey: string, slug: string) => void;
}) {
  const [open, setOpen] = useState(true);
  const selected = getFilterSlugs(searchParams, paramKey);

  if (!children.length) return null;

  return (
    <fieldset className="mb-5">
      <legend>
        <button
          type="button"
          onClick={() => setOpen(!open)}
          className="flex w-full items-center justify-between text-sm font-semibold uppercase tracking-wide text-gray-700"
        >
          <span>{title}</span>
          <svg
            className={`h-4 w-4 text-gray-400 transition-transform ${open ? 'rotate-180' : ''}`}
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2}
          >
            <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
          </svg>
        </button>
      </legend>
      {open && (
        <div className="mt-2 space-y-1.5">
          {children.map((cat) => {
            const checked = selected.has(cat.slug);
            return (
              <label
                key={cat.id}
                className="flex cursor-pointer items-center gap-2 rounded px-2 py-1 text-sm text-gray-600 hover:bg-gray-50"
              >
                <input
                  type="checkbox"
                  checked={checked}
                  onChange={() => onToggle(paramKey, cat.slug)}
                  className="h-4 w-4 rounded border-gray-300 text-upstream-600 focus:ring-upstream-500"
                />
                <span className="flex-1">{cat.name}</span>
                <span className="text-xs text-gray-400">{cat.product_count}</span>
              </label>
            );
          })}
        </div>
      )}
    </fieldset>
  );
}

/** Map parent category names to URL param keys */
const PARENT_PARAM_MAP: Record<string, string> = {
  'by-grade': 'grade',
  'by-focus': 'focus',
  'by-format': 'format',
};

export default function ShopPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const sort = searchParams.get('sort') ?? '';
  const categoryParam = buildCategoryParam(searchParams);

  const { data: productsData, isLoading: productsLoading, isError } = useQuery({
    queryKey: queryKeys.products.list({
      page_size: 24,
      ordering: sort || undefined,
      category: categoryParam,
    }),
    queryFn: () =>
      productsApi.getProducts({
        page_size: 24,
        ordering: sort || undefined,
        category: categoryParam,
      }),
  });

  const { data: categories } = useQuery({
    queryKey: queryKeys.categories.list(),
    queryFn: categoriesApi.getCategories,
  });

  const addToCart = useAddToCart();
  const products = productsData?.results ?? [];

  // Count active filters
  const activeFilterCount = ['grade', 'focus', 'format'].reduce(
    (acc, key) => acc + getFilterSlugs(searchParams, key).size,
    0,
  );

  function handleSortChange(value: string) {
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev);
      if (value) {
        next.set('sort', value);
      } else {
        next.delete('sort');
      }
      return next;
    });
  }

  function handleToggleFilter(paramKey: string, slug: string) {
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev);
      const current = getFilterSlugs(next, paramKey);
      if (current.has(slug)) {
        current.delete(slug);
      } else {
        current.add(slug);
      }
      if (current.size > 0) {
        next.set(paramKey, [...current].join(','));
      } else {
        next.delete(paramKey);
      }
      return next;
    });
  }

  function handleClearFilters() {
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev);
      next.delete('grade');
      next.delete('focus');
      next.delete('format');
      return next;
    });
  }

  // Mobile filter toggle
  const [mobileFiltersOpen, setMobileFiltersOpen] = useState(false);

  // Build filter groups from category tree
  const filterGroups = (categories ?? [])
    .filter((cat) => cat.children && cat.children.length > 0)
    .map((parent) => ({
      title: parent.name.replace(/^By\s+/i, ''),
      paramKey: PARENT_PARAM_MAP[parent.slug] ?? parent.slug,
      children: parent.children,
    }));

  const filterSidebar = (
    <>
      {filterGroups.length > 0 ? (
        <>
          {activeFilterCount > 0 && (
            <button
              type="button"
              onClick={handleClearFilters}
              className="mb-4 text-xs font-medium text-upstream-600 hover:text-upstream-800"
            >
              Clear all filters ({activeFilterCount})
            </button>
          )}
          {filterGroups.map((group) => (
            <FilterGroup
              key={group.paramKey}
              title={group.title}
              paramKey={group.paramKey}
              children={group.children}
              searchParams={searchParams}
              onToggle={handleToggleFilter}
            />
          ))}
        </>
      ) : (
        <div className="animate-pulse space-y-2">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-8 rounded bg-gray-200" />
          ))}
        </div>
      )}
    </>
  );

  return (
    <>
      <Helmet>
        <title>Shop – Upstream Literacy</title>
        <meta name="description" content="Browse all educational materials from Upstream Literacy." />
      </Helmet>

      <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        {/* Page heading */}
        <div className="mb-6">
          <h1 className="text-3xl font-bold tracking-tight text-gray-900">Shop</h1>
          <p className="mt-1 text-sm text-gray-500">
            Discover books, guides, and digital resources for critical thinkers.
          </p>
        </div>

        <div className="flex flex-col gap-8 lg:flex-row">
          {/* Sidebar – filters (desktop) */}
          <aside className="hidden w-full lg:block lg:w-56 lg:flex-shrink-0" aria-label="Filter products">
            <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-gray-700">
              Filters
            </h2>
            {filterSidebar}
          </aside>

          {/* Product grid */}
          <div className="flex-1">
            {/* Mobile filter button */}
            <div className="mb-4 lg:hidden">
              <button
                type="button"
                onClick={() => setMobileFiltersOpen(!mobileFiltersOpen)}
                className="inline-flex items-center gap-2 rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
              >
                <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
                </svg>
                Filters
                {activeFilterCount > 0 && (
                  <span className="inline-flex h-5 w-5 items-center justify-center rounded-full bg-upstream-600 text-xs text-white">
                    {activeFilterCount}
                  </span>
                )}
              </button>
            </div>

            {/* Mobile filters panel */}
            {mobileFiltersOpen && (
              <div className="mb-6 rounded-lg border border-gray-200 bg-white p-4 lg:hidden">
                {filterSidebar}
              </div>
            )}

            {productsLoading ? (
              <ProductGridSkeleton count={8} />
            ) : isError ? (
              <div className="rounded-lg border border-red-200 bg-red-50 p-6 text-center">
                <p className="text-sm text-red-700">
                  Failed to load products. Please try refreshing the page.
                </p>
              </div>
            ) : products.length === 0 ? (
              <div className="rounded-lg border border-gray-200 p-12 text-center">
                <p className="text-gray-500">No products match the selected filters.</p>
                {activeFilterCount > 0 && (
                  <button
                    type="button"
                    onClick={handleClearFilters}
                    className="mt-3 text-sm text-upstream-600 hover:underline"
                  >
                    Clear all filters
                  </button>
                )}
              </div>
            ) : (
              <>
                {/* Toolbar: count + sort */}
                <div className="mb-4 flex items-center justify-between">
                  <p className="text-sm text-gray-500">
                    {productsData?.count ?? products.length} products
                  </p>
                  <select
                    value={sort}
                    onChange={(e) => handleSortChange(e.target.value)}
                    className="rounded-md border border-gray-300 bg-white px-3 py-1.5 text-sm text-gray-700 focus:border-upstream-500 focus:outline-none focus:ring-1 focus:ring-upstream-500"
                    aria-label="Sort products"
                  >
                    {SORT_OPTIONS.map((opt) => (
                      <option key={opt.value} value={opt.value}>
                        {opt.label}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-3 xl:grid-cols-4">
                  {products.map((product) => (
                    <ProductCard
                      key={product.id}
                      product={product}
                      onQuickAdd={(skuId) => addToCart.mutate({ skuId })}
                      isAdding={addToCart.isPending}
                    />
                  ))}
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </>
  );
}
