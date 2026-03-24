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

const DEBUG_LOG = (data: Record<string, unknown>) => {
  fetch('http://127.0.0.1:7463/ingest/9791c52c-4ea2-4fa8-b6e8-0390ad523297', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-Debug-Session-Id': '1fad8f' },
    body: JSON.stringify({ sessionId: '1fad8f', location: 'products.ts:getProducts', message: 'products API', data: { ...data }, timestamp: Date.now() }),
  }).catch(() => {});
};

export const productsApi = {
  getProducts: async (
    params?: ProductsParams,
  ): Promise<PaginatedResponse<ProductListItem>> => {
    // #region agent log
    const baseURL = import.meta.env.VITE_API_BASE_URL ?? '/api';
    DEBUG_LOG({ hypothesisId: 'H1-H5', baseURL, fullUrl: `${baseURL}/products/`, params });
    // #endregion
    try {
      const response = await apiClient.get<PaginatedResponse<ProductListItem>>('/products/', {
        params,
      });
      // #region agent log
      DEBUG_LOG({ hypothesisId: 'H4', success: true, hasResults: !!response.data?.results, count: response.data?.count });
      // #endregion
      return response.data;
    } catch (err) {
      // #region agent log
      const ax = err as { message?: string; code?: string; config?: { url?: string; baseURL?: string }; response?: { status?: number; data?: unknown } };
      DEBUG_LOG({
        hypothesisId: 'H1,H2,H3,H5',
        error: true,
        message: ax.message,
        code: ax.code,
        reqUrl: ax.config?.url,
        reqBase: ax.config?.baseURL,
        resStatus: ax.response?.status,
        resData: ax.response?.data,
      });
      // #endregion
      throw err;
    }
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
