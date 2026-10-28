import { mockAlerts } from '../data/mock/mockAlerts';
import { AlertItem } from '../types';
import { apiClient } from './apiClient';

/**
 * Alert Service
 * Abstraction layer for alert data.
 * Interacts with FastAPI backend when configured; falls back to mock data.
 */

let dynamicAlerts: AlertItem[] = [...mockAlerts];

export const alertService = {
  /**
   * Add a locally triggered alert into the service store
   */
  addLocalAlert(alert: AlertItem): void {
    const existingIdx = dynamicAlerts.findIndex((a) => a.id === alert.id);
    if (existingIdx >= 0) {
      dynamicAlerts[existingIdx] = alert;
    } else {
      dynamicAlerts = [alert, ...dynamicAlerts];
    }
  },

  /**
   * Mark a locally tracked alert as resolved
   */
  resolveLocalAlert(id: string): void {
    const alert = dynamicAlerts.find((a) => a.id === id);
    if (alert) {
      alert.isResolved = true;
    }
  },

  /**
   * Get all alerts
   */
  async getAlerts(): Promise<AlertItem[]> {
    if (apiClient.isConfigured()) {
      try {
        const remote = await apiClient.get<AlertItem[]>('/alerts');
        // Merge remote with local dynamic alerts not yet on backend
        const remoteIds = new Set(remote.map((r) => r.id));
        const localUnsynced = dynamicAlerts.filter((l) => !remoteIds.has(l.id));
        return [...localUnsynced, ...remote];
      } catch (err) {
        console.warn('[alertService] getAlerts API failed, falling back to mock:', err);
      }
    }
    await new Promise((resolve) => setTimeout(resolve, 250));
    return dynamicAlerts;
  },

  /**
   * Get alerts by severity filter
   */
  async getAlertsBySeverity(
    severity: 'all' | 'critical' | 'warning' | 'info'
  ): Promise<AlertItem[]> {
    const all = await this.getAlerts();
    if (severity === 'all') {
      return all;
    }
    return all.filter((alert) => alert.severity === severity);
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
    return dynamicAlerts.find((alert) => alert.id === id) || null;
  },

  /**
   * Mark alert as resolved
   */
  async resolveAlert(id: string): Promise<boolean> {
    this.resolveLocalAlert(id);
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
