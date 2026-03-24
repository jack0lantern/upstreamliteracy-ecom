import apiClient from './client';
import type { UserProfile, ProfileUpdatePayload, Address, AddressPayload } from '@/types';

export const accountApi = {
  getProfile: async (): Promise<UserProfile> => {
    const response = await apiClient.get<UserProfile>('/account/profile/');
    return response.data;
  },

  updateProfile: async (data: ProfileUpdatePayload): Promise<UserProfile> => {
    const response = await apiClient.patch<UserProfile>('/account/profile/', data);
    return response.data;
  },

  getAddresses: async (): Promise<Address[]> => {
    const response = await apiClient.get<Address[]>('/account/addresses/');
    return response.data;
  },

  createAddress: async (data: AddressPayload): Promise<Address> => {
    const response = await apiClient.post<Address>('/account/addresses/', data);
    return response.data;
  },

  updateAddress: async (id: number, data: Partial<AddressPayload>): Promise<Address> => {
    const response = await apiClient.patch<Address>(`/account/addresses/${id}/`, data);
    return response.data;
  },

  deleteAddress: async (id: number): Promise<void> => {
    await apiClient.delete(`/account/addresses/${id}/`);
  },

  setDefaultAddress: async (id: number): Promise<Address> => {
    const response = await apiClient.post<Address>(`/account/addresses/${id}/set-default/`);
    return response.data;
  },
};
