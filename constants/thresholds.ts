import { MetricType, StatusLevel } from '../types';

/**
 * Agronomic Threshold and Physical Limit Definitions
 * Central source of truth for VertiFarm sensor monitoring across mobile client.
 */

export interface MetricThresholdConfig {
  metric: MetricType;
  name: string;
  unit: string;
  physicalMin: number;
  physicalMax: number;
  optimalMin: number;
  optimalMax: number;
  warningMin: number;
  warningMax: number;
  hysteresis: number;
  recommendations: {
    low: string;
    high: string;
    normal: string;
  };
}

export const SENSOR_THRESHOLDS: Record<MetricType, MetricThresholdConfig> = {
  temperature: {
    metric: 'temperature',
    name: 'Temperature',
    unit: '°C',
    physicalMin: -40.0,
    physicalMax: 100.0,
    optimalMin: 20.0,
    optimalMax: 30.0,
    warningMin: 15.0,
    warningMax: 35.0,
    hysteresis: 0.5,
    recommendations: {
      low: 'Temperature is below optimal. Check thermal curtains and activate supplemental heating.',
      high: 'Temperature is elevated. Check ventilation systems, increase airflow, or activate cooling equipment.',
      normal: 'Temperature is within optimal range for healthy canopy growth.',
    },
  },
  humidity: {
    metric: 'humidity',
    name: 'Humidity',
    unit: '%',
    physicalMin: 0.0,
    physicalMax: 100.0,
    optimalMin: 60.0,
    optimalMax: 80.0,
    warningMin: 40.0,
    warningMax: 90.0,
    hysteresis: 1.0,
    recommendations: {
      low: 'Humidity is too low. Activate greenhouse misting/humidifiers to avoid excessive crop transpiration.',
      high: 'Humidity is elevated. Increase ventilation and exhaust fans to prevent fungal disease development.',
      normal: 'Relative humidity is well balanced for transpiration and nutrient uptake.',
    },
  },
  soilMoisture: {
    metric: 'soilMoisture',
    name: 'Soil Moisture',
    unit: '%',
    physicalMin: 0.0,
    physicalMax: 100.0,
    optimalMin: 40.0,
    optimalMax: 60.0,
    warningMin: 30.0,
    warningMax: 75.0,
    hysteresis: 1.0,
    recommendations: {
      low: 'Irrigation is recommended to maintain optimal soil moisture for healthy plant growth.',
      high: 'Soil moisture is oversaturated. Suspend irrigation cycle to prevent root rot and hypoxia.',
      normal: 'Substrate moisture level is optimal for root zone respiration.',
    },
  },
  ph: {
    metric: 'ph',
    name: 'Soil pH',
    unit: 'pH',
    physicalMin: 0.0,
    physicalMax: 14.0,
    optimalMin: 6.0,
    optimalMax: 7.0,
    warningMin: 5.5,
    warningMax: 7.5,
    hysteresis: 0.1,
    recommendations: {
      low: 'pH is acidic. Introduce pH-up or alkaline buffering to prevent micronutrient lockout.',
      high: 'pH is slightly high. Add organic matter or pH down solution to lower the pH level.',
      normal: 'Substrate pH provides optimal nutrient availability.',
    },
  },
  tds: {
    metric: 'tds',
    name: 'TDS',
    unit: 'ppm',
    physicalMin: 0.0,
    physicalMax: 5000.0,
    optimalMin: 500.0,
    optimalMax: 800.0,
    warningMin: 400.0,
    warningMax: 1000.0,
    hysteresis: 10.0,
    recommendations: {
      low: 'Nutrient concentration is depleted. Replenish standard A+B nutrient reservoir dosage.',
      high: 'Nutrient concentration is high. Dilute irrigation reservoir with clean fresh water.',
      normal: 'TDS is in good range. Maintain current nutrient concentration.',
    },
  },
  light: {
    metric: 'light',
    name: 'Light Intensity',
    unit: 'Lux',
    physicalMin: 0.0,
    physicalMax: 150000.0,
    optimalMin: 1000.0,
    optimalMax: 2000.0,
    warningMin: 500.0,
    warningMax: 3000.0,
    hysteresis: 50.0,
    recommendations: {
      low: 'Light intensity is insufficient for optimal photosynthesis. Activate supplemental grow lights.',
      high: 'Light intensity too high. Deploy shade screens or reduce artificial lighting to prevent leaf scorch.',
      normal: 'Photosynthetic photon flux is within target range.',
    },
  },
};

