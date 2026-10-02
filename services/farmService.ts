import { mockFarms } from '../data/mock/mockFarms';
import { Farm } from '../types';
import { config } from '../constants/config';
import { apiClient } from './apiClient';

/**
 * Farm Service
 * Abstraction layer for farm management data.
 * Interacts with FastAPI backend when configured; falls back to mock data only in explicit demo mode.
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
        if (!config.demoMode) {
          throw err;
        }
        console.warn('[farmService] API request failed, falling back to demo mode:', err);
      }
    } else if (!config.demoMode && !__DEV__) {
      throw new Error('API backend is not configured.');
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
      } catch (err: any) {
        if (err?.message?.includes('404')) {
          return null;
        }
        if (!config.demoMode) {
          throw err;
        }
        console.warn(`[farmService] API request failed for farm ${id}, falling back to demo mode:`, err);
      }
    } else if (!config.demoMode && !__DEV__) {
      throw new Error('API backend is not configured.');
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
