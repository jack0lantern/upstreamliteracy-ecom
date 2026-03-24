import { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Helmet } from 'react-helmet-async';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { productsApi } from '@/lib/api/products';
import { cartApi } from '@/lib/api/cart';
import { queryKeys } from '@/lib/queryKeys';
import LoadingSkeleton from '@/components/ui/LoadingSkeleton';
import { useUIStore } from '@/stores/uiStore';
import { trackEvent } from '@/lib/analytics';

export default function ProductDetailPage() {
  const { slug = '' } = useParams<{ slug: string }>();
  const addToast = useUIStore((s) => s.addToast);
  const queryClient = useQueryClient();

  const [selectedSkuId, setSelectedSkuId] = useState<number | null>(null);
  const [quantity, setQuantity] = useState(1);
  const [activeImageIndex, setActiveImageIndex] = useState(0);

  const { data: product, isLoading, isError } = useQuery({
    queryKey: queryKeys.products.detail(slug),
    queryFn: () => productsApi.getProduct(slug),
    enabled: !!slug,
  });

  const addItemMutation = useMutation({
    mutationFn: ({ skuId, qty }: { skuId: number; qty: number }) =>
      cartApi.addItem(skuId, qty),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.cart.current() });
      addToast('Added to cart!', 'success');
      trackEvent('add_to_cart', {
        product_slug: slug,
        sku_id: selectedSkuId ?? undefined,
        quantity,
      });
    },
    onError: () => {
      addToast('Failed to add item to cart. Please try again.', 'error');
    },
  });

  function handleAddToCart() {
    const skus = product?.sku_set ?? [];
    const targetSku = selectedSkuId
      ? skus.find((s) => s.id === selectedSkuId)
      : skus.find((s) => s.is_available) ?? skus[0];

    if (!targetSku) {
      addToast('Please select a variant.', 'warning');
      return;
    }

    addItemMutation.mutate({ skuId: targetSku.id, qty: quantity });
  }

  if (isLoading) {
    return (
      <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        <div className="grid gap-12 lg:grid-cols-2">
          <div className="aspect-square animate-pulse rounded-xl bg-gray-200" />
          <div className="space-y-4">
            <LoadingSkeleton lines={5} />
          </div>
        </div>
      </div>
    );
  }

  if (isError || !product) {
    return (
      <div className="mx-auto max-w-7xl px-4 py-16 text-center sm:px-6 lg:px-8">
        <h1 className="text-2xl font-bold text-gray-900">Product not found</h1>
        <p className="mt-2 text-gray-500">
          The product you're looking for doesn't exist or has been removed.
        </p>
        <Link to="/shop" className="btn-primary mt-6 inline-flex">
          Back to Shop
        </Link>
      </div>
    );
  }

  const images = product.images?.length ? product.images : product.primary_image ? [product.primary_image] : [];
  const activeImage = images[activeImageIndex];
  const skus = product.sku_set ?? [];
  const hasVariants = skus.length > 1;
  const currentSku = selectedSkuId
    ? skus.find((s) => s.id === selectedSkuId)
    : skus[0];
  const isInStock = currentSku ? currentSku.is_available : product.is_in_stock;
  const displayPrice = currentSku?.price ?? product.price;

  return (
    <>
      <Helmet>
        <title>{product.meta_title || product.title} – Upstream Literacy</title>
        {product.meta_description && (
          <meta name="description" content={product.meta_description} />
        )}
      </Helmet>

      <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        {/* Breadcrumb */}
        <nav aria-label="Breadcrumb" className="mb-6 flex items-center gap-2 text-sm text-gray-500">
          <Link to="/shop" className="hover:text-gray-700">Shop</Link>
          <span aria-hidden="true">/</span>
          {product.category && (
            <Link to={`/shop/category/${product.category.slug}`} className="hover:text-gray-700">
              {product.category.name}
            </Link>
          )}
          <span aria-hidden="true">/</span>
          <span className="truncate text-gray-900">{product.title}</span>
        </nav>

        <div className="grid gap-10 lg:grid-cols-2">
          {/* Images */}
          <div>
            <div className="overflow-hidden rounded-xl bg-gray-100">
              {activeImage ? (
                <img
                  src={activeImage.image}
                  alt={activeImage.alt_text || product.title}
                  className="h-full w-full object-contain"
                />
              ) : (
                <div className="flex aspect-square items-center justify-center text-gray-300">
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    className="h-24 w-24"
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

            {images.length > 1 && (
              <div className="mt-4 flex gap-2 overflow-x-auto pb-1">
                {images.map((img, idx) => (
                  <button
                    key={img.id}
                    type="button"
                    onClick={() => setActiveImageIndex(idx)}
                    className={`h-16 w-16 flex-shrink-0 overflow-hidden rounded-lg border-2 transition-colors ${
                      idx === activeImageIndex
                        ? 'border-upstream-500'
                        : 'border-transparent hover:border-gray-300'
                    }`}
                    aria-label={`View image ${idx + 1}`}
                    aria-pressed={idx === activeImageIndex}
                  >
                    <img
                      src={img.image}
                      alt={img.alt_text || `${product.title} image ${idx + 1}`}
                      className="h-full w-full object-cover"
                    />
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Info */}
          <div className="flex flex-col">
            <div className="mb-1 flex items-center gap-2">
              {product.category && (
                <Link
                  to={`/shop/category/${product.category.slug}`}
                  className="text-xs font-semibold uppercase tracking-wide text-upstream-600 hover:text-upstream-700"
                >
                  {product.category.name}
                </Link>
              )}
              <span className="rounded bg-gray-100 px-2 py-0.5 text-xs text-gray-500 capitalize">
                {product.product_type}
              </span>
            </div>

            <h1 className="text-2xl font-bold tracking-tight text-gray-900 sm:text-3xl">
              {product.title}
            </h1>

            <div className="mt-3 flex items-baseline gap-3">
              <span className="text-2xl font-bold text-gray-900">${displayPrice}</span>
              {product.compare_at_price && (
                <span className="text-lg text-gray-400 line-through">${product.compare_at_price}</span>
              )}
            </div>

            {product.short_description && (
              <p className="mt-4 text-gray-600 leading-relaxed">{product.short_description}</p>
            )}

            {/* SKU variants */}
            {hasVariants && (
              <div className="mt-6">
                <h3 className="mb-2 text-sm font-medium text-gray-700">Options</h3>
                <div className="flex flex-wrap gap-2">
                  {skus.map((sku) => (
                    <button
                      key={sku.id}
                      type="button"
                      onClick={() => setSelectedSkuId(sku.id)}
                      disabled={!sku.is_available}
                      className={`rounded-md border px-3 py-1.5 text-sm font-medium transition-colors ${
                        selectedSkuId === sku.id || (!selectedSkuId && sku === skus[0])
                          ? 'border-upstream-500 bg-upstream-50 text-upstream-700'
                          : 'border-gray-300 text-gray-700 hover:border-gray-400'
                      } disabled:cursor-not-allowed disabled:opacity-40`}
                    >
                      {Object.values(sku.attributes).join(' / ')}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Quantity + Add to cart */}
            <div className="mt-6 flex items-center gap-3">
              <div className="flex items-center rounded-md border border-gray-300">
                <button
                  type="button"
                  onClick={() => setQuantity((q) => Math.max(1, q - 1))}
                  className="px-3 py-2 text-gray-600 hover:text-gray-900 disabled:opacity-40"
                  aria-label="Decrease quantity"
                  disabled={quantity <= 1}
                >
                  -
                </button>
                <span className="min-w-[2.5rem] px-2 py-2 text-center text-sm font-medium">
                  {quantity}
                </span>
                <button
                  type="button"
                  onClick={() => setQuantity((q) => q + 1)}
                  className="px-3 py-2 text-gray-600 hover:text-gray-900"
                  aria-label="Increase quantity"
                >
                  +
                </button>
              </div>

              <button
                type="button"
                onClick={handleAddToCart}
                disabled={!isInStock || addItemMutation.isPending}
                className="btn-primary flex-1"
              >
                {addItemMutation.isPending
                  ? 'Adding…'
                  : !isInStock
                    ? 'Out of Stock'
                    : 'Add to Cart'}
              </button>
            </div>

            {/* Specs */}
            {product.format_specs && product.format_specs.length > 0 && (
              <dl className="mt-8 divide-y divide-gray-100 rounded-lg border border-gray-200">
                {product.format_specs.map((spec) => (
                  <div key={spec.label} className="flex gap-4 px-4 py-3">
                    <dt className="w-32 flex-shrink-0 text-sm text-gray-500">{spec.label}</dt>
                    <dd className="text-sm font-medium text-gray-900">{spec.value}</dd>
                  </div>
                ))}
              </dl>
            )}

            {/* Skill tags */}
            {product.skill_tags && product.skill_tags.length > 0 && (
              <div className="mt-6 flex flex-wrap gap-2">
                {product.skill_tags.map((tag) => (
                  <span
                    key={tag}
                    className="rounded-full bg-upstream-50 px-3 py-1 text-xs font-medium text-upstream-700"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Full description */}
        {product.description && (
          <div className="mt-16">
            <h2 className="mb-4 text-xl font-semibold text-gray-900">About this product</h2>
            <div
              className="prose max-w-none text-gray-600"
              dangerouslySetInnerHTML={{ __html: product.description }}
            />
          </div>
        )}

        {/* Related products */}
        {product.related_products && product.related_products.length > 0 && (
          <div className="mt-16">
            <h2 className="mb-6 text-xl font-semibold text-gray-900">You might also like</h2>
            <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
              {product.related_products.slice(0, 4).map((rel) => (
                <Link
                  key={rel.id}
                  to={`/shop/product/${rel.slug}`}
                  className="group overflow-hidden rounded-lg border border-gray-200 bg-white p-4 shadow-sm transition-shadow hover:shadow-md"
                >
                  {rel.primary_image && (
                    <img
                      src={rel.primary_image.image}
                      alt={rel.primary_image.alt_text || rel.title}
                      className="mb-3 aspect-square w-full rounded object-cover"
                      loading="lazy"
                    />
                  )}
                  <p className="text-sm font-medium text-gray-900 group-hover:text-upstream-700">
                    {rel.title}
                  </p>
                  <p className="mt-1 text-sm font-bold text-gray-900">${rel.price}</p>
                </Link>
              ))}
            </div>
          </div>
        )}
      </div>
    </>
  );
}
