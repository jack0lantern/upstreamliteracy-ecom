import { useSearchParams, Link } from 'react-router-dom';
import { Helmet } from 'react-helmet-async';
import { useQuery, keepPreviousData } from '@tanstack/react-query';
import { productsApi } from '@/lib/api/products';
import { categoriesApi } from '@/lib/api/categories';
import { queryKeys } from '@/lib/queryKeys';
import { ProductGridSkeleton } from '@/components/ui/LoadingSkeleton';
import { ProductCard } from '@/components/product/ProductCard';
import { useAddToCart } from '@/hooks/useAddToCart';

const SORT_OPTIONS = [
  { label: 'Relevance', value: '' },
  { label: 'Price: Low to High', value: 'base_price' },
  { label: 'Price: High to Low', value: '-base_price' },
  { label: 'Newest', value: '-created_at' },
  { label: 'Name A–Z', value: 'title' },
] as const;

export default function SearchResultsPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const query = searchParams.get('q') ?? '';
  const page = parseInt(searchParams.get('page') ?? '1', 10);
  const sort = searchParams.get('sort') ?? '';

  const { data, isLoading, isError } = useQuery({
    queryKey: queryKeys.search.results(query, page),
    queryFn: () => productsApi.getProducts({ search: query, page, ordering: sort || undefined }),
    enabled: query.length >= 1,
    placeholderData: keepPreviousData,
  });

  const { data: categories } = useQuery({
    queryKey: queryKeys.categories.list(),
    queryFn: categoriesApi.getCategories,
    staleTime: 5 * 60 * 1000,
  });

  const addToCart = useAddToCart();
  const products = data?.results ?? [];
  const resultCount = products.length;
  const hasNextPage = !!data?.next;
  const hasPrevPage = !!data?.previous;

  function setParam(key: string, value: string) {
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev);
      if (value) {
        next.set(key, value);
      } else {
        next.delete(key);
      }
      // Reset page when changing sort
      if (key === 'sort') next.delete('page');
      return next;
    });
  }

  return (
    <>
      <Helmet>
        <title>
          {query ? `Search: "${query}"` : 'Search'} – Upstream Literacy
        </title>
      </Helmet>

      <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        <div className="mb-6">
          <h1 className="truncate text-2xl font-bold tracking-tight text-gray-900">
            {query ? (
              <>
                Results for{' '}
                <span className="text-upstream-700">&ldquo;{query.length > 80 ? query.slice(0, 80) + '…' : query}&rdquo;</span>
              </>
            ) : (
              'Search'
            )}
          </h1>
          {!isLoading && query && resultCount > 0 && (
            <p className="mt-1 text-sm text-gray-500">
              {resultCount} result{resultCount !== 1 ? 's' : ''}{hasNextPage ? '+' : ''}
            </p>
          )}
        </div>

        {!query ? (
          <div className="rounded-xl border border-gray-200 bg-gray-50 py-16 text-center">
            <p className="text-gray-500">Enter a search term to find products.</p>
          </div>
        ) : isLoading ? (
          <ProductGridSkeleton count={8} />
        ) : isError ? (
          <div className="rounded-lg border border-red-200 bg-red-50 p-6 text-center">
            <p className="text-sm text-red-700">
              Search failed. Please try again.
            </p>
          </div>
        ) : products.length === 0 ? (
          /* Improved no-results state */
          <div className="rounded-xl border border-gray-200 bg-gray-50 py-12 px-6 text-center">
            <svg xmlns="http://www.w3.org/2000/svg" className="mx-auto mb-4 h-12 w-12 text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1}>
              <path strokeLinecap="round" strokeLinejoin="round" d="m21 21-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 5.196a7.5 7.5 0 0 0 10.607 10.607Z" />
            </svg>
            <p className="text-lg font-medium text-gray-600">No results found</p>
            <p className="mx-auto mt-2 max-w-md text-sm text-gray-400">
              Try checking your spelling, using more general terms, or browsing by category below.
            </p>

            {/* Category suggestions */}
            {categories && categories.length > 0 && (
              <div className="mt-6">
                <p className="mb-3 text-sm font-medium text-gray-500">Browse by category</p>
                <div className="flex flex-wrap justify-center gap-2">
                  {categories.map((cat) => (
                    <Link
                      key={cat.id}
                      to={`/shop/category/${cat.slug}`}
                      className="rounded-full border border-gray-300 px-4 py-1.5 text-sm text-gray-600 transition-colors hover:border-upstream-500 hover:text-upstream-700"
                    >
                      {cat.name}
                    </Link>
                  ))}
                </div>
              </div>
            )}

            <Link to="/shop" className="btn-primary mt-6 inline-flex">
              Browse All Products
            </Link>
          </div>
        ) : (
          <>
            {/* Toolbar: sort */}
            <div className="mb-4 flex items-center justify-end">
              <select
                value={sort}
                onChange={(e) => setParam('sort', e.target.value)}
                className="rounded-md border border-gray-300 bg-white px-3 py-1.5 text-sm text-gray-700 focus:border-upstream-500 focus:outline-none focus:ring-1 focus:ring-upstream-500"
                aria-label="Sort results"
              >
                {SORT_OPTIONS.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>

            <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
              {products.map((product) => (
                <ProductCard
                  key={product.id}
                  product={product}
                  onQuickAdd={(skuId) => addToCart.mutate({ skuId })}
                  isAdding={addToCart.isPending}
                />
              ))}
            </div>

            {/* Pagination */}
            {(hasPrevPage || hasNextPage) && (
              <div className="mt-8 flex items-center justify-center gap-4">
                <button
                  type="button"
                  onClick={() => setParam('page', String(page - 1))}
                  disabled={!hasPrevPage}
                  className="btn-secondary disabled:opacity-40"
                >
                  Previous
                </button>
                <span className="text-sm text-gray-500">Page {page}</span>
                <button
                  type="button"
                  onClick={() => setParam('page', String(page + 1))}
                  disabled={!hasNextPage}
                  className="btn-secondary disabled:opacity-40"
                >
                  Next
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </>
  );
}
