/**
 * VertiFarm TypeScript Domain Models
 * Structured according to PRD section 7.2 and 8
 */

export type StatusLevel = 'healthy' | 'warning' | 'critical' | 'offline' | 'info';

export type MetricType =
  | 'temperature'
  | 'humidity'
  | 'soilMoisture'
  | 'ph'
  | 'tds'
  | 'light';

export interface Farm {
  id: string;
  name: string;
  location: string;
  sensorCount: number;
  zoneCount: number;
  isActive: boolean;
  imageUrl?: string;
  createdAt: string;
}

export interface Zone {
  id: string;
  farmId: string;
  name: string;
  crop: string;
  sensorCount: number;
}

export interface SensorDevice {
  id: string;
  name: string;
  type: string; // e.g., 'DHT22', 'Capacitive', 'Analog', 'BH1750', 'ESP32-CAM'
  metric: MetricType | 'camera';
  zoneId: string;
  zoneName: string;
  status: 'active' | 'warning' | 'offline';
  lastSeen: string;
  batteryLevel?: number;
}

export interface SensorReading {
  id: string;
  sensorId: string;
  metric: MetricType;
  value: number;
  unit: string;
  status: StatusLevel;
  statusLabel?: string;
  timestamp: string;
}

export interface TelemetrySummary {
  metric: MetricType;
  name: string;
  currentValue: number;
  unit: string;
  status: StatusLevel;
  statusLabel: string;
  min: number;
  max: number;
  avg: number;
  optimalMin: number;
  optimalMax: number;
  optimalText: string;
  trend: number[]; // Array of values for line graphs
  timestamps: string[]; // Corresponding timestamps
}

export interface AlertItem {
  id: string;
  farmId: string;
  zoneId: string;
  zoneName: string;
  metric: MetricType;
  severity: 'critical' | 'warning' | 'info';
  title: string;
  description: string;
  currentValue: string;
  thresholdValue: string;
  timestamp: string;
  isResolved: boolean;
  recommendation: string;
}

export interface AIScan {
  id: string;
  plantType: string;
  diseaseName: string;
  isHealthy: boolean;
  confidence: number; // e.g., 92.6
  imageUrl: string;
  timestamp: string;
  recommendations: string[];
}

export interface CameraCapture {
  id: string;
  cameraId: string;
  zoneName: string;
  imageUrl: string;
  timestamp: string;
  isLive: boolean;
  nextCaptureIn: string;
}

export interface RecommendationItem {
  id: string;
  category: 'irrigation' | 'ph' | 'nutrition' | 'environment' | 'disease';
  title: string;
  description: string;
  priority: 'high' | 'medium' | 'low';
  tab: 'forYou' | 'general';
  actionableLink?: string;
}

export interface UserProfile {
  id: string;
  name: string;
  role: string;
  farmName: string;
  email: string;
  avatarUrl?: string;
}

export interface AuthUser extends UserProfile {
  authProvider?: 'google' | 'email' | 'phone' | 'guest';
  googleId?: string;
  accessToken?: string;
  idToken?: string;
  createdAt?: string;
}

