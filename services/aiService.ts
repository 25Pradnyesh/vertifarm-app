import { mockScans, mockCameraCapture } from '../data/mock/mockScans';
import { mockRecommendations } from '../data/mock/mockRecommendations';
import { AIScan, CameraCapture, RecommendationItem } from '../types';

/**
 * AI Service
 * Abstraction layer for AI plant health and camera monitoring
 */

export const aiService = {
  /**
   * Get recent AI scans
   */
  async getRecentScans(): Promise<AIScan[]> {
    await new Promise((resolve) => setTimeout(resolve, 250));
    return mockScans;
  },

  /**
   * Get scan by ID
   */
  async getScanById(id: string): Promise<AIScan | null> {
    await new Promise((resolve) => setTimeout(resolve, 150));
    return mockScans.find((scan) => scan.id === id) || null;
  },

  /**
   * Get current camera capture status
   */
  async getCameraStatus(): Promise<CameraCapture> {
    await new Promise((resolve) => setTimeout(resolve, 200));
    return mockCameraCapture;
  },

  /**
   * Trigger manual camera capture
   */
  async captureImage(): Promise<boolean> {
    await new Promise((resolve) => setTimeout(resolve, 1000));
    console.log('Manual camera capture triggered');
    return true;
  },

  /**
   * Get recommendations
   */
  async getRecommendations(tab?: 'forYou' | 'general'): Promise<RecommendationItem[]> {
    await new Promise((resolve) => setTimeout(resolve, 200));

    if (tab) {
      return mockRecommendations.filter((rec) => rec.tab === tab);
    }

    return mockRecommendations;
  },
};
