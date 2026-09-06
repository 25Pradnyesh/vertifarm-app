import { mockAlerts } from '../data/mock/mockAlerts';
import { AlertItem } from '../types';

/**
 * Alert Service
 * Abstraction layer for alert data - currently returns mock data,
 * but can be replaced with REST API calls when backend is ready.
 */

export const alertService = {
  /**
   * Get all alerts
   */
  async getAlerts(): Promise<AlertItem[]> {
    await new Promise((resolve) => setTimeout(resolve, 250));
    return mockAlerts;
  },

  /**
   * Get alerts by severity filter
   */
  async getAlertsBySeverity(
    severity: 'all' | 'critical' | 'warning' | 'info'
  ): Promise<AlertItem[]> {
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
    await new Promise((resolve) => setTimeout(resolve, 150));
    return mockAlerts.find((alert) => alert.id === id) || null;
  },

  /**
   * Mark alert as resolved
   */
  async resolveAlert(id: string): Promise<boolean> {
    await new Promise((resolve) => setTimeout(resolve, 300));
    // In a real implementation, this would call the backend API
    console.log(`Alert ${id} marked as resolved`);
    return true;
  },
};
