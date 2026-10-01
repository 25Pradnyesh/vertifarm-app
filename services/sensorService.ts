import { mockTelemetry } from '../data/mock/mockTelemetry';
import { mockSensors } from '../data/mock/mockSensors';
import { TelemetrySummary, SensorDevice, MetricType } from '../types';
import { apiClient } from './apiClient';

/**
 * Sensor Service
 * Abstraction layer for sensor data.
 * Interacts with FastAPI backend when configured; falls back to mock data.
 */

export const sensorService = {
  /**
   * Get all sensor telemetry summaries
   */
  async getTelemetrySummaries(): Promise<TelemetrySummary[]> {
    if (apiClient.isConfigured()) {
      try {
        return await apiClient.get<TelemetrySummary[]>('/telemetry/summary');
      } catch (err) {
        console.warn('[sensorService] getTelemetrySummaries API failed, falling back to mock:', err);
      }
    }
    await new Promise((resolve) => setTimeout(resolve, 300));
    return mockTelemetry;
  },

  /**
   * Get telemetry for a specific metric
   */
  async getTelemetryByMetric(metric: MetricType): Promise<TelemetrySummary | null> {
    if (apiClient.isConfigured()) {
      try {
        return await apiClient.get<TelemetrySummary>(`/telemetry/${metric}`);
      } catch (err) {
        console.warn(`[sensorService] getTelemetryByMetric API failed for ${metric}, falling back to mock:`, err);
      }
    }
    await new Promise((resolve) => setTimeout(resolve, 200));
    return mockTelemetry.find((t) => t.metric === metric) || null;
  },

  /**
   * Get all configured sensor devices
   */
  async getSensorDevices(): Promise<SensorDevice[]> {
    if (apiClient.isConfigured()) {
      try {
        return await apiClient.get<SensorDevice[]>('/sensors');
      } catch (err) {
        console.warn('[sensorService] getSensorDevices API failed, falling back to mock:', err);
      }
    }
    await new Promise((resolve) => setTimeout(resolve, 200));
    return mockSensors;
  },

  /**
   * Get overall farm health status
   */
  async getFarmHealthStatus(): Promise<{
    status: 'healthy' | 'warning' | 'critical';
    message: string;
  }> {
    if (apiClient.isConfigured()) {
      try {
        return await apiClient.get<{ status: 'healthy' | 'warning' | 'critical'; message: string }>('/telemetry/health');
      } catch (err) {
        console.warn('[sensorService] getFarmHealthStatus API failed, falling back to mock:', err);
      }
    }
    await new Promise((resolve) => setTimeout(resolve, 150));

    const criticalCount = mockTelemetry.filter((t) => t.status === 'critical').length;
    const warningCount = mockTelemetry.filter((t) => t.status === 'warning').length;

    if (criticalCount > 0) {
      return {
        status: 'critical',
        message: 'Some parameters require immediate attention.',
      };
    }

    if (warningCount > 0) {
      return {
        status: 'warning',
        message: 'Some parameters need monitoring.',
      };
    }

    return {
      status: 'healthy',
      message: 'All systems are running smoothly.',
    };
  },
};
