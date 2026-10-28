import { Platform } from 'react-native';
import { router } from 'expo-router';
import type * as NotificationsType from 'expo-notifications';

export interface NotificationPayload {
  alertId: string;
  metric: string;
  farmId?: string;
  title: string;
  body: string;
  severity?: 'critical' | 'warning' | 'info';
  timestamp?: string;
}

export interface PermissionStatus {
  granted: boolean;
  canAskAgain: boolean;
  status: string;
}

/**
 * Detect whether the application is running inside the Expo Go sandbox.
 * In Expo SDK 52+, Expo Go does not include native push/local notification
 * binaries (such as ExpoTopicSubscriptionModule). Native notifications require
 * a custom development build (npx expo run:android / eas build).
 */
function isRunningInExpoGoClient(): boolean {
  try {
    const { isRunningInExpoGo } = require('expo');
    if (typeof isRunningInExpoGo === 'function' && isRunningInExpoGo()) {
      return true;
    }
  } catch {
    // ignore
  }
  try {
    const Constants = require('expo-constants').default;
    return (
      Constants?.appOwnership === 'expo' ||
      Constants?.executionEnvironment === 'storeClient'
    );
  } catch {
    return false;
  }
}

let _cachedNotificationsModule: typeof NotificationsType | null = null;
let _hasCheckedModule = false;

function getNotificationsModule(): typeof NotificationsType | null {
  if (_hasCheckedModule) {
    return _cachedNotificationsModule;
  }
  _hasCheckedModule = true;

  // Disable native notification module evaluation in Expo Go or Web to avoid crashing on missing native modules
  if (Platform.OS === 'web' || isRunningInExpoGoClient()) {
    _cachedNotificationsModule = null;
    return null;
  }

  try {
    _cachedNotificationsModule = require('expo-notifications');
    return _cachedNotificationsModule;
  } catch (err) {
    console.warn('[NotificationService] expo-notifications native module not available:', err);
    _cachedNotificationsModule = null;
    return null;
  }
}

class NotificationService {
  private isInitialized = false;
  private responseSubscription: { remove: () => void } | null = null;
  private receivedSubscription: { remove: () => void } | null = null;
  private onNotificationTapCallback?: (data: any) => void;

  /**
   * Initializes notification channels, handler, and platform listeners.
   */
  async initialize(): Promise<void> {
    if (this.isInitialized) return;

    // Web fallback
    if (Platform.OS === 'web') {
      this.isInitialized = true;
      return;
    }

    // Expo Go fallback: native notification modules are absent by design
    if (isRunningInExpoGoClient()) {
      this.isInitialized = true;
      console.info(
        '[NotificationService] Running in Expo Go client. Native push/local notification channels require a custom development build (npx expo run:android). In-app alert banners and dashboard indicators remain fully active.'
      );
      return;
    }

    const Notifications = getNotificationsModule();
    if (!Notifications) {
      this.isInitialized = true;
      return;
    }

    try {
      // Configure default foreground presentation
      Notifications.setNotificationHandler({
        handleNotification: async () => ({
          shouldShowAlert: true,
          shouldPlaySound: true,
          shouldSetBadge: true,
          shouldShowBanner: true,
          shouldShowList: true,
        }),
      });

      // Android Channel setup
      if (Platform.OS === 'android') {
        await Notifications.setNotificationChannelAsync('sensor-alerts', {
          name: 'Sensor Threshold Alerts',
          description: 'High-priority alerts when environmental readings exceed safe thresholds',
          importance: Notifications.AndroidImportance.HIGH,
          vibrationPattern: [0, 250, 250, 250],
          lightColor: '#DC2626', // Red accent
          sound: 'default',
          enableLights: true,
          enableVibrate: true,
          showBadge: true,
        });
      }

      // Attach user tap response listener
      this.responseSubscription = Notifications.addNotificationResponseReceivedListener(
        (response: any) => {
          this.handleNotificationResponse(response);
        }
      );

      this.isInitialized = true;
    } catch (err) {
      console.warn('[NotificationService] Initialization error:', err);
      this.isInitialized = true;
    }
  }

