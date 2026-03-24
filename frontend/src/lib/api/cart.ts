import apiClient from './client';
import type { Cart } from '@/types';

export const cartApi = {
  getCart: async (): Promise<Cart> => {
    const response = await apiClient.get<Cart>('/cart/');
    return response.data;
  },

  addItem: async (skuId: number, quantity: number): Promise<Cart> => {
    const response = await apiClient.post<Cart>('/cart/items/', { sku_id: skuId, quantity });
    return response.data;
  },

  updateItem: async (itemId: number, quantity: number): Promise<Cart> => {
    const response = await apiClient.patch<Cart>(`/cart/items/${itemId}/`, { quantity });
    return response.data;
  },

  removeItem: async (itemId: number): Promise<Cart> => {
    const response = await apiClient.delete<Cart>(`/cart/items/${itemId}/`);
    return response.data;
  },

  mergeCart: async (guestToken: string): Promise<Cart> => {
    const response = await apiClient.post<Cart>('/cart/merge/', { guest_token: guestToken });
    return response.data;
  },
};
