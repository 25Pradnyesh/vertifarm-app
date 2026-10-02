import { Platform } from 'react-native';
import Constants from 'expo-constants';
import { config } from '../constants/config';
import { authService } from './authService';

/**
 * Universal Mobile API Client
 * Provides typed HTTP communication with the VertiFarm FastAPI backend.
 * Gracefully defers to mock data when backend is unreachable or unconfigured.
 */
export const apiClient = {
  /**
   * Get raw base URL with development LAN IP fallback for mobile devices
   */
  getRawBaseUrl(): string {
    const configured = config.api.baseUrl?.trim() || '';
    if (configured && !configured.includes('placeholder')) {
      if (Platform.OS !== 'web' && (configured.includes('localhost') || configured.includes('127.0.0.1'))) {
        const hostIp = Constants.expoConfig?.hostUri?.split(':')[0];
        if (hostIp) {
          return configured.replace('localhost', hostIp).replace('127.0.0.1', hostIp);
        }
      }
      return configured;
    }

    // Auto-detect host machine IP in Expo dev environment
    if (__DEV__) {
      const hostIp = Constants.expoConfig?.hostUri?.split(':')[0];
      if (hostIp && Platform.OS !== 'web') {
        return `http://${hostIp}:8000`;
      }
      if (Platform.OS === 'web') {
        return 'http://127.0.0.1:8000';
      }
    }

    return '';
  },

  /**
   * Check if backend API URL is configured or auto-detected in environment
   */
  isConfigured(): boolean {
    const url = this.getRawBaseUrl();
    return Boolean(url && url.trim().length > 0 && !url.includes('placeholder'));
  },

  /**
   * Get formatted base URL with /api/v1 prefix
   */
  getBaseUrl(): string {
    const raw = this.getRawBaseUrl().trim().replace(/\/+$/, '');
    if (raw.endsWith('/api/v1')) {
      return raw;
    }
    return `${raw}/api/v1`;
  },

  /**
   * Get WebSocket URL for streaming endpoints
   */
  getWsUrl(endpoint: string): string {
    const base = this.getBaseUrl().replace(/^http/, 'ws');
    return `${base}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;
  },


  /**
   * Get Authorization headers
   */
  getHeaders(): Record<string, string> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      Accept: 'application/json',
    };
    const currentUser = authService.getCurrentUser();
    if (currentUser?.accessToken) {
      headers['Authorization'] = `Bearer ${currentUser.accessToken}`;
    }
    return headers;
  },

  /**
   * Perform GET request
   */
  async get<T>(endpoint: string): Promise<T> {
    const url = `${this.getBaseUrl()}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), config.api.timeout);

    try {
      const response = await fetch(url, {
        method: 'GET',
        headers: this.getHeaders(),
        signal: controller.signal,
      });

      if (!response.ok) {
        let errorDetail = response.statusText;
        try {
          const errJson = await response.json();
          if (errJson?.detail) {
            errorDetail = typeof errJson.detail === 'string' ? errJson.detail : JSON.stringify(errJson.detail);
          }
        } catch {
          // Ignore JSON parse error on non-JSON response
        }
        throw new Error(`API Error [${response.status}]: ${errorDetail}`);
      }

      return (await response.json()) as T;
    } finally {
      clearTimeout(timer);
    }
  },

  /**
   * Perform POST request
   */
  async post<T>(endpoint: string, body?: any): Promise<T> {
    const url = `${this.getBaseUrl()}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), config.api.timeout);

    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: this.getHeaders(),
        body: body ? JSON.stringify(body) : undefined,
        signal: controller.signal,
      });

      if (!response.ok) {
        let errorDetail = response.statusText;
        try {
          const errJson = await response.json();
          if (errJson?.detail) {
            errorDetail = typeof errJson.detail === 'string' ? errJson.detail : JSON.stringify(errJson.detail);
          }
        } catch {
          // Ignore JSON parse error on non-JSON response
        }
        throw new Error(`API Error [${response.status}]: ${errorDetail}`);
      }

      return (await response.json()) as T;
    } finally {
      clearTimeout(timer);
    }
  },

  /**
   * Perform POST request with FormData (multipart/form-data)
   */
  async postMultipart<T>(endpoint: string, formData: FormData): Promise<T> {
    const url = `${this.getBaseUrl()}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), config.api.timeout);

    const headers: Record<string, string> = {
      Accept: 'application/json',
    };
    const currentUser = authService.getCurrentUser();
    if (currentUser?.accessToken) {
      headers['Authorization'] = `Bearer ${currentUser.accessToken}`;
    }

    try {
      const response = await fetch(url, {
        method: 'POST',
        headers,
        body: formData,
        signal: controller.signal,
      });

      if (!response.ok) {
        let errorDetail = response.statusText;
        try {
          const errJson = await response.json();
          if (errJson?.detail) {
            errorDetail = typeof errJson.detail === 'string' ? errJson.detail : JSON.stringify(errJson.detail);
          }
        } catch {
          // Ignore JSON parse failure on error body
        }
        throw new Error(`API Error [${response.status}]: ${errorDetail}`);
      }

      return (await response.json()) as T;
    } finally {
      clearTimeout(timer);
    }
  },
};
