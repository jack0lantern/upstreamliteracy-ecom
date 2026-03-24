import { Helmet } from 'react-helmet-async';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { productsApi } from '@/lib/api/products';
import { categoriesApi } from '@/lib/api/categories';
import { queryKeys } from '@/lib/queryKeys';
import { ProductGridSkeleton } from '@/components/ui/LoadingSkeleton';
import type { ProductListItem } from '@/types';

function ProductCard({ product }: { product: ProductListItem }) {
  const imageUrl = product.primary_image?.image ?? null;

  return (
    <Link
      to={`/shop/product/${product.slug}`}
      className="group flex flex-col overflow-hidden rounded-lg border border-gray-200 bg-white shadow-sm transition-shadow hover:shadow-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-upstream-500"
    >
      {/* Image */}
      <div className="aspect-square overflow-hidden bg-gray-100">
        {imageUrl ? (
          <img
            src={imageUrl}
            alt={product.primary_image?.alt_text || product.title}
            className="h-full w-full object-cover transition-transform duration-300 group-hover:scale-105"
            loading="lazy"
          />
        ) : (
          <div className="flex h-full w-full items-center justify-center text-gray-300">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className="h-16 w-16"
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

      {/* Details */}
      <div className="flex flex-1 flex-col p-4">
        {product.category && (
          <p className="text-xs font-medium uppercase tracking-wide text-upstream-600">
            {product.category.name}
          </p>
        )}
        <h3 className="mt-1 flex-1 text-sm font-semibold leading-tight text-gray-900 group-hover:text-upstream-700">
          {product.title}
        </h3>
        <div className="mt-2 flex items-baseline gap-2">
          <span className="text-base font-bold text-gray-900">${product.price}</span>
          {product.compare_at_price && (
            <span className="text-sm text-gray-400 line-through">${product.compare_at_price}</span>
          )}
        </div>
        {!product.is_in_stock && (
          <span className="mt-1 text-xs text-red-500">Out of stock</span>
        )}
      </div>
    </Link>
  );
}

export default function ShopPage() {
  const { data: productsData, isLoading: productsLoading, isError } = useQuery({
    queryKey: queryKeys.products.list(),
    queryFn: () => productsApi.getProducts({ page_size: 24 }),
  });

  const { data: categories } = useQuery({
    queryKey: queryKeys.categories.list(),
    queryFn: categoriesApi.getCategories,
  });

  const products = productsData?.results ?? [];

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
                    className="block rounded px-2 py-1.5 text-sm text-gray-600 hover:bg-gray-100 hover:text-gray-900"
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
                <p className="mb-4 text-sm text-gray-500">
                  {productsData?.count ?? products.length} products
                </p>
                <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-3 xl:grid-cols-4">
                  {products.map((product) => (
                    <ProductCard key={product.id} product={product} />
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
