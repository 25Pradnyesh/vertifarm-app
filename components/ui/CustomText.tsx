import React from 'react';
import { Text, TextProps, StyleSheet } from 'react-native';
import { colors } from '../../constants/colors';
import { typography } from '../../constants/typography';

interface CustomTextProps extends TextProps {
  variant?: 'title' | 'body' | 'caption' | 'button' | 'label';
  weight?: 'regular' | 'medium' | 'semibold' | 'bold';
  color?: string;
}

export function CustomText({
  variant = 'body',
  weight = 'regular',
  color = colors.textPrimary,
  style,
  children,
  ...props
}: CustomTextProps) {
  const textStyle = [
    styles.base,
    variant === 'title' && styles.title,
    variant === 'body' && styles.body,
    variant === 'caption' && styles.caption,
    variant === 'button' && styles.button,
    variant === 'label' && styles.label,
    { fontWeight: typography.fontWeight[weight], color },
    style,
  ];

  return (
    <Text style={textStyle} {...props}>
      {children}
    </Text>
  );
}

const styles = StyleSheet.create({
  base: {
    fontFamily: typography.fontFamily.regular,
  },
  title: {
    fontSize: typography.fontSize.screenTitle,
    lineHeight: typography.fontSize.screenTitle * typography.lineHeight.tight,
  },
  body: {
    fontSize: typography.fontSize.body,
    lineHeight: typography.fontSize.body * typography.lineHeight.normal,
  },
  caption: {
    fontSize: typography.fontSize.caption,
    lineHeight: typography.fontSize.caption * typography.lineHeight.normal,
  },
  button: {
    fontSize: typography.fontSize.button,
    lineHeight: typography.fontSize.button * typography.lineHeight.tight,
  },
  label: {
    fontSize: typography.fontSize.label,
    lineHeight: typography.fontSize.label * typography.lineHeight.normal,
  },
});
