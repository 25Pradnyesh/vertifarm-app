import { mockTelemetry } from '../data/mock/mockTelemetry';
import { mockSensors } from '../data/mock/mockSensors';
import { TelemetrySummary, SensorDevice, MetricType } from '../types';

/**
 * Sensor Service
 * Abstraction layer for sensor data - currently returns mock data,
 * but can be replaced with REST API calls when backend is ready.
 */

export const sensorService = {
  /**
   * Get all sensor telemetry summaries
   */
  async getTelemetrySummaries(): Promise<TelemetrySummary[]> {
    // Simulate network delay
    await new Promise((resolve) => setTimeout(resolve, 300));
    return mockTelemetry;
  },

  /**
   * Get telemetry for a specific metric
   */
  async getTelemetryByMetric(metric: MetricType): Promise<TelemetrySummary | null> {
    await new Promise((resolve) => setTimeout(resolve, 200));
    return mockTelemetry.find((t) => t.metric === metric) || null;
  },

  /**
   * Get all configured sensor devices
   */
  async getSensorDevices(): Promise<SensorDevice[]> {
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
