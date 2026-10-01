import { mockFarms } from '../data/mock/mockFarms';
import { Farm } from '../types';
import { apiClient } from './apiClient';

/**
 * Farm Service
 * Abstraction layer for farm management data.
 * Interacts with FastAPI backend when configured; falls back to mock data.
 */

export const farmService = {
  /**
   * Get all farms for the current user
   */
  async getFarms(): Promise<Farm[]> {
    if (apiClient.isConfigured()) {
      try {
        return await apiClient.get<Farm[]>('/farms');
      } catch (err) {
        console.warn('[farmService] API request failed, falling back to mock:', err);
      }
    }
    await new Promise((resolve) => setTimeout(resolve, 200));
    return mockFarms;
  },

  /**
   * Get farm by ID
   */
  async getFarmById(id: string): Promise<Farm | null> {
    if (apiClient.isConfigured()) {
      try {
        return await apiClient.get<Farm>(`/farms/${id}`);
      } catch (err) {
        console.warn(`[farmService] API request failed for farm ${id}, falling back to mock:`, err);
      }
    }
    await new Promise((resolve) => setTimeout(resolve, 150));
    return mockFarms.find((farm) => farm.id === id) || null;
  },

  /**
   * Get currently selected farm (in real app, this would be from state/storage)
   */
  async getCurrentFarm(): Promise<Farm> {
    const farms = await this.getFarms();
    return farms[0] || mockFarms[0];
  },
};
