import { useSearchParams, Link } from 'react-router-dom';
import { Helmet } from 'react-helmet-async';
import { useQuery, keepPreviousData } from '@tanstack/react-query';
import { productsApi } from '@/lib/api/products';
import { queryKeys } from '@/lib/queryKeys';
import { ProductGridSkeleton } from '@/components/ui/LoadingSkeleton';
import type { ProductListItem } from '@/types';

function ProductCard({ product }: { product: ProductListItem }) {
  return (
    <Link
      to={`/shop/product/${product.slug}`}
      className="group flex flex-col overflow-hidden rounded-lg border border-gray-200 bg-white shadow-sm transition-shadow hover:shadow-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-upstream-500"
    >
      <div className="aspect-square overflow-hidden bg-gray-100">
        {product.primary_image ? (
          <img
            src={product.primary_image.image}
            alt={product.primary_image.alt_text || product.title}
            className="h-full w-full object-cover transition-transform duration-300 group-hover:scale-105"
            loading="lazy"
          />
        ) : (
          <div className="flex h-full w-full items-center justify-center text-gray-300">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className="h-12 w-12"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={1}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="m2.25 15.75 5.159-5.159a2.25 2.25 0 0 1 3.182 0l5.159 5.159m-1.5-1.5 1.409-1.409a2.25 2.25 0 0 1 3.182 0l2.909 2.909m-18 3.75h16.5a1.5 1.5 0 0 0 1.5-1.5V6a1.5 1.5 0 0 0-1.5-1.5H3.75A1.5 1.5 0 0 0 2.25 6v12a1.5 1.5 0 0 0 1.5 1.5Zm10.5-11.25h.008v.008h-.008V8.25Zm.375 0a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Z"
              />
            </svg>
          </div>
        )}
      </div>
      <div className="flex flex-1 flex-col p-4">
        <p className="text-xs font-medium uppercase tracking-wide text-upstream-600">
          {product.category?.name}
        </p>
        <h3 className="mt-1 flex-1 text-sm font-semibold leading-tight text-gray-900 group-hover:text-upstream-700">
          {product.title}
        </h3>
        <div className="mt-2 flex items-baseline gap-2">
          <span className="text-base font-bold text-gray-900">${product.price}</span>
          {product.compare_at_price && (
            <span className="text-sm text-gray-400 line-through">${product.compare_at_price}</span>
          )}
        </div>
      </div>
    </Link>
  );
}

export default function SearchResultsPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const query = searchParams.get('q') ?? '';
  const page = parseInt(searchParams.get('page') ?? '1', 10);

  const { data, isLoading, isError } = useQuery({
    queryKey: queryKeys.search.results(query, page),
    queryFn: () => productsApi.getProducts({ search: query, page }),
    enabled: query.length >= 1,
    placeholderData: keepPreviousData,
  });

  const products = data?.results ?? [];
  const totalCount = data?.count ?? 0;
  const hasNextPage = !!data?.next;
  const hasPrevPage = !!data?.previous;

  function goToPage(p: number) {
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev);
      next.set('page', String(p));
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
          <h1 className="text-2xl font-bold tracking-tight text-gray-900">
            {query ? (
              <>
                Results for{' '}
                <span className="text-upstream-700">&ldquo;{query}&rdquo;</span>
              </>
            ) : (
              'Search'
            )}
          </h1>
          {!isLoading && query && (
            <p className="mt-1 text-sm text-gray-500">
              {totalCount} result{totalCount !== 1 ? 's' : ''}
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
          <div className="rounded-xl border border-gray-200 bg-gray-50 py-16 text-center">
            <p className="text-lg font-medium text-gray-600">No results found</p>
            <p className="mt-1 text-sm text-gray-400">
              Try different keywords or browse all products.
            </p>
            <Link to="/shop" className="btn-primary mt-6 inline-flex">
              Browse All Products
            </Link>
          </div>
        ) : (
          <>
            <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
              {products.map((product) => (
                <ProductCard key={product.id} product={product} />
              ))}
            </div>

            {/* Pagination */}
            {(hasPrevPage || hasNextPage) && (
              <div className="mt-8 flex items-center justify-center gap-4">
                <button
                  type="button"
                  onClick={() => goToPage(page - 1)}
                  disabled={!hasPrevPage}
                  className="btn-secondary disabled:opacity-40"
                >
                  Previous
                </button>
                <span className="text-sm text-gray-500">Page {page}</span>
                <button
                  type="button"
                  onClick={() => goToPage(page + 1)}
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
