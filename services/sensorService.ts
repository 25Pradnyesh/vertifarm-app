import { mockTelemetry } from '../data/mock/mockTelemetry';
import { mockSensors } from '../data/mock/mockSensors';
import { TelemetrySummary, SensorDevice, SensorReading, MetricType } from '../types';
import { apiClient } from './apiClient';

function getMockLatestReadings(): SensorReading[] {
  return mockTelemetry.map((t, idx) => ({
    id: `mock-reading-${t.metric}-${idx}`,
    sensorId: `s-${idx + 1}`,
    metric: t.metric,
    value: t.currentValue,
    unit: t.unit,
    status: t.status,
    statusLabel: t.statusLabel,
    timestamp: new Date().toISOString(),
  }));
}


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

  /**
   * Get latest readings snapshot across all metrics
   */
  async getLatestReadings(farmId?: string): Promise<SensorReading[]> {
    if (apiClient.isConfigured()) {
      try {
        const query = farmId ? `?farmId=${encodeURIComponent(farmId)}` : '';
        return await apiClient.get<SensorReading[]>(`/telemetry/latest${query}`);
      } catch (err) {
        console.warn('[sensorService] getLatestReadings API failed, falling back to mock:', err);
      }
    }
    await new Promise((resolve) => setTimeout(resolve, 200));
    return getMockLatestReadings();
  },

  /**
   * Get raw historical sensor readings
   */
  async getReadingsHistory(
    metric?: MetricType,
    farmId?: string,
    limit: number = 50
  ): Promise<SensorReading[]> {
    if (apiClient.isConfigured()) {
      try {
        const params = new URLSearchParams();
        if (metric) params.append('metric', metric);
        if (farmId) params.append('farmId', farmId);
        params.append('limit', limit.toString());
        return await apiClient.get<SensorReading[]>(`/telemetry/readings?${params.toString()}`);
      } catch (err) {
        console.warn('[sensorService] getReadingsHistory API failed, falling back to mock:', err);
      }
    }
    await new Promise((resolve) => setTimeout(resolve, 200));
    const all = getMockLatestReadings();
    return metric ? all.filter((r) => r.metric === metric) : all;
  },

  /**
   * Subscribe to real-time telemetry streaming (WebSocket with graceful fallback)
   */
  subscribeToTelemetry(
    onReading: (reading: SensorReading) => void,
    farmId?: string
  ): () => void {
    if (!apiClient.isConfigured()) {
      return () => {};
    }

    try {
      const wsUrl = apiClient.getWsUrl('/telemetry/ws');
      const ws = new WebSocket(wsUrl);

      ws.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);
          if (payload.type === 'telemetry_reading' && payload.data) {
            const reading: SensorReading = payload.data;
            if (!farmId || (reading as any).farmId === farmId || reading.sensorId.includes(farmId)) {
              onReading(reading);
            }
          }
        } catch {
          // ignore parse errors
        }
      };

      ws.onerror = (err) => {
        console.warn('[sensorService] Telemetry WebSocket error:', err);
      };

      return () => {
        try {
          if (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING) {
            ws.close();
          }
        } catch {
          // ignore close errors
        }
      };
    } catch (err) {
      console.warn('[sensorService] Failed to establish Telemetry WebSocket:', err);
      return () => {};
    }
  },
};
