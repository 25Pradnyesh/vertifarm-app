/**
 * VertiFarm Configuration Constants
 */

export const config = {
  app: {
    name: 'VertiFarm',
    tagline: 'Monitor. Analyze. Grow Better.',
    version: '1.0.0',
  },

  api: {
    // To be configured later when backend is ready
    baseUrl: process.env.EXPO_PUBLIC_API_URL || '',
    timeout: 30000,
  },

  auth: {
    google: {
      webClientId: process.env.EXPO_PUBLIC_GOOGLE_WEB_CLIENT_ID || '',
      iosClientId: process.env.EXPO_PUBLIC_GOOGLE_IOS_CLIENT_ID || '',
      androidClientId: process.env.EXPO_PUBLIC_GOOGLE_ANDROID_CLIENT_ID || '',
      clientId: process.env.EXPO_PUBLIC_GOOGLE_CLIENT_ID || '',
    },
  },

  sensor: {
    updateInterval: 5000, // Target refresh rate: < 5 seconds
    offlineThreshold: 60000, // Mark sensor offline after 60s
  },

  camera: {
    autoCapturIntervalMinutes: 30,
  },

  alerts: {
    debounceDurationMs: 300000, // 5 minutes debounce for repeated alerts
  },

  charts: {
    timeRanges: [
      { label: '30m', minutes: 30 },
      { label: '1H', minutes: 60 },
      { label: '6H', minutes: 360 },
      { label: '24H', minutes: 1440 },
      { label: '7D', minutes: 10080 },
    ],
  },
};

export type Config = typeof config;
