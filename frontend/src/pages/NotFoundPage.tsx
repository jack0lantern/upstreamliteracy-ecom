import { Link } from 'react-router-dom';
import { Helmet } from 'react-helmet-async';
import { useQuery } from '@tanstack/react-query';
import { categoriesApi } from '@/lib/api/categories';
import { queryKeys } from '@/lib/queryKeys';
import SearchBar from '@/components/search/SearchBar';

export default function NotFoundPage() {
  const { data: categories } = useQuery({
    queryKey: queryKeys.categories.list(),
    queryFn: categoriesApi.getCategories,
    staleTime: 5 * 60 * 1000,
  });

  return (
    <>
      <Helmet>
        <title>Page Not Found – Upstream Literacy</title>
      </Helmet>

      <div className="mx-auto max-w-7xl px-4 py-24 text-center sm:px-6 lg:px-8">
        <p className="text-sm font-semibold uppercase tracking-wide text-upstream-600">404</p>
        <h1 className="mt-2 text-3xl font-bold tracking-tight text-gray-900 sm:text-4xl">
          Page not found
        </h1>
        <p className="mt-4 text-gray-500">
          Sorry, we couldn&rsquo;t find the page you&rsquo;re looking for.
        </p>

        {/* Search bar */}
        <div className="mx-auto mt-8 max-w-md">
          <SearchBar />
        </div>

        {/* Category links */}
        {categories && categories.length > 0 && (
          <div className="mt-8">
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

        <div className="mt-8 flex items-center justify-center gap-4">
          <Link to="/shop" className="btn-primary">
            Browse Products
          </Link>
          <Link to="/" className="text-sm font-medium text-upstream-600 hover:underline">
            Go Home
          </Link>
        </div>
      </div>
    </>
  );
}
