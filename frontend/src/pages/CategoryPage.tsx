import { useParams, Link } from 'react-router-dom';
import { Helmet } from 'react-helmet-async';
import { useQuery } from '@tanstack/react-query';
import { categoriesApi } from '@/lib/api/categories';
import { productsApi } from '@/lib/api/products';
import { queryKeys } from '@/lib/queryKeys';
import LoadingSkeleton, { ProductGridSkeleton } from '@/components/ui/LoadingSkeleton';
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
      <div className="flex flex-1 flex-col p-4">
        <h3 className="flex-1 text-sm font-semibold leading-tight text-gray-900 group-hover:text-upstream-700">
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

export default function CategoryPage() {
  const { slug = '' } = useParams<{ slug: string }>();

  const { data: category, isLoading: catLoading } = useQuery({
    queryKey: queryKeys.categories.detail(slug),
    queryFn: () => categoriesApi.getCategory(slug),
    enabled: !!slug,
  });

  const { data: productsData, isLoading: productsLoading } = useQuery({
    queryKey: queryKeys.products.list({ category: slug }),
    queryFn: () => productsApi.getProducts({ category: slug, page_size: 24 }),
    enabled: !!slug,
  });

  const products = productsData?.results ?? [];
  const pageTitle = category?.name ?? 'Category';

  return (
    <>
      <Helmet>
        <title>{pageTitle} – Upstream Literacy</title>
        {category?.description && (
          <meta name="description" content={category.description} />
        )}
      </Helmet>

      <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        {/* Breadcrumb */}
        <nav aria-label="Breadcrumb" className="mb-6 flex items-center gap-2 text-sm text-gray-500">
          <Link to="/shop" className="hover:text-gray-700">
            Shop
          </Link>
          <span aria-hidden="true">/</span>
          {catLoading ? (
            <div className="h-4 w-24 animate-pulse rounded bg-gray-200" />
          ) : (
            <span className="text-gray-900">{pageTitle}</span>
          )}
        </nav>

        {/* Heading */}
        <div className="mb-8">
          {catLoading ? (
            <LoadingSkeleton lines={2} className="max-w-sm" />
          ) : (
            <>
              <h1 className="text-3xl font-bold tracking-tight text-gray-900">{pageTitle}</h1>
              {category?.description && (
                <p className="mt-2 text-gray-600">{category.description}</p>
              )}
            </>
          )}
        </div>

        {/* Sub-categories */}
        {category?.children && category.children.length > 0 && (
          <div className="mb-8 flex flex-wrap gap-2">
            {category.children.map((child) => (
              <Link
                key={child.id}
                to={`/shop/category/${child.slug}`}
                className="rounded-full border border-gray-300 px-4 py-1.5 text-sm text-gray-600 transition-colors hover:border-upstream-500 hover:text-upstream-700"
              >
                {child.name}
                <span className="ml-1.5 text-xs text-gray-400">({child.product_count})</span>
              </Link>
            ))}
          </div>
        )}

        {/* Products */}
        {productsLoading ? (
          <ProductGridSkeleton count={8} />
        ) : products.length === 0 ? (
          <div className="rounded-lg border border-gray-200 p-12 text-center">
            <p className="text-gray-500">No products in this category yet.</p>
            <Link to="/shop" className="mt-4 inline-block text-sm text-upstream-600 hover:underline">
              Browse all products
            </Link>
          </div>
        ) : (
          <>
            <p className="mb-4 text-sm text-gray-500">{productsData?.count ?? products.length} products</p>
            <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 xl:grid-cols-4">
              {products.map((product) => (
                <ProductCard key={product.id} product={product} />
              ))}
            </div>
          </>
        )}
      </div>
    </>
  );
}
