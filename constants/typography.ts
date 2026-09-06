/**
 * VertiFarm Typography System
 * Clean sans-serif hierarchy matching design-reference.png
 */

export const typography = {
  // Font Families
  fontFamily: {
    regular: 'System',
    medium: 'System',
    semiBold: 'System',
    bold: 'System',
  },

  // Font Sizes
  fontSize: {
    // Titles
    screenTitle: 26, // Large screen headers (Dashboard, Analytics)
    largeMetric: 32, // Large sensor values (32.6°C)
    cardTitle: 16, // Card/Section headers
    sectionTitle: 20, // Section headers (WHAT'S HAPPENING?)

    // Body & Interface
    body: 14, // Standard body text
    bodyLarge: 15, // Slightly larger body
    caption: 12, // Timestamps, metadata, secondary
    small: 11, // Very small labels, badge text

    // Buttons & Inputs
    button: 15, // Button text
    input: 15, // Input field text
    label: 13, // Input labels

    // Navigation
    tab: 11, // Bottom tab labels
    navTitle: 17, // Navigation header titles
  },

  // Font Weights
  fontWeight: {
    regular: '400' as const,
    medium: '500' as const,
    semibold: '600' as const,
    bold: '700' as const,
  },

  // Line Heights
  lineHeight: {
    tight: 1.2,
    normal: 1.4,
    relaxed: 1.6,
    loose: 1.8,
  },

  // Letter Spacing
  letterSpacing: {
    tight: -0.5,
    normal: 0,
    wide: 0.5,
  },
};

export type Typography = typeof typography;
