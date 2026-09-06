import { TelemetrySummary } from '../../types';

// Generate realistic time series data for the past 24 hours
const generateTimeSeries = (baseValue: number, variance: number, points: number = 24) => {
  const data: number[] = [];
  const timestamps: string[] = [];
  const now = new Date();

  for (let i = points - 1; i >= 0; i--) {
    const time = new Date(now.getTime() - i * 60 * 60 * 1000); // Hourly data
    const randomVariance = (Math.random() - 0.5) * variance;
    data.push(Number((baseValue + randomVariance).toFixed(2)));
    timestamps.push(time.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }));
  }

  return { data, timestamps };
};

const tempSeries = generateTimeSeries(32.6, 4);
const humiditySeries = generateTimeSeries(65.4, 8);
const soilMoistureSeries = generateTimeSeries(48, 6);
const phSeries = generateTimeSeries(6.58, 0.3);
const tdsSeries = generateTimeSeries(620, 50);
const lightSeries = generateTimeSeries(1200, 200);

export const mockTelemetry: TelemetrySummary[] = [
  {
    metric: 'temperature',
    name: 'Temperature',
    currentValue: 32.6,
    unit: '°C',
    status: 'healthy',
    statusLabel: 'Normal',
    min: 24.1,
    max: 33.8,
    avg: 32.6,
    optimalMin: 20,
    optimalMax: 30,
    optimalText: 'For healthy growth',
    trend: tempSeries.data,
    timestamps: tempSeries.timestamps,
  },
  {
    metric: 'humidity',
    name: 'Humidity',
    currentValue: 65.4,
    unit: '%',
    status: 'healthy',
    statusLabel: 'Normal',
    min: 58.2,
    max: 72.1,
    avg: 65.4,
    optimalMin: 60,
    optimalMax: 80,
    optimalText: 'For healthy growth',
    trend: humiditySeries.data,
    timestamps: humiditySeries.timestamps,
  },
  {
    metric: 'soilMoisture',
    name: 'Soil Moisture',
    currentValue: 48,
    unit: '%',
    status: 'healthy',
    statusLabel: 'Normal',
    min: 42,
    max: 54,
    avg: 48,
    optimalMin: 40,
    optimalMax: 60,
    optimalText: 'For healthy growth',
    trend: soilMoistureSeries.data,
    timestamps: soilMoistureSeries.timestamps,
  },
  {
    metric: 'ph',
    name: 'Soil pH',
    currentValue: 6.58,
    unit: 'pH',
    status: 'healthy',
    statusLabel: 'Slightly Acidic',
    min: 6.2,
    max: 6.9,
    avg: 6.58,
    optimalMin: 6.0,
    optimalMax: 7.0,
    optimalText: 'For healthy growth',
    trend: phSeries.data,
    timestamps: phSeries.timestamps,
  },
  {
    metric: 'tds',
    name: 'TDS',
    currentValue: 620,
    unit: 'ppm',
    status: 'healthy',
    statusLabel: 'Normal',
    min: 580,
    max: 670,
    avg: 620,
    optimalMin: 500,
    optimalMax: 800,
    optimalText: 'For healthy growth',
    trend: tdsSeries.data,
    timestamps: tdsSeries.timestamps,
  },
  {
    metric: 'light',
    name: 'Light',
    currentValue: 1200,
    unit: 'lux',
    status: 'healthy',
    statusLabel: 'Normal',
    min: 950,
    max: 1350,
    avg: 1200,
    optimalMin: 1000,
    optimalMax: 1500,
    optimalText: 'For healthy growth',
    trend: lightSeries.data,
    timestamps: lightSeries.timestamps,
  },
];
