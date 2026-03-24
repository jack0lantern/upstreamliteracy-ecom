import apiClient from './client';
import type { Category } from '@/types';

export const categoriesApi = {
  getCategories: async (): Promise<Category[]> => {
    const response = await apiClient.get<Category[]>('/categories/');
    return response.data;
  },

  getCategory: async (slug: string): Promise<Category> => {
    const response = await apiClient.get<Category>(`/categories/${slug}/`);
    return response.data;
  },
};
