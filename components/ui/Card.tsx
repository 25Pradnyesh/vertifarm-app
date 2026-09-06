import React, { ReactNode } from 'react';
import { View, StyleSheet, ViewStyle, TouchableOpacity, StyleProp } from 'react-native';
import { colors } from '../../constants/colors';
import { radii } from '../../constants/radii';
import { spacing } from '../../constants/spacing';

interface CardProps {
  children: ReactNode;
  variant?: 'default' | 'elevated' | 'subtle' | 'outline' | 'hero';
  padding?: 'none' | 'small' | 'medium' | 'large';
  onPress?: () => void;
  style?: StyleProp<ViewStyle>;
}

export function Card({
  children,
  variant = 'default',
  padding = 'medium',
  onPress,
  style,
}: CardProps) {
  const cardStyles: StyleProp<ViewStyle> = [
    styles.base,
    variant === 'default' && styles.default,
    variant === 'elevated' && styles.elevated,
    variant === 'subtle' && styles.subtle,
    variant === 'outline' && styles.outline,
    variant === 'hero' && styles.hero,
    padding === 'none' && styles.paddingNone,
    padding === 'small' && styles.paddingSmall,
    padding === 'medium' && styles.paddingMedium,
    padding === 'large' && styles.paddingLarge,
    style,
  ];

  if (onPress) {
    return (
      <TouchableOpacity style={cardStyles} onPress={onPress} activeOpacity={0.8}>
        {children}
      </TouchableOpacity>
    );
  }

  return <View style={cardStyles}>{children}</View>;
}

const styles = StyleSheet.create({
  base: {
    borderRadius: radii.card,
    overflow: 'hidden',
  },
  default: {
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.borderLight,
  },
  elevated: {
    backgroundColor: colors.surface,
    shadowColor: colors.shadowColor,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 8,
    elevation: 2,
  },
  subtle: {
    backgroundColor: colors.surfaceSubtle,
    borderWidth: 1,
    borderColor: colors.borderLight,
  },
  outline: {
    backgroundColor: 'transparent',
    borderWidth: 1.5,
    borderColor: colors.border,
  },
  hero: {
    backgroundColor: colors.primary,
    borderRadius: radii.cardLarge,
  },
  paddingNone: {
    padding: 0,
  },
  paddingSmall: {
    padding: spacing.sm,
  },
  paddingMedium: {
    padding: spacing.cardPadding,
  },
  paddingLarge: {
    padding: spacing.xxl,
  },
});