  /**
   * Request notification permissions from the OS.
   */
  async requestPermissions(): Promise<PermissionStatus> {
    if (Platform.OS === 'web' || isRunningInExpoGoClient()) {
      return { granted: true, canAskAgain: true, status: 'granted' };
    }

    const Notifications = getNotificationsModule();
    if (!Notifications) {
      return { granted: true, canAskAgain: true, status: 'granted' };
    }

    try {
      const existing = await Notifications.getPermissionsAsync();
      if (existing.granted) {
        return { granted: true, canAskAgain: existing.canAskAgain, status: existing.status };
      }

      const requested = await Notifications.requestPermissionsAsync({
        ios: {
          allowAlert: true,
          allowBadge: true,
          allowSound: true,
        },
      });

      return {
        granted: requested.granted,
        canAskAgain: requested.canAskAgain,
        status: requested.status,
      };
    } catch (err) {
      console.warn('[NotificationService] Permission request failed:', err);
      return { granted: false, canAskAgain: false, status: 'denied' };
    }
  }

  /**
   * Check current notification permission status.
   */
  async checkPermissions(): Promise<boolean> {
    if (Platform.OS === 'web' || isRunningInExpoGoClient()) return true;
    const Notifications = getNotificationsModule();
    if (!Notifications) return true;
    try {
      const perms = await Notifications.getPermissionsAsync();
      return perms.granted;
    } catch {
      return false;
    }
  }

  /**
   * Send a local sensor alert notification.
   * Features:
   * - Red leaf emoji & styling in title
   * - Red icon tint on Android
   * - Single-line concise body
   * - Deep linking payload to alert detail screen
   */
  async sendSensorAlertNotification(payload: NotificationPayload): Promise<string | null> {
    // Check permission first
    const hasPermission = await this.checkPermissions();
    if (!hasPermission) {
      console.warn('[NotificationService] Notification skipped: Permission not granted');
      return null;
    }

    // Header styling: Red leaf indicator
    const formattedTitle = `🔴 🍃 VertiFarm Alert`;

    if (Platform.OS === 'web') {
      console.log(`[Web Notification] ${formattedTitle}: ${payload.body}`);
      return 'web-notification-id';
    }

    if (isRunningInExpoGoClient()) {
      console.log(`[Expo Go Alert] ${formattedTitle}: ${payload.body}`);
      return 'expo-go-simulated-notification-id';
    }

    const Notifications = getNotificationsModule();
    if (!Notifications) {
      console.log(`[Local Alert] ${formattedTitle}: ${payload.body}`);
      return 'simulated-notification-id';
    }

    try {
      const notificationId = await Notifications.scheduleNotificationAsync({
        content: {
          title: formattedTitle,
          body: payload.body,
          data: {
            alertId: payload.alertId,
            metric: payload.metric,
            farmId: payload.farmId || 'farm-1',
            timestamp: payload.timestamp || new Date().toISOString(),
          },
          sound: 'default',
          color: '#DC2626', // Red leaf theme
          badge: 1,
          categoryIdentifier: 'SENSOR_ALERT',
        },
        trigger: null, // deliver immediately
      });

      return notificationId;
    } catch (err) {
      console.warn('[NotificationService] Failed to schedule notification:', err);
      return null;
    }
  }

  /**
   * Handles notification tap interaction and routes to the relevant screen.
   */
  private handleNotificationResponse(response: any): void {
    try {
      const data = response?.notification?.request?.content?.data;
      if (this.onNotificationTapCallback) {
        this.onNotificationTapCallback(data);
      }

      if (data && data.alertId) {
        router.push(`/alerts/${data.alertId}` as any);
      } else if (data && data.metric) {
        router.push(`/live-data/${data.metric}` as any);
      } else {
        router.push('/(tabs)/alerts');
      }
    } catch (err) {
      console.warn('[NotificationService] Error handling notification tap routing:', err);
    }
  }

  /**
   * Set custom tap handler listener (used in UI testing or telemetry monitoring).
   */
  setOnNotificationTap(callback: (data: any) => void): void {
    this.onNotificationTapCallback = callback;
  }

  /**
   * Clean up listeners when needed.
   */
  cleanup(): void {
    if (this.responseSubscription) {
      this.responseSubscription.remove();
      this.responseSubscription = null;
    }
    if (this.receivedSubscription) {
      this.receivedSubscription.remove();
      this.receivedSubscription = null;
    }
    this.isInitialized = false;
  }
}

export const notificationService = new NotificationService();
