import apiClient from './client';
import type {
  CheckoutSession,
  CheckoutRequest,
  ShippingMethod,
  TaxEstimate,
  AddressPayload,
  Order,
} from '@/types';

export interface ContactPayload {
  email: string;
  phone?: string;
}

export interface ShippingMethodPayload {
  shipping_method_id: string;
}

export interface PaymentPayload {
  payment_method_nonce: string;
  coupon_code?: string;
}

export const checkoutApi = {
  createSession: async (cartToken?: string): Promise<CheckoutSession> => {
    const response = await apiClient.post<CheckoutSession>('/checkout/sessions/', {
      cart_token: cartToken,
    });
    return response.data;
  },

  getSession: async (token: string): Promise<CheckoutSession> => {
    const response = await apiClient.get<CheckoutSession>(`/checkout/sessions/${token}/`);
    return response.data;
  },

  updateContact: async (token: string, data: ContactPayload): Promise<CheckoutSession> => {
    const response = await apiClient.patch<CheckoutSession>(
      `/checkout/sessions/${token}/contact/`,
      data,
    );
    return response.data;
  },

  updateAddress: async (
    token: string,
    data: { shipping_address: AddressPayload; billing_same_as_shipping: boolean; billing_address?: AddressPayload },
  ): Promise<CheckoutSession> => {
    const response = await apiClient.patch<CheckoutSession>(
      `/checkout/sessions/${token}/address/`,
      data,
    );
    return response.data;
  },

  updateShipping: async (token: string, data: ShippingMethodPayload): Promise<CheckoutSession> => {
    const response = await apiClient.patch<CheckoutSession>(
      `/checkout/sessions/${token}/shipping/`,
      data,
    );
    return response.data;
  },

  updatePayment: async (token: string, data: PaymentPayload): Promise<CheckoutSession> => {
    const response = await apiClient.patch<CheckoutSession>(
      `/checkout/sessions/${token}/payment/`,
      data,
    );
    return response.data;
  },

  submitCheckout: async (token: string): Promise<Order> => {
    const response = await apiClient.post<Order>(`/checkout/sessions/${token}/submit/`);
    return response.data;
  },

  getShippingRates: async (zip?: string): Promise<ShippingMethod[]> => {
    const response = await apiClient.get<ShippingMethod[]>('/checkout/shipping-rates/', {
      params: zip ? { postal_code: zip } : undefined,
    });
    return response.data;
  },

  getTaxEstimate: async (sessionId: string): Promise<TaxEstimate> => {
    const response = await apiClient.get<TaxEstimate>(
      `/checkout/sessions/${sessionId}/tax-estimate/`,
    );
    return response.data;
  },

  // Kept for backward compatibility – wraps the multi-step flow into a single call
  submitOrder: async (data: CheckoutRequest): Promise<Order> => {
    const response = await apiClient.post<Order>('/checkout/submit/', data);
    return response.data;
  },
};
