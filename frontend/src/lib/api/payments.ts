import apiClient from './client';

export interface CreatePaymentIntentResponse {
  client_secret: string;
  payment_intent_id: string | null;
}

export const paymentsApi = {
  createPaymentIntent: async (
    sessionToken: string,
  ): Promise<CreatePaymentIntentResponse> => {
    const response = await apiClient.post<CreatePaymentIntentResponse>(
      '/payments/intent/',
      { session_token: sessionToken },
    );
    return response.data;
  },
};
