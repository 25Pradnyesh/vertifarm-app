import { RecommendationItem } from '../../types';

export const mockRecommendations: RecommendationItem[] = [
  {
    id: 'rec-1',
    category: 'irrigation',
    title: 'Irrigation Recommendation',
    description: 'Soil moisture is below optimal range. Consider irrigation.',
    priority: 'high',
    tab: 'forYou',
    actionableLink: '/live-data/soilMoisture',
  },
  {
    id: 'rec-2',
    category: 'ph',
    title: 'pH Adjustment',
    description: 'pH is slightly high. Add organic matter or pH down solution.',
    priority: 'medium',
    tab: 'forYou',
    actionableLink: '/live-data/ph',
  },
  {
    id: 'rec-3',
    category: 'nutrition',
    title: 'Nutrition Management',
    description: 'TDS is in good range. Maintain current nutrient concentration.',
    priority: 'low',
    tab: 'general',
    actionableLink: '/live-data/tds',
  },
  {
    id: 'rec-4',
    category: 'environment',
    title: 'Environmental Control',
    description: 'Maintain temperature between 20°C – 30°C for best results.',
    priority: 'low',
    tab: 'general',
    actionableLink: '/live-data/temperature',
  },
];
