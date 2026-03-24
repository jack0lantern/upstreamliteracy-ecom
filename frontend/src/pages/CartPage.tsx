import { Helmet } from 'react-helmet-async';
import { Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { cartApi } from '@/lib/api/cart';
import { queryKeys } from '@/lib/queryKeys';
import LoadingSkeleton from '@/components/ui/LoadingSkeleton';
import { useUIStore } from '@/stores/uiStore';
import { trackEvent } from '@/lib/analytics';
import type { CartItem } from '@/types';

function CartLineItem({
  item,
  onRemove,
  onUpdateQty,
  isPending,
}: {
  item: CartItem;
  onRemove: (id: number) => void;
  onUpdateQty: (id: number, qty: number) => void;
  isPending: boolean;
}) {
  const product = item.sku.product;
  const image = product.primary_image;

  return (
    <li className="flex gap-4 py-4">
      {/* Thumbnail */}
      <div className="h-20 w-20 flex-shrink-0 overflow-hidden rounded-lg bg-gray-100">
        {image ? (
          <img
            src={image.image}
            alt={image.alt_text || product.title}
            className="h-full w-full object-cover"
          />
        ) : (
          <div className="flex h-full w-full items-center justify-center text-gray-300">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className="h-8 w-8"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={1.5}
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
      <div className="flex flex-1 flex-col">
        <div className="flex items-start justify-between gap-2">
          <Link
            to={`/shop/product/${product.slug}`}
            className="text-sm font-medium text-gray-900 hover:text-upstream-700"
          >
            {product.title}
          </Link>
          <span className="flex-shrink-0 text-sm font-semibold text-gray-900">
            ${item.line_total}
          </span>
        </div>

        {Object.keys(item.sku.attributes).length > 0 && (
          <p className="mt-0.5 text-xs text-gray-500">
            {Object.entries(item.sku.attributes)
              .map(([k, v]) => `${k}: ${v}`)
              .join(', ')}
          </p>
        )}

        <p className="mt-0.5 text-xs text-gray-400">Unit: ${item.unit_price}</p>

        <div className="mt-2 flex items-center gap-3">
          <div className="flex items-center rounded border border-gray-300">
            <button
              type="button"
              onClick={() => onUpdateQty(item.id, item.quantity - 1)}
              disabled={isPending || item.quantity <= 1}
              className="px-2 py-1 text-gray-600 hover:text-gray-900 disabled:opacity-40"
              aria-label="Decrease quantity"
            >
              -
            </button>
            <span className="min-w-[1.75rem] px-1 py-1 text-center text-sm">
              {item.quantity}
            </span>
            <button
              type="button"
              onClick={() => onUpdateQty(item.id, item.quantity + 1)}
              disabled={isPending}
              className="px-2 py-1 text-gray-600 hover:text-gray-900 disabled:opacity-40"
              aria-label="Increase quantity"
            >
              +
            </button>
          </div>
          <button
            type="button"
            onClick={() => onRemove(item.id)}
            disabled={isPending}
            className="text-xs text-red-500 hover:text-red-700 disabled:opacity-40"
          >
            Remove
          </button>
        </div>
      </div>
    </li>
  );
}

export default function CartPage() {
  const addToast = useUIStore((s) => s.addToast);
  const queryClient = useQueryClient();

  const { data: cart, isLoading } = useQuery({
    queryKey: queryKeys.cart.current(),
    queryFn: cartApi.getCart,
    retry: false,
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, qty }: { id: number; qty: number }) => cartApi.updateItem(id, qty),
    onSuccess: (updatedCart) => {
      queryClient.setQueryData(queryKeys.cart.current(), updatedCart);
    },
    onError: () => addToast('Could not update item.', 'error'),
  });

  const removeMutation = useMutation({
    mutationFn: (id: number) => cartApi.removeItem(id),
    onSuccess: (updatedCart) => {
      queryClient.setQueryData(queryKeys.cart.current(), updatedCart);
      addToast('Item removed from cart.', 'info');
      trackEvent('remove_from_cart');
    },
    onError: () => addToast('Could not remove item.', 'error'),
  });

  const isPending = updateMutation.isPending || removeMutation.isPending;

  return (
    <>
      <Helmet>
        <title>Your Cart – Upstream Literacy</title>
      </Helmet>

      <div className="mx-auto max-w-4xl px-4 py-8 sm:px-6 lg:px-8">
        <h1 className="mb-6 text-2xl font-bold tracking-tight text-gray-900">Your Cart</h1>

        {isLoading ? (
          <LoadingSkeleton lines={5} />
        ) : !cart || cart.items.length === 0 ? (
          <div className="rounded-xl border border-gray-200 bg-gray-50 py-20 text-center">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className="mx-auto mb-4 h-16 w-16 text-gray-300"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={1}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M2.25 3h1.386c.51 0 .955.343 1.087.835l.383 1.437M7.5 14.25a3 3 0 0 0-3 3h15.75m-12.75-3h11.218c1.121-2.3 2.1-4.684 2.924-7.138a60.114 60.114 0 0 0-16.536-1.84M7.5 14.25 5.106 5.272M6 20.25a.75.75 0 1 1-1.5 0 .75.75 0 0 1 1.5 0Zm12.75 0a.75.75 0 1 1-1.5 0 .75.75 0 0 1 1.5 0Z"
              />
            </svg>
            <p className="text-lg font-medium text-gray-600">Your cart is empty</p>
            <p className="mt-1 text-sm text-gray-400">Add some products to get started.</p>
            <Link to="/shop" className="btn-primary mt-6 inline-flex">
              Browse Products
            </Link>
          </div>
        ) : (
          <div className="grid gap-8 lg:grid-cols-3">
            {/* Items list */}
            <div className="lg:col-span-2">
              <ul className="divide-y divide-gray-200">
                {cart.items.map((item) => (
                  <CartLineItem
                    key={item.id}
                    item={item}
                    isPending={isPending}
                    onRemove={(id) => removeMutation.mutate(id)}
                    onUpdateQty={(id, qty) => updateMutation.mutate({ id, qty })}
                  />
                ))}
              </ul>
            </div>

            {/* Order summary */}
            <div className="h-fit rounded-xl border border-gray-200 bg-gray-50 p-6">
              <h2 className="mb-4 text-base font-semibold text-gray-900">Order Summary</h2>
              <dl className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <dt className="text-gray-600">
                    Subtotal ({cart.item_count} item{cart.item_count !== 1 ? 's' : ''})
                  </dt>
                  <dd className="font-medium text-gray-900">${cart.subtotal}</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-gray-600">Shipping</dt>
                  <dd className="text-gray-500">Calculated at checkout</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-gray-600">Tax</dt>
                  <dd className="text-gray-500">Calculated at checkout</dd>
                </div>
              </dl>

              <div className="my-4 border-t border-gray-200" />

              <div className="flex justify-between text-base font-semibold">
                <span>Subtotal</span>
                <span>${cart.subtotal}</span>
              </div>

              <Link to="/shop/checkout" className="btn-primary mt-4 w-full justify-center">
                Proceed to Checkout
              </Link>

              <Link
                to="/shop"
                className="mt-3 block text-center text-sm text-upstream-600 hover:underline"
              >
                Continue Shopping
              </Link>
            </div>
          </div>
        )}
      </div>
    </>
  );
}
