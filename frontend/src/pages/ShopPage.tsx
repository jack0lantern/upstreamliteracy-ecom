import { Helmet } from 'react-helmet-async';
import { useQuery } from '@tanstack/react-query';
import { Link, useSearchParams } from 'react-router-dom';
import { productsApi } from '@/lib/api/products';
import { categoriesApi } from '@/lib/api/categories';
import { queryKeys } from '@/lib/queryKeys';
import { ProductGridSkeleton } from '@/components/ui/LoadingSkeleton';
import { ProductCard } from '@/components/product/ProductCard';
import { useAddToCart } from '@/hooks/useAddToCart';

const SORT_OPTIONS = [
  { label: 'Featured', value: '' },
  { label: 'Price: Low to High', value: 'base_price' },
  { label: 'Price: High to Low', value: '-base_price' },
  { label: 'Newest', value: '-created_at' },
  { label: 'Name A–Z', value: 'title' },
] as const;

export default function ShopPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const sort = searchParams.get('sort') ?? '';

  const { data: productsData, isLoading: productsLoading, isError } = useQuery({
    queryKey: queryKeys.products.list({ page_size: 24, ordering: sort || undefined }),
    queryFn: () => productsApi.getProducts({ page_size: 24, ordering: sort || undefined }),
  });

  const { data: categories } = useQuery({
    queryKey: queryKeys.categories.list(),
    queryFn: categoriesApi.getCategories,
  });

  const addToCart = useAddToCart();
  const products = productsData?.results ?? [];

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
          {/* Sidebar – categories */}
          <aside className="w-full lg:w-56 lg:flex-shrink-0" aria-label="Filter by category">
            <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-gray-700">
              Categories
            </h2>
            {categories && categories.length > 0 ? (
              <ul className="space-y-1">
                <li>
                  <Link
                    to="/shop"
                    className="block rounded px-2 py-1.5 text-sm font-medium text-upstream-700 bg-upstream-50"
                  >
                    All Products
                  </Link>
                </li>
                {categories.map((cat) => (
                  <li key={cat.id}>
                    <Link
                      to={`/shop/category/${cat.slug}`}
                      className="flex items-center justify-between rounded px-2 py-1.5 text-sm text-gray-600 hover:bg-gray-100 hover:text-gray-900"
                    >
                      <span>{cat.name}</span>
                      <span className="text-xs text-gray-400">{cat.product_count}</span>
                    </Link>
                  </li>
                ))}
              </ul>
            ) : (
              <div className="animate-pulse space-y-2">
                {[1, 2, 3, 4].map((i) => (
                  <div key={i} className="h-8 rounded bg-gray-200" />
                ))}
              </div>
            )}
          </aside>

          {/* Product grid */}
          <div className="flex-1">
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
                <p className="text-gray-500">No products found.</p>
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
