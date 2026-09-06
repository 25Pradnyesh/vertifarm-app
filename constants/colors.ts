/**
 * VertiFarm Color System
 * Botanical SaaS aesthetic matching design-reference.png
 */

export const colors = {
  // Brand / Botanical Primary
  primary: '#1B3B2B', // Deep forest green - main brand & primary actions
  primaryLight: '#2D5A43',
  primaryDark: '#12281D',
  primaryMuted: '#E8F3ED',
  leafGreen: '#34A853', // Bright vibrant leaf icon accent
  leafGreenLight: '#E6F4EA',

  // Backgrounds & Surfaces
  background: '#F8F9F6', // Soft warm cream / off-white app background
  backgroundSecondary: '#F1F3EE',
  surface: '#FFFFFF', // Pure white card surfaces
  surfaceSubtle: '#F9FAF7', // Extremely subtle green-tinted card surface
  surfaceElevated: '#FFFFFF',

  // Typography / Content
  textPrimary: '#1A2E22', // Deep charcoal / near-black botanical
  textSecondary: '#5C6B62', // Muted gray-green secondary
  textMuted: '#8E9E94', // Light placeholder / caption
  textInverse: '#FFFFFF', // White text on dark green surfaces

  // Status System (Never rely on color alone)
  status: {
    healthy: {
      primary: '#2E7D32',
      background: '#E8F5E9',
      border: '#C8E6C9',
      text: '#1B5E20',
      label: 'Normal',
    },
    warning: {
      primary: '#D97706',
      background: '#FEF3C7',
      border: '#FDE68A',
      text: '#92400E',
      label: 'Warning',
    },
    critical: {
      primary: '#DC2626',
      background: '#FEE2E2',
      border: '#FECACA',
      text: '#991B1B',
      label: 'Attention',
    },
    offline: {
      primary: '#6B7280',
      background: '#F3F4F6',
      border: '#E5E7EB',
      text: '#374151',
      label: 'Offline',
    },
    info: {
      primary: '#0284C7',
      background: '#E0F2FE',
      border: '#BAE6FD',
      text: '#0369A1',
      label: 'Info',
    },
  },

  // Metric Specific Accent Colors (Matching Reference Chart Lines)
  metrics: {
    temperature: '#E53E3E', // Thermometer Red
    humidity: '#3182CE', // Droplet Blue
    soilMoisture: '#38A169', // Soil/Plant Green
    ph: '#805AD5', // Beaker Purple
    tds: '#0D9488', // Mineral Teal
    light: '#D97706', // Sun Amber/Yellow
  },

  // Borders & Dividers
  border: '#E6EAE5',
  borderLight: '#F0F3EF',
  borderDark: '#D0D8CF',
  divider: '#EBEFE9',

  // Bottom Navigation
  navBackground: '#FFFFFF',
  navBorder: '#E6EAE5',
  navActive: '#1B3B2B',
  navInactive: '#8E9E94',

  // Shadows
  shadowColor: '#000000',
};

export type Colors = typeof colors;
