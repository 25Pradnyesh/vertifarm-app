/**
 * VertiFarm Spacing System
 * Consistent spacing scale matching design-reference.png
 */

export const spacing = {
  xs: 4,
  sm: 8,
  md: 12,
  lg: 16,
  xl: 20,
  xxl: 24,
  xxxl: 32,
  huge: 40,
  massive: 48,

  // Semantic aliases for common use cases
  cardPadding: 16,
  cardGap: 12,
  screenPadding: 20,
  sectionGap: 24,
  listItemGap: 12,
  buttonPadding: 16,
  inputPadding: 14,
  iconSize: 24,
  iconSizeLarge: 32,
  iconSizeSmall: 20,
};

export type Spacing = typeof spacing;
