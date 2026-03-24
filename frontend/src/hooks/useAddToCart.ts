import { useMutation, useQueryClient } from '@tanstack/react-query';
import { cartApi } from '@/lib/api/cart';
import { queryKeys } from '@/lib/queryKeys';
import { useUIStore } from '@/stores/uiStore';
import { trackEvent } from '@/lib/analytics';

export function useAddToCart() {
  const queryClient = useQueryClient();
  const addToast = useUIStore((s) => s.addToast);
  const openCartSidebar = useUIStore((s) => s.openCartSidebar);

  return useMutation({
    mutationFn: ({ skuId, quantity = 1 }: { skuId: number; quantity?: number }) =>
      cartApi.addItem(skuId, quantity),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.cart.current() });
      addToast('Added to cart!', 'success');
      openCartSidebar();
      trackEvent('add_to_cart', { sku_id: variables.skuId, quantity: variables.quantity });
    },
    onError: () => {
      addToast('Failed to add item to cart.', 'error');
    },
  });
}
