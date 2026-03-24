import type { ProductsParams } from '@/lib/api/products';
import type { OrdersParams } from '@/lib/api/orders';

export const queryKeys = {
  products: {
    all: ['products'] as const,
    list: (params?: ProductsParams) => ['products', 'list', params] as const,
    detail: (slug: string) => ['products', 'detail', slug] as const,
    related: (slug: string) => ['products', 'related', slug] as const,
  },

  categories: {
    all: ['categories'] as const,
    list: () => ['categories', 'list'] as const,
    detail: (slug: string) => ['categories', 'detail', slug] as const,
  },

  cart: {
    all: ['cart'] as const,
    current: () => ['cart', 'current'] as const,
  },

  checkout: {
    all: ['checkout'] as const,
    session: (token: string) => ['checkout', 'session', token] as const,
    shippingRates: (zip?: string) => ['checkout', 'shipping-rates', zip] as const,
    taxEstimate: (sessionId: string) => ['checkout', 'tax-estimate', sessionId] as const,
  },

  orders: {
    all: ['orders'] as const,
    list: (params?: OrdersParams) => ['orders', 'list', params] as const,
    detail: (orderNumber: string) => ['orders', 'detail', orderNumber] as const,
  },

  account: {
    all: ['account'] as const,
    profile: () => ['account', 'profile'] as const,
    addresses: () => ['account', 'addresses'] as const,
  },

  search: {
    all: ['search'] as const,
    results: (query: string, page?: number) => ['search', 'results', query, page] as const,
  },
};
