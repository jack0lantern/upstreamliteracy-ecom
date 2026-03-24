import apiClient from './client';
import type { Order, OrderSummary, PaginatedResponse } from '@/types';

export interface OrdersParams {
  page?: number;
  page_size?: number;
  status?: string;
}

export const ordersApi = {
  getOrders: async (params?: OrdersParams): Promise<PaginatedResponse<OrderSummary>> => {
    const response = await apiClient.get<PaginatedResponse<OrderSummary>>('/orders/', { params });
    return response.data;
  },

  getOrder: async (orderNumber: string): Promise<Order> => {
    const response = await apiClient.get<Order>(`/orders/${orderNumber}/`);
    return response.data;
  },

  trackOrder: async (
    orderNumber: string,
    token: string,
  ): Promise<{ tracking_number: string | null; tracking_url: string | null; status: string }> => {
    const response = await apiClient.get(`/orders/${orderNumber}/track/`, {
      params: { token },
    });
    return response.data;
  },
};
