import { useParams, Link, useSearchParams } from 'react-router-dom';
import { Helmet } from 'react-helmet-async';
import { useQuery } from '@tanstack/react-query';
import { categoriesApi } from '@/lib/api/categories';
import { productsApi } from '@/lib/api/products';
import { queryKeys } from '@/lib/queryKeys';
import LoadingSkeleton, { ProductGridSkeleton } from '@/components/ui/LoadingSkeleton';
import { ProductCard } from '@/components/product/ProductCard';
import { useAddToCart } from '@/hooks/useAddToCart';

const SORT_OPTIONS = [
  { label: 'Featured', value: '' },
  { label: 'Price: Low to High', value: 'base_price' },
  { label: 'Price: High to Low', value: '-base_price' },
  { label: 'Newest', value: '-created_at' },
  { label: 'Name A–Z', value: 'title' },
] as const;

export default function CategoryPage() {
  const { slug = '' } = useParams<{ slug: string }>();
  const [searchParams, setSearchParams] = useSearchParams();
  const sort = searchParams.get('sort') ?? '';

  const { data: category, isLoading: catLoading, isError: catError } = useQuery({
    queryKey: queryKeys.categories.detail(slug),
    queryFn: () => categoriesApi.getCategory(slug),
    enabled: !!slug,
    retry: false,
  });

  const { data: productsData, isLoading: productsLoading } = useQuery({
    queryKey: queryKeys.products.list({ category: slug, page_size: 24, ordering: sort || undefined }),
    queryFn: () => productsApi.getProducts({ category: slug, page_size: 24, ordering: sort || undefined }),
    enabled: !!slug,
  });

  const addToCart = useAddToCart();
  const products = productsData?.results ?? [];
  const pageTitle = category?.name ?? 'Category';

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
        <title>{pageTitle} – Upstream Literacy</title>
        {category?.description && (
          <meta name="description" content={category.description} />
        )}
      </Helmet>

      <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        {/* 404 for invalid category */}
        {catError && !catLoading && (
          <div className="py-16 text-center">
            <p className="text-sm font-semibold uppercase tracking-wide text-upstream-600">404</p>
            <h1 className="mt-2 text-2xl font-bold text-gray-900">Category not found</h1>
            <p className="mt-2 text-gray-500">The category you&rsquo;re looking for doesn&rsquo;t exist.</p>
            <Link to="/shop" className="btn-primary mt-6 inline-flex">Back to Shop</Link>
          </div>
        )}

        {!catError && (
          <>
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
                {/* Toolbar: count + sort */}
                <div className="mb-4 flex items-center justify-between">
                  <p className="text-sm text-gray-500">{products.length} products</p>
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

                <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 xl:grid-cols-4">
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
          </>
        )}
      </div>
    </>
  );
}
