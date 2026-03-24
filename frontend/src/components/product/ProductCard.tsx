import { Link, useNavigate } from 'react-router-dom';
import type { ProductListItem } from '@/types';

interface ProductCardProps {
  product: ProductListItem;
  onQuickAdd?: (skuId: number) => void;
  isAdding?: boolean;
}

export function ProductCard({ product, onQuickAdd, isAdding }: ProductCardProps) {
  const navigate = useNavigate();
  const imageUrl = product.primary_image?.image ?? null;
  const detailPath = `/shop/product/${product.slug}`;

  const canQuickAdd =
    product.is_in_stock && product.sku_count === 1 && product.default_sku_id != null;
  const hasMultipleSkus = product.sku_count > 1;

  function handleButtonClick(e: React.MouseEvent) {
    e.preventDefault();
    e.stopPropagation();

    if (canQuickAdd && onQuickAdd) {
      onQuickAdd(product.default_sku_id!);
    } else {
      navigate(detailPath);
    }
  }

  return (
    <div className="group flex flex-col overflow-hidden rounded-lg border border-gray-200 bg-white shadow-sm transition-shadow hover:shadow-md">
      <Link
        to={detailPath}
        className="flex flex-1 flex-col focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-upstream-500"
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
        <div className="flex flex-1 flex-col p-4 pb-2">
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
              <span className="text-sm text-gray-400 line-through">
                ${product.compare_at_price}
              </span>
            )}
          </div>
          {!product.is_in_stock && (
            <span className="mt-1 text-xs text-red-500">Out of stock</span>
          )}
        </div>
      </Link>

      {/* Quick add button */}
      <div className="px-4 pb-4">
        {!product.is_in_stock ? (
          <button
            type="button"
            disabled
            className="w-full rounded-md bg-gray-100 px-3 py-2 text-sm font-medium text-gray-400 cursor-not-allowed"
          >
            Out of Stock
          </button>
        ) : (
          <button
            type="button"
            onClick={handleButtonClick}
            disabled={isAdding}
            className="w-full rounded-md border border-upstream-600 px-3 py-2 text-sm font-medium text-upstream-600 transition-colors hover:bg-upstream-50 disabled:opacity-50"
          >
            {isAdding
              ? 'Adding...'
              : hasMultipleSkus
                ? 'Select Options'
                : 'Add to Cart'}
          </button>
        )}
      </div>
    </div>
  );
}
