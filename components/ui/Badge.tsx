import React from 'react';
import { View, Text, StyleSheet, ViewStyle, StyleProp } from 'react-native';
import { colors } from '../../constants/colors';
import { typography } from '../../constants/typography';
import { radii } from '../../constants/radii';
import { StatusLevel } from '../../types';

interface BadgeProps {
  status?: StatusLevel;
  label?: string;
  variant?: 'solid' | 'subtle' | 'outline';
  size?: 'small' | 'medium';
  style?: StyleProp<ViewStyle>;
}

export function Badge({
  status = 'healthy',
  label,
  variant = 'subtle',
  size = 'small',
  style,
}: BadgeProps) {
  const statusConfig = colors.status[status] || colors.status.healthy;
  const displayLabel = label || statusConfig.label;

  const badgeStyles: StyleProp<ViewStyle> = [
    styles.base,
    variant === 'subtle' && {
      backgroundColor: statusConfig.background,
      borderColor: statusConfig.border,
      borderWidth: 1,
    },
    variant === 'solid' && {
      backgroundColor: statusConfig.primary,
    },
    variant === 'outline' && {
      backgroundColor: 'transparent',
      borderColor: statusConfig.primary,
      borderWidth: 1.5,
    },
    size === 'small' && styles.small,
    size === 'medium' && styles.medium,
    style,
  ];

  const textColor = variant === 'solid' ? colors.textInverse : statusConfig.text;

  return (
    <View style={badgeStyles}>
      <Text
        style={[
          styles.text,
          { color: textColor },
          size === 'small' && styles.smallText,
          size === 'medium' && styles.mediumText,
        ]}
      >
        {displayLabel}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  base: {
    borderRadius: radii.badge,
    alignSelf: 'flex-start',
    alignItems: 'center',
    justifyContent: 'center',
  },
  small: {
    paddingHorizontal: 8,
    paddingVertical: 3,
  },
  medium: {
    paddingHorizontal: 12,
    paddingVertical: 5,
  },
  text: {
    fontWeight: typography.fontWeight.semibold,
  },
  smallText: {
    fontSize: typography.fontSize.small,
  },
  mediumText: {
    fontSize: typography.fontSize.label,
  },
});