export interface ThresholdEvaluation {
  isValid: boolean;
  status: StatusLevel;
  severity: 'critical' | 'warning' | 'info';
  statusLabel: string;
  isViolation: boolean;
  violationDirection?: 'low' | 'high';
  title: string;
  notificationBody: string;
  currentValueFormatted: string;
  thresholdValueFormatted: string;
  recommendation: string;
}

/**
 * Format numeric value with metric-specific decimal precision
 */
export function formatMetricValue(metric: MetricType, value: number): string {
  if (metric === 'ph') {
    return value.toFixed(2);
  }
  if (metric === 'tds' || metric === 'light') {
    return Math.round(value).toLocaleString();
  }
  return value.toFixed(1);
}

/**
 * Evaluates a single sensor reading against configured agronomic thresholds.
 * Validates against missing, non-numeric, non-finite, and physical limits.
 * Applies hysteresis when recovering from an existing violation to prevent boundary flutter.
 */
export function evaluateSensorThreshold(
  metric: MetricType,
  value: any,
  activeViolationDirection?: 'low' | 'high' | null
): ThresholdEvaluation {
  const config = SENSOR_THRESHOLDS[metric];
  if (!config) {
    return {
      isValid: false,
      status: 'offline',
      severity: 'info',
      statusLabel: 'Unknown Metric',
      isViolation: false,
      title: 'Invalid Metric',
      notificationBody: '',
      currentValueFormatted: String(value),
      thresholdValueFormatted: '--',
      recommendation: '',
    };
  }

  // 1. Validate missing or malformed values
  if (value === null || value === undefined || value === '') {
    return {
      isValid: false,
      status: 'offline',
      severity: 'info',
      statusLabel: 'No Data',
      isViolation: false,
      title: 'Sensor Unavailable',
      notificationBody: '',
      currentValueFormatted: '--',
      thresholdValueFormatted: `${config.optimalMin}–${config.optimalMax} ${config.unit}`,
      recommendation: 'Verify sensor wiring and edge controller connectivity.',
    };
  }

  const num = typeof value === 'number' ? value : parseFloat(value);
  if (isNaN(num) || !isFinite(num)) {
    return {
      isValid: false,
      status: 'offline',
      severity: 'info',
      statusLabel: 'Malformed',
      isViolation: false,
      title: 'Malformed Reading',
      notificationBody: '',
      currentValueFormatted: 'NaN',
      thresholdValueFormatted: `${config.optimalMin}–${config.optimalMax} ${config.unit}`,
      recommendation: 'Check edge telemetry ADC conversion format.',
    };
  }

  // 2. Validate physical bounds (hardware failure or disconnection)
  if (num < config.physicalMin || num > config.physicalMax) {
    return {
      isValid: false,
      status: 'offline',
      severity: 'info',
      statusLabel: 'Out of Bounds',
      isViolation: false,
      title: 'Sensor Out of Bounds',
      notificationBody: '',
      currentValueFormatted: `${num} ${config.unit}`,
      thresholdValueFormatted: `[${config.physicalMin}, ${config.physicalMax}] ${config.unit}`,
      recommendation: 'Reading is outside physical hardware limits. Inspect sensor hardware.',
    };
  }

  const formattedVal = `${formatMetricValue(metric, num)} ${config.unit}`;

  // 3. Apply hysteresis recovery if currently in violation
  if (activeViolationDirection === 'high') {
    // Has not fully recovered below optimalMax - hysteresis
    const recoveryThreshold = config.optimalMax - config.hysteresis;
    if (num > recoveryThreshold) {
      // Still in high violation
      const isCritical = num > config.warningMax;
      const severity: 'critical' | 'warning' = isCritical ? 'critical' : 'warning';
      return {
        isValid: true,
        status: severity,
        severity,
        statusLabel: isCritical ? 'Critical High' : 'High',
        isViolation: true,
        violationDirection: 'high',
        title: `${config.name} is High`,
        notificationBody: `High ${config.name.toLowerCase()} detected: ${formattedVal} — Normal range: ${config.optimalMin}–${config.optimalMax} ${config.unit}`,
        currentValueFormatted: formattedVal,
        thresholdValueFormatted: `> ${config.optimalMax} ${config.unit}`,
        recommendation: config.recommendations.high,
      };
    }
  } else if (activeViolationDirection === 'low') {
    // Has not fully recovered above optimalMin + hysteresis
    const recoveryThreshold = config.optimalMin + config.hysteresis;
    if (num < recoveryThreshold) {
      // Still in low violation
      const isCritical = num < config.warningMin;
      const severity: 'critical' | 'warning' = isCritical ? 'critical' : 'warning';
      return {
        isValid: true,
        status: severity,
        severity,
        statusLabel: isCritical ? 'Critical Low' : 'Low',
        isViolation: true,
        violationDirection: 'low',
        title: `${config.name} is Low`,
        notificationBody: `${config.name} too low: ${formattedVal} — Minimum: ${config.optimalMin} ${config.unit}`,
        currentValueFormatted: formattedVal,
        thresholdValueFormatted: `< ${config.optimalMin} ${config.unit}`,
        recommendation: config.recommendations.low,
      };
    }
  }

  // 4. Standard evaluation
  if (num > config.warningMax) {
    return {
      isValid: true,
      status: 'critical',
      severity: 'critical',
      statusLabel: 'Critical High',
      isViolation: true,
      violationDirection: 'high',
      title: `${config.name} is Critical`,
      notificationBody: `${config.name} critical: ${formattedVal} — Maximum: ${config.optimalMax} ${config.unit}`,
      currentValueFormatted: formattedVal,
      thresholdValueFormatted: `> ${config.optimalMax} ${config.unit}`,
      recommendation: config.recommendations.high,
    };
  }

  if (num < config.warningMin) {
    return {
      isValid: true,
      status: 'critical',
      severity: 'critical',
      statusLabel: 'Critical Low',
      isViolation: true,
      violationDirection: 'low',
      title: `${config.name} is Critical`,
      notificationBody: `${config.name} critical: ${formattedVal} — Minimum: ${config.optimalMin} ${config.unit}`,
      currentValueFormatted: formattedVal,
      thresholdValueFormatted: `< ${config.optimalMin} ${config.unit}`,
      recommendation: config.recommendations.low,
    };
  }

  if (num > config.optimalMax) {
    return {
      isValid: true,
      status: 'warning',
      severity: 'warning',
      statusLabel: 'High',
      isViolation: true,
      violationDirection: 'high',
      title: `${config.name} is High`,
      notificationBody: `High ${config.name.toLowerCase()} detected: ${formattedVal} — Normal range: ${config.optimalMin}–${config.optimalMax} ${config.unit}`,
      currentValueFormatted: formattedVal,
      thresholdValueFormatted: `> ${config.optimalMax} ${config.unit}`,
      recommendation: config.recommendations.high,
    };
  }

  if (num < config.optimalMin) {
    return {
      isValid: true,
      status: 'warning',
      severity: 'warning',
      statusLabel: 'Low',
      isViolation: true,
      violationDirection: 'low',
      title: `${config.name} is Low`,
      notificationBody: `${config.name} too low: ${formattedVal} — Minimum: ${config.optimalMin} ${config.unit}`,
      currentValueFormatted: formattedVal,
      thresholdValueFormatted: `< ${config.optimalMin} ${config.unit}`,
      recommendation: config.recommendations.low,
    };
  }

  // Normal / healthy
  return {
    isValid: true,
    status: 'healthy',
    severity: 'info',
    statusLabel: metric === 'ph' && num < 6.8 ? 'Slightly Acidic' : 'Normal',
    isViolation: false,
    title: `${config.name} Normal`,
    notificationBody: '',
    currentValueFormatted: formattedVal,
    thresholdValueFormatted: `${config.optimalMin}–${config.optimalMax} ${config.unit}`,
    recommendation: config.recommendations.normal,
  };
}
