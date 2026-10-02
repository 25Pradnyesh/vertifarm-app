import { config } from '../constants/config';
import { authService } from './authService';

/**
 * Universal Mobile API Client
 * Provides typed HTTP communication with the VertiFarm FastAPI backend.
 * Gracefully defers to mock data when EXPO_PUBLIC_API_URL is unconfigured.
 */
export const apiClient = {
  /**
   * Check if backend API URL is configured in environment
   */
  isConfigured(): boolean {
    const url = config.api.baseUrl;
    return Boolean(url && url.trim().length > 0 && !url.includes('placeholder'));
  },

  /**
   * Get formatted base URL with /api/v1 prefix
   */
  getBaseUrl(): string {
    const raw = config.api.baseUrl.trim().replace(/\/+$/, '');
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
        throw new Error(`API Error [${response.status}]: ${response.statusText}`);
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
        throw new Error(`API Error [${response.status}]: ${response.statusText}`);
      }

      return (await response.json()) as T;
    } finally {
      clearTimeout(timer);
    }
  },
};
