import { mockAlerts } from '../data/mock/mockAlerts';
import { AlertItem } from '../types';
import { apiClient } from './apiClient';

/**
 * Alert Service
 * Abstraction layer for alert data.
 * Interacts with FastAPI backend when configured; falls back to mock data.
 */

export const alertService = {
  /**
   * Get all alerts
   */
  async getAlerts(): Promise<AlertItem[]> {
    if (apiClient.isConfigured()) {
      try {
        return await apiClient.get<AlertItem[]>('/alerts');
      } catch (err) {
        console.warn('[alertService] getAlerts API failed, falling back to mock:', err);
      }
    }
    await new Promise((resolve) => setTimeout(resolve, 250));
    return mockAlerts;
  },

  /**
   * Get alerts by severity filter
   */
  async getAlertsBySeverity(
    severity: 'all' | 'critical' | 'warning' | 'info'
  ): Promise<AlertItem[]> {
    if (apiClient.isConfigured()) {
      try {
        const query = severity === 'all' ? '' : `?severity=${severity}`;
        return await apiClient.get<AlertItem[]>(`/alerts${query}`);
      } catch (err) {
        console.warn('[alertService] getAlertsBySeverity API failed, falling back to mock:', err);
      }
    }
    await new Promise((resolve) => setTimeout(resolve, 200));

    if (severity === 'all') {
      return mockAlerts;
    }

    return mockAlerts.filter((alert) => alert.severity === severity);
  },

  /**
   * Get alert by ID
   */
  async getAlertById(id: string): Promise<AlertItem | null> {
    if (apiClient.isConfigured()) {
      try {
        return await apiClient.get<AlertItem>(`/alerts/${id}`);
      } catch (err) {
        console.warn(`[alertService] getAlertById API failed for ${id}, falling back to mock:`, err);
      }
    }
    await new Promise((resolve) => setTimeout(resolve, 150));
    return mockAlerts.find((alert) => alert.id === id) || null;
  },

  /**
   * Mark alert as resolved
   */
  async resolveAlert(id: string): Promise<boolean> {
    if (apiClient.isConfigured()) {
      try {
        await apiClient.post<{ id: string; isResolved: boolean }>(`/alerts/${id}/resolve`);
        return true;
      } catch (err) {
        console.warn(`[alertService] resolveAlert API failed for ${id}, falling back to mock:`, err);
      }
    }
    await new Promise((resolve) => setTimeout(resolve, 300));
    console.log(`Alert ${id} marked as resolved`);
    return true;
  },
};
