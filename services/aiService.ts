import { mockScans, mockCameraCapture } from '../data/mock/mockScans';
import { mockRecommendations } from '../data/mock/mockRecommendations';
import { AIScan, CameraCapture, RecommendationItem } from '../types';
import { apiClient } from './apiClient';

/**
 * AI Service
 * Abstraction layer for AI plant health and camera monitoring.
 * Interacts with FastAPI backend when configured; falls back to mock data.
 */

export const aiService = {
  /**
   * Get recent AI scans
   */
  async getRecentScans(): Promise<AIScan[]> {
    if (apiClient.isConfigured()) {
      try {
        return await apiClient.get<AIScan[]>('/ai/scans');
      } catch (err) {
        console.warn('[aiService] getRecentScans API failed, falling back to mock:', err);
      }
    }
    await new Promise((resolve) => setTimeout(resolve, 250));
    return mockScans;
  },

  /**
   * Get scan by ID
   */
  async getScanById(id: string): Promise<AIScan | null> {
    if (apiClient.isConfigured()) {
      try {
        return await apiClient.get<AIScan>(`/ai/scans/${id}`);
      } catch (err) {
        console.warn(`[aiService] getScanById API failed for ${id}, falling back to mock:`, err);
      }
    }
    await new Promise((resolve) => setTimeout(resolve, 150));
    return mockScans.find((scan) => scan.id === id) || null;
  },

  /**
   * Get current camera capture status
   */
  async getCameraStatus(): Promise<CameraCapture> {
    if (apiClient.isConfigured()) {
      try {
        return await apiClient.get<CameraCapture>('/ai/camera/status');
      } catch (err) {
        console.warn('[aiService] getCameraStatus API failed, falling back to mock:', err);
      }
    }
    await new Promise((resolve) => setTimeout(resolve, 200));
    return mockCameraCapture;
  },

  /**
   * Trigger manual camera capture
   */
  async captureImage(): Promise<boolean> {
    if (apiClient.isConfigured()) {
      try {
        await apiClient.post<{ queued: boolean; job_id: string }>('/ai/camera/capture');
        return true;
      } catch (err) {
        console.warn('[aiService] captureImage API failed, falling back to mock:', err);
      }
    }
    await new Promise((resolve) => setTimeout(resolve, 1000));
    console.log('Manual camera capture triggered');
    return true;
  },

  /**
   * Get recommendations
   */
  async getRecommendations(tab?: 'forYou' | 'general'): Promise<RecommendationItem[]> {
    if (apiClient.isConfigured()) {
      try {
        const query = tab ? `?tab=${tab}` : '';
        return await apiClient.get<RecommendationItem[]>(`/recommendations${query}`);
      } catch (err) {
        console.warn('[aiService] getRecommendations API failed, falling back to mock:', err);
      }
    }
    await new Promise((resolve) => setTimeout(resolve, 200));

    if (tab) {
      return mockRecommendations.filter((rec) => rec.tab === tab);
    }

    return mockRecommendations;
  },
};
