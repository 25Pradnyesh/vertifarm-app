import { AIScan, CameraCapture } from '../../types';

export const mockScans: AIScan[] = [
  {
    id: 'scan-1',
    plantType: 'Tomato Plant',
    diseaseName: 'Leaf Spot',
    isHealthy: false,
    confidence: 92.6,
    imageUrl: 'https://images.unsplash.com/photo-1592417817098-8f3d6910a566?w=600',
    timestamp: 'Today, 10:28 AM',
    recommendations: [
      'Remove affected leaves immediately',
      'Improve air circulation around canopy',
      'Apply suitable organic fungicide',
      'Monitor humidity levels closely',
      'Avoid overhead watering',
    ],
  },
  {
    id: 'scan-2',
    plantType: 'Lettuce Plant',
    diseaseName: 'Powdery Mildew',
    isHealthy: false,
    confidence: 87.3,
    imageUrl: 'https://images.unsplash.com/photo-1540420773420-3366772f4999?w=600',
    timestamp: 'Yesterday, 04:15 PM',
    recommendations: [
      'Isolate infected plants if possible',
      'Reduce ambient humidity below 65%',
      'Apply potassium bicarbonate or neem oil spray',
      'Increase space between crops for better airflow',
    ],
  },
  {
    id: 'scan-3',
    plantType: 'Lettuce Plant',
    diseaseName: 'Healthy',
    isHealthy: true,
    confidence: 98.1,
    imageUrl: 'https://images.unsplash.com/photo-1550989460-0adf9ea622e2?w=600',
    timestamp: '24 May 2025, 11:30 AM',
    recommendations: [
      'Plant is in healthy state',
      'Maintain current light and nutrient schedule',
      'Continue regular monitoring',
    ],
  },
];

export const mockCameraCapture: CameraCapture = {
  id: 'cam-1',
  cameraId: 'ESP32-CAM-01',
  zoneName: 'Greenhouse 1 - Zone 1',
  imageUrl: 'https://images.unsplash.com/photo-1530836369250-ef72a3f5cda8?w=800',
  timestamp: '10:30 AM',
  isLive: true,
  nextCaptureIn: '04:52',
};
