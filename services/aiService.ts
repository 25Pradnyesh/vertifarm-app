import { Platform } from 'react-native';
import { File, Paths, UploadType } from 'expo-file-system';
import { mockScans, mockCameraCapture } from '../data/mock/mockScans';
import { mockRecommendations } from '../data/mock/mockRecommendations';
import { AIScan, CameraCapture, RecommendationItem, ScanDiagnosisResponse } from '../types';
import { config } from '../constants/config';
import { apiClient } from './apiClient';
import { authService } from './authService';

/**
 * AI Service
 * Abstraction layer for AI plant health and camera monitoring.
 * Interacts with FastAPI backend when configured; falls back to mock data only in explicit demo mode.
 */

export const aiService = {
  /**
   * Diagnose a plant leaf image by uploading to the FastAPI AI disease classifier
   */
  async diagnoseImage(
    imageUri: string,
    options?: { filename?: string; mimeType?: string; farmId?: string }
  ): Promise<ScanDiagnosisResponse> {
    if (apiClient.isConfigured()) {
      const filename =
        options?.filename ||
        imageUri.split('/').pop()?.split('?')[0] ||
        'leaf_scan.jpg';
      const extension = filename.split('.').pop()?.toLowerCase();
      let mimeType = options?.mimeType || 'image/jpeg';
      if (extension === 'png') mimeType = 'image/png';
      else if (extension === 'webp') mimeType = 'image/webp';

      if (Platform.OS === 'web') {
        // Web: fetch URI as blob and append with filename
        let blob: Blob;
        try {
          const res = await fetch(imageUri);
          if (!res.ok) {
            throw new Error(`Failed to load image: HTTP ${res.status} ${res.statusText}`);
          }
          blob = await res.blob();
        } catch (err: any) {
          throw new Error(`Could not process leaf image for diagnosis: ${err?.message || err}`);
        }
        const formData = new FormData();
        const fileBlob = blob.type ? blob : new Blob([blob], { type: mimeType });
        formData.append('file', fileBlob, filename);
        if (options?.farmId) {
          formData.append('farm_id', options.farmId);
        }
        return await apiClient.postMultipart<ScanDiagnosisResponse>('/ai/scans/diagnose', formData);
      } else {
        // React Native (iOS/Android): Use expo-file-system native multipart upload.
        // This streams the file directly via Android OkHttp / iOS NSURLSession, bypassing
        // React Native's JS FormData bridge serialization that throws "Unsupported FormDataPart implementation".
        let localUri = imageUri;
        if (imageUri.startsWith('http://') || imageUri.startsWith('https://')) {
          const tempFile = new File(Paths.cache, `leaf_upload_${Date.now()}.jpg`);
          const downloaded = await File.downloadFileAsync(imageUri, tempFile, { idempotent: true });
          localUri = downloaded.uri;
        }

        const localFile = new File(localUri);
        const uploadUrl = `${apiClient.getBaseUrl()}/ai/scans/diagnose`;
        const headers: Record<string, string> = {
          Accept: 'application/json',
        };
        const currentUser = authService.getCurrentUser();
        if (currentUser?.accessToken) {
          headers['Authorization'] = `Bearer ${currentUser.accessToken}`;
        }

        const uploadResult = await localFile.upload(uploadUrl, {
          httpMethod: 'POST',
          uploadType: UploadType.MULTIPART,
          fieldName: 'file',
          mimeType,
          parameters: {
            farm_id: options?.farmId || 'farm-1',
          },
          headers,
        });

        if (uploadResult.status < 200 || uploadResult.status >= 300) {
          let errorDetail = uploadResult.body;
          try {
            const parsed = JSON.parse(uploadResult.body);
            errorDetail = parsed.detail || parsed.message || uploadResult.body;
          } catch {
            // Keep raw body if not JSON
          }
          throw new Error(`Diagnosis upload failed (${uploadResult.status}): ${errorDetail}`);
        }

        return JSON.parse(uploadResult.body) as ScanDiagnosisResponse;
      }
    }

    if (!config.demoMode) {
      throw new Error(
        'Backend API is not configured. Please set EXPO_PUBLIC_API_URL or run the backend server.'
      );
    }

    // Explicit demo mode fallback only when EXPO_PUBLIC_DEMO_MODE=true
    await new Promise((resolve) => setTimeout(resolve, 800));
    const isFenugreek = Math.random() > 0.5;
    return {
      id: `scan-mock-${Date.now()}`,
      plantType: isFenugreek ? 'Fenugreek' : 'Coriander',
      diseaseName: 'Healthy',
      isHealthy: true,
      confidence: 94.2,
      imageUrl: imageUri,
      timestamp: 'Just now',
      recommendations: [
        'Foliage demonstrates strong chlorophyll density and healthy leaf morphology.',
        'Maintain current EC, pH, and photoperiod targets.',
      ],
      predictedCrop: isFenugreek ? 'Fenugreek' : 'Coriander',
      predictedDisease: 'Healthy',
      rawClass: isFenugreek ? 'fenugreek_healthy' : 'coriander_healthy',
      isUncertain: false,
      uncertaintyMessage: null,
      topPredictions: [
        {
          class_name: isFenugreek ? 'fenugreek_healthy' : 'coriander_healthy',
          crop: isFenugreek ? 'Fenugreek' : 'Coriander',
          disease: 'Healthy',
          is_healthy: true,
          confidence: 94.2,
        },
      ],
      thresholdApplied: 0.6,
    };
  },

  /**
   * Get recent AI scans
   */
  async getRecentScans(): Promise<AIScan[]> {
    if (apiClient.isConfigured()) {
      try {
        return await apiClient.get<AIScan[]>('/ai/scans');
      } catch (err) {
        if (!config.demoMode) {
          throw err;
        }
        console.warn('[aiService] getRecentScans API failed, falling back to demo mode:', err);
      }
    } else if (!config.demoMode && !__DEV__) {
      throw new Error('API backend is not configured.');
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
      } catch (err: any) {
        if (err?.message?.includes('404')) {
          return null;
        }
        if (!config.demoMode) {
          throw err;
        }
        console.warn(`[aiService] getScanById API failed for ${id}, falling back to demo mode:`, err);
      }
    } else if (!config.demoMode && !__DEV__) {
      throw new Error('API backend is not configured.');
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
        if (!config.demoMode) {
          throw err;
        }
        console.warn('[aiService] getCameraStatus API failed, falling back to demo mode:', err);
      }
    } else if (!config.demoMode && !__DEV__) {
      throw new Error('API backend is not configured.');
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
        if (!config.demoMode) {
          throw err;
        }
        console.warn('[aiService] captureImage API failed, falling back to demo mode:', err);
      }
    } else if (!config.demoMode && !__DEV__) {
      throw new Error('API backend is not configured.');
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
        if (!config.demoMode) {
          throw err;
        }
        console.warn('[aiService] getRecommendations API failed, falling back to demo mode:', err);
      }
    } else if (!config.demoMode && !__DEV__) {
      throw new Error('API backend is not configured.');
    }
    await new Promise((resolve) => setTimeout(resolve, 200));

    if (tab) {
      return mockRecommendations.filter((rec) => rec.tab === tab);
    }

    return mockRecommendations;
  },
};
