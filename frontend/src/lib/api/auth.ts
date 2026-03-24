import apiClient from './client';
import type { AuthUser, AuthTokens } from '@/types';

export interface RegisterPayload {
  email: string;
  password: string;
  first_name: string;
  last_name: string;
}

export interface LoginPayload {
  email: string;
  password: string;
}

export interface LoginResponse {
  user: AuthUser;
  tokens: AuthTokens;
}

export interface RegisterResponse {
  user: AuthUser;
  message: string;
}

export const authApi = {
  register: async (data: RegisterPayload): Promise<RegisterResponse> => {
    const response = await apiClient.post<RegisterResponse>('/auth/register/', data);
    return response.data;
  },

  login: async (data: LoginPayload): Promise<LoginResponse> => {
    const response = await apiClient.post<{ access: string; user: AuthUser }>('/auth/login/', data);
    return {
      user: response.data.user,
      tokens: {
        access: response.data.access,
        refresh: '', // refresh token is delivered via httpOnly cookie
      },
    };
  },

  logout: async (refreshToken: string): Promise<void> => {
    await apiClient.post('/auth/logout/', { refresh: refreshToken });
  },

  refreshToken: async (token: string): Promise<{ access: string }> => {
    const response = await apiClient.post<{ access: string }>('/auth/token/refresh/', {
      refresh: token,
    });
    return response.data;
  },

  verifyEmail: async (token: string): Promise<{ message: string }> => {
    const response = await apiClient.post<{ message: string }>('/auth/verify-email/', { token });
    return response.data;
  },

  resendVerification: async (email: string): Promise<{ message: string }> => {
    const response = await apiClient.post<{ message: string }>('/auth/resend-verification/', {
      email,
    });
    return response.data;
  },

  requestPasswordReset: async (email: string): Promise<{ message: string }> => {
    const response = await apiClient.post<{ message: string }>('/auth/password-reset/', { email });
    return response.data;
  },

  confirmPasswordReset: async (
    token: string,
    password: string,
  ): Promise<{ message: string }> => {
    const response = await apiClient.post<{ message: string }>('/auth/password-reset/confirm/', {
      token,
      password,
    });
    return response.data;
  },

  changePassword: async (
    current_password: string,
    new_password: string,
  ): Promise<{ message: string }> => {
    const response = await apiClient.post<{ message: string }>('/auth/change-password/', {
      current_password,
      new_password,
    });
    return response.data;
  },
};
