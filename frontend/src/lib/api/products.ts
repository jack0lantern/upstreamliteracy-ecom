import apiClient from './client';
import type { ProductListItem, ProductDetail, PaginatedResponse } from '@/types';

export interface ProductsParams {
  page?: number;
  page_size?: number;
  category?: string;
  search?: string;
  ordering?: string;
  min_price?: number;
  max_price?: number;
  product_type?: string;
  in_stock?: boolean;
}

export const productsApi = {
  getProducts: async (
    params?: ProductsParams,
  ): Promise<PaginatedResponse<ProductListItem>> => {
    const response = await apiClient.get<PaginatedResponse<ProductListItem>>('/products/', {
      params,
    });
    return response.data;
  },

  getProduct: async (slug: string): Promise<ProductDetail> => {
    const response = await apiClient.get<ProductDetail>(`/products/${slug}/`);
    return response.data;
  },

  getRelatedProducts: async (slug: string): Promise<ProductListItem[]> => {
    const response = await apiClient.get<ProductListItem[]>(`/products/${slug}/related/`);
    return response.data;
  },
};
