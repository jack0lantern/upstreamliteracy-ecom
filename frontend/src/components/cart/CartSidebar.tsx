import { useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { cartApi } from '@/lib/api/cart';
import { queryKeys } from '@/lib/queryKeys';
import { useUIStore } from '@/stores/uiStore';
import type { CartItem } from '@/types';

function SidebarItem({ item, onRemove, isRemoving }: {
  item: CartItem;
  onRemove: (id: number) => void;
  isRemoving: boolean;
}) {
  const imageUrl = item.sku.primary_image_url || null;
  const title = item.sku.product_title;
  const slug = item.sku.product_slug;

  return (
    <div className="flex gap-3 py-3">
      {/* Thumbnail */}
      <div className="h-16 w-16 flex-shrink-0 overflow-hidden rounded-md bg-gray-100">
        {imageUrl ? (
          <img
            src={imageUrl}
            alt={title}
            className="h-full w-full object-cover"
          />
        ) : (
          <div className="flex h-full w-full items-center justify-center text-gray-300">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1}>
              <path strokeLinecap="round" strokeLinejoin="round" d="m2.25 15.75 5.159-5.159a2.25 2.25 0 0 1 3.182 0l5.159 5.159m-1.5-1.5 1.409-1.409a2.25 2.25 0 0 1 3.182 0l2.909 2.909m-18 3.75h16.5a1.5 1.5 0 0 0 1.5-1.5V6a1.5 1.5 0 0 0-1.5-1.5H3.75A1.5 1.5 0 0 0 2.25 6v12a1.5 1.5 0 0 0 1.5 1.5Zm10.5-11.25h.008v.008h-.008V8.25Zm.375 0a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Z" />
            </svg>
          </div>
        )}
      </div>

      {/* Info */}
      <div className="flex flex-1 flex-col min-w-0">
        <Link
          to={`/shop/product/${slug}`}
          className="text-sm font-medium text-gray-900 hover:text-upstream-700 truncate"
        >
          {title}
        </Link>
        {item.sku.variant_label && (
          <p className="text-xs text-gray-500">{item.sku.variant_label}</p>
        )}
        <div className="mt-1 flex items-center justify-between">
          <p className="text-sm text-gray-500">
            Qty {item.quantity} &times; ${item.unit_price}
          </p>
          <p className="text-sm font-medium text-gray-900">${item.line_total}</p>
        </div>
      </div>

      {/* Remove */}
      <button
        type="button"
        onClick={() => onRemove(item.id)}
        disabled={isRemoving}
        className="self-start p-1 text-gray-400 hover:text-red-500 disabled:opacity-40"
        aria-label={`Remove ${title}`}
      >
        <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
          <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
        </svg>
      </button>
    </div>
  );
}

export function CartSidebar() {
  const isOpen = useUIStore((s) => s.isCartSidebarOpen);
  const close = useUIStore((s) => s.closeCartSidebar);
  const addToast = useUIStore((s) => s.addToast);
  const queryClient = useQueryClient();

  const { data: cart } = useQuery({
    queryKey: queryKeys.cart.current(),
    queryFn: cartApi.getCart,
    enabled: isOpen,
    staleTime: 30_000,
  });

  const removeMutation = useMutation({
    mutationFn: (itemId: number) => cartApi.removeItem(itemId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.cart.current() });
    },
    onError: () => {
      addToast('Failed to remove item.', 'error');
    },
  });

  // Body scroll lock
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
      return () => { document.body.style.overflow = ''; };
    }
  }, [isOpen]);

  // Close on Escape
  useEffect(() => {
    if (!isOpen) return;
    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === 'Escape') close();
    }
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, close]);

  const items = cart?.items ?? [];

  return (
    <>
      {/* Backdrop */}
      <div
        className={`fixed inset-0 z-40 bg-black/40 transition-opacity duration-300 ${
          isOpen ? 'opacity-100' : 'pointer-events-none opacity-0'
        }`}
        onClick={close}
        aria-hidden="true"
      />

      {/* Panel */}
      <div
        className={`fixed right-0 top-0 z-50 flex h-full w-full max-w-md flex-col bg-white shadow-xl transition-transform duration-300 ease-in-out ${
          isOpen ? 'translate-x-0' : 'translate-x-full'
        }`}
        role="dialog"
        aria-modal={isOpen}
        aria-label="Shopping cart"
      >
        {/* Header */}
        <div className="flex items-center justify-between border-b border-gray-200 px-5 py-4">
          <h2 className="text-lg font-semibold text-gray-900">Cart</h2>
          <button
            type="button"
            onClick={close}
            className="rounded-md p-1 text-gray-400 hover:text-gray-600"
            aria-label="Close cart"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
            </svg>
          </button>
        </div>

        {/* Items */}
        <div className="flex-1 overflow-y-auto px-5">
          {items.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-16 text-center">
              <svg xmlns="http://www.w3.org/2000/svg" className="mb-4 h-12 w-12 text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 3h1.386c.51 0 .955.343 1.087.835l.383 1.437M7.5 14.25a3 3 0 0 0-3 3h15.75m-12.75-3h11.218c1.121-2.3 2.1-4.684 2.924-7.138a60.114 60.114 0 0 0-16.536-1.84M7.5 14.25 5.106 5.272M6 20.25a.75.75 0 1 1-1.5 0 .75.75 0 0 1 1.5 0Zm12.75 0a.75.75 0 1 1-1.5 0 .75.75 0 0 1 1.5 0Z" />
              </svg>
              <p className="text-sm font-medium text-gray-600">Your cart is empty</p>
              <button
                type="button"
                onClick={close}
                className="mt-4 text-sm font-medium text-upstream-600 hover:underline"
              >
                Continue Shopping
              </button>
            </div>
          ) : (
            <div className="divide-y divide-gray-100">
              {items.map((item) => (
                <SidebarItem
                  key={item.id}
                  item={item}
                  onRemove={(id) => removeMutation.mutate(id)}
                  isRemoving={removeMutation.isPending}
                />
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        {items.length > 0 && (
          <div className="border-t border-gray-200 px-5 py-4 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-gray-700">Subtotal</span>
              <span className="text-base font-semibold text-gray-900">${cart?.subtotal}</span>
            </div>
            <p className="text-xs text-gray-500">Shipping and taxes calculated at checkout.</p>
            <div className="flex gap-3">
              <Link
                to="/shop/cart"
                onClick={close}
                className="btn-secondary flex-1 text-center"
              >
                View Cart
              </Link>
              <Link
                to="/shop/checkout"
                onClick={close}
                className="btn-primary flex-1 text-center"
              >
                Checkout
              </Link>
            </div>
          </div>
        )}
      </div>
    </>
  );
}
