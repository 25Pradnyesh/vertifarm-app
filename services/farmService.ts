import { mockFarms } from '../data/mock/mockFarms';
import { Farm } from '../types';

/**
 * Farm Service
 * Abstraction layer for farm management data
 */

export const farmService = {
  /**
   * Get all farms for the current user
   */
  async getFarms(): Promise<Farm[]> {
    await new Promise((resolve) => setTimeout(resolve, 200));
    return mockFarms;
  },

  /**
   * Get farm by ID
   */
  async getFarmById(id: string): Promise<Farm | null> {
    await new Promise((resolve) => setTimeout(resolve, 150));
    return mockFarms.find((farm) => farm.id === id) || null;
  },

  /**
   * Get currently selected farm (in real app, this would be from state/storage)
   */
  async getCurrentFarm(): Promise<Farm> {
    await new Promise((resolve) => setTimeout(resolve, 100));
    return mockFarms[0]; // Default to Greenhouse 1
  },
};
