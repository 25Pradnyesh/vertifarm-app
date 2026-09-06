import { Farm } from '../../types';

export const mockFarms: Farm[] = [
  {
    id: 'farm-1',
    name: 'Greenhouse 1',
    location: 'Pune, Maharashtra, India',
    sensorCount: 12,
    zoneCount: 2,
    isActive: true,
    imageUrl: 'https://images.unsplash.com/photo-1585320806297-9794b3e4eeae?w=600',
    createdAt: '2025-01-15',
  },
  {
    id: 'farm-2',
    name: 'Greenhouse 2',
    location: 'Nashik, Maharashtra, India',
    sensorCount: 8,
    zoneCount: 1,
    isActive: false,
    imageUrl: 'https://images.unsplash.com/photo-1592417817098-8f3d6910a566?w=600',
    createdAt: '2025-02-20',
  },
];
