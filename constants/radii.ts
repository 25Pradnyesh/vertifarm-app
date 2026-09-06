/**
 * VertiFarm Border Radius System
 * Rounded card aesthetic matching design-reference.png
 */

export const radii = {
  none: 0,
  xs: 6,
  sm: 10,
  md: 12,
  lg: 16,
  xl: 18,
  xxl: 20,
  huge: 24,
  pill: 999, // Full pill shape for badges/chips

  // Semantic aliases
  button: 12,
  input: 12,
  card: 18,
  cardLarge: 20,
  badge: 999,
  chip: 999,
  modal: 20,
};

export type Radii = typeof radii;
