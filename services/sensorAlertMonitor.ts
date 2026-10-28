import { AlertItem, MetricType, SensorReading, TelemetrySummary } from '../types';
import { evaluateSensorThreshold, SENSOR_THRESHOLDS } from '../constants/thresholds';
import { notificationService } from './notificationService';
import { alertService } from './alertService';
import { sensorService } from './sensorService';

interface ActiveAlertRecord {
  alert: AlertItem;
  direction: 'low' | 'high';
  createdAt: number;
  lastNotifiedAt: number;
}

export type AlertListener = (activeAlerts: AlertItem[], allAlerts: AlertItem[]) => void;

/**
 * Sensor Alert Monitor
 * State-based lifecycle manager for real-time sensor threshold detection,
 * deduplication, recovery, and native notification delivery.
 */
class SensorAlertMonitor {
  private activeAlerts = new Map<string, ActiveAlertRecord>();
  private listeners: Set<AlertListener> = new Set();
  private isMonitoring = false;
  private wsUnsubscribe: (() => void) | null = null;
  private pollingTimer: any = null;

  private makeKey(farmId: string, metric: MetricType): string {
    return `${farmId}:${metric}`;
  }

  /**
   * Process a single sensor reading through the threshold evaluation lifecycle.
   */
  async processReading(reading: SensorReading & { farmId?: string; zoneId?: string; zoneName?: string }): Promise<AlertItem | null> {
    if (!reading || !reading.metric) {
      return null;
    }

    const farmId = reading.farmId || 'farm-1';
    const zoneId = reading.zoneId || 'z-1';
    const zoneName = reading.zoneName || 'Greenhouse 1 - Zone 1';
    const key = this.makeKey(farmId, reading.metric);
    const existing = this.activeAlerts.get(key);

    // 1. Evaluate reading against threshold config with hysteresis recovery
    const evaluation = evaluateSensorThreshold(
      reading.metric,
      reading.value,
      existing ? existing.direction : null
    );

    // 2. Reject invalid or unavailable sensor readings without alerting
    if (!evaluation.isValid) {
      return null;
    }

    // 3. Lifecycle State: THRESHOLD EXCEEDED
    if (evaluation.isViolation) {
      if (existing) {
        // STATE 2: Threshold STILL exceeded -> Suppress duplicate notification
        // Update current reading in existing alert without re-alerting
        existing.alert.currentValue = evaluation.currentValueFormatted;
        return null;
      }

      // STATE 1: Normal -> Threshold exceeded (New violation)
      const now = new Date();
      const timeStr = now.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
      const alertId = `alert-${reading.metric}-${Date.now()}`;

      const newAlert: AlertItem = {
        id: alertId,
        farmId,
        zoneId,
        zoneName,
        metric: reading.metric,
        severity: evaluation.severity,
        title: evaluation.title,
        description: evaluation.notificationBody,
        currentValue: evaluation.currentValueFormatted,
        thresholdValue: evaluation.thresholdValueFormatted,
        timestamp: timeStr,
        isResolved: false,
        recommendation: evaluation.recommendation,
      };

      // Record active alert
      this.activeAlerts.set(key, {
        alert: newAlert,
        direction: evaluation.violationDirection || 'high',
        createdAt: Date.now(),
        lastNotifiedAt: Date.now(),
      });

      // Synchronize with alert service
      alertService.addLocalAlert(newAlert);

      // Trigger native notification with Red Leaf icon and single-line description
      await notificationService.sendSensorAlertNotification({
        alertId: newAlert.id,
        metric: newAlert.metric,
        farmId: newAlert.farmId,
        title: newAlert.title,
        body: newAlert.description,
        severity: newAlert.severity,
        timestamp: newAlert.timestamp,
      });

      this.notifyListeners();
      return newAlert;
    }

    // 4. Lifecycle State: RECOVERY (Reading returns to normal)
    if (existing && !evaluation.isViolation) {
      // STATE 3: Reading returns to normal -> Resolve alert
      const resolvedAlert = existing.alert;
      resolvedAlert.isResolved = true;

      this.activeAlerts.delete(key);
      alertService.resolveLocalAlert(resolvedAlert.id);

      this.notifyListeners();
      return null;
    }

    return null;
  }

  /**
   * Process a TelemetrySummary item (used in polling or summaries snapshot).
   */
  async processSummary(summary: TelemetrySummary, farmId: string = 'farm-1'): Promise<AlertItem | null> {
    return this.processReading({
      id: `reading-${summary.metric}-${Date.now()}`,
      sensorId: `s-${summary.metric}`,
      farmId,
      metric: summary.metric,
      value: summary.currentValue,
      unit: summary.unit,
      status: summary.status,
      statusLabel: summary.statusLabel,
      timestamp: new Date().toISOString(),
    });
  }

  /**
   * Get all currently active, unresolved alerts.
   */
  getActiveAlerts(): AlertItem[] {
    return Array.from(this.activeAlerts.values()).map((r) => r.alert);
  }

  /**
   * Check if a specific metric currently has an active alert.
   */
  hasActiveAlert(metric: MetricType, farmId: string = 'farm-1'): boolean {
    return this.activeAlerts.has(this.makeKey(farmId, metric));
  }

  /**
   * Register listener for alert state updates.
   */
  subscribe(listener: AlertListener): () => void {
    this.listeners.add(listener);
    // Send immediate snapshot
    const active = this.getActiveAlerts();
    alertService.getAlerts().then((all) => listener(active, all));

    return () => {
      this.listeners.delete(listener);
    };
  }

  private notifyListeners(): void {
    const active = this.getActiveAlerts();
    alertService.getAlerts().then((all) => {
      for (const listener of this.listeners) {
        try {
          listener(active, all);
        } catch (e) {
          console.warn('[SensorAlertMonitor] Listener error:', e);
        }
      }
    });
  }

  /**
   * Starts real-time monitoring across WebSocket and polling fallbacks.
   */
  startMonitoring(farmId: string = 'farm-1'): void {
    if (this.isMonitoring) return;
    this.isMonitoring = true;

    // 1. Subscribe to WebSocket streaming
    this.wsUnsubscribe = sensorService.subscribeToTelemetry((reading) => {
      this.processReading({ ...reading, farmId });
    }, farmId);

    // 2. Poll latest telemetry summaries every 5 seconds (graceful fallback)
    const pollTelemetry = async () => {
      try {
        const summaries = await sensorService.getTelemetrySummaries();
        for (const summary of summaries) {
          await this.processSummary(summary, farmId);
        }
      } catch (err) {
        // quiet fallback
      }
    };

    pollTelemetry();
    this.pollingTimer = setInterval(pollTelemetry, 5000);
  }

  /**
   * Stops real-time monitoring.
   */
  stopMonitoring(): void {
    if (this.wsUnsubscribe) {
      this.wsUnsubscribe();
      this.wsUnsubscribe = null;
    }
    if (this.pollingTimer) {
      clearInterval(this.pollingTimer);
      this.pollingTimer = null;
    }
    this.isMonitoring = false;
  }

  /**
   * Reset monitor state (useful for tests).
   */
  reset(): void {
    this.activeAlerts.clear();
    this.notifyListeners();
  }
}

export const sensorAlertMonitor = new SensorAlertMonitor();
