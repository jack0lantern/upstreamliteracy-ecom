import apiClient from './client';
import type { Cart } from '@/types';

const CART_TOKEN_KEY = 'upstream_cart_token';

function getStoredCartToken(): string | null {
  return localStorage.getItem(CART_TOKEN_KEY);
}

function storeCartToken(token: string): void {
  localStorage.setItem(CART_TOKEN_KEY, token);
}

function cartHeaders(): Record<string, string> {
  const token = getStoredCartToken();
  return token ? { 'X-Cart-Token': token } : {};
}

function handleCartResponse(response: { data: Cart }): Cart {
  if (response.data.token) {
    storeCartToken(response.data.token);
  }
  return response.data;
}

export const cartApi = {
  getCart: async (): Promise<Cart> => {
    const response = await apiClient.get<Cart>('/cart/', { headers: cartHeaders() });
    return handleCartResponse(response);
  },

  addItem: async (skuId: number, quantity: number): Promise<Cart> => {
    const response = await apiClient.post<Cart>('/cart/items/', { sku_id: skuId, quantity }, { headers: cartHeaders() });
    return handleCartResponse(response);
  },

  updateItem: async (itemId: number, quantity: number): Promise<Cart> => {
    const response = await apiClient.patch<Cart>(`/cart/items/${itemId}/`, { quantity }, { headers: cartHeaders() });
    return handleCartResponse(response);
  },

  removeItem: async (itemId: number): Promise<Cart> => {
    const response = await apiClient.delete<Cart>(`/cart/items/${itemId}/`, { headers: cartHeaders() });
    return handleCartResponse(response);
  },

  mergeCart: async (guestToken: string): Promise<Cart> => {
    const response = await apiClient.post<Cart>('/cart/merge/', { guest_cart_token: guestToken }, { headers: cartHeaders() });
    return handleCartResponse(response);
  },

  clearToken: (): void => {
    localStorage.removeItem(CART_TOKEN_KEY);
  },
};
