import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { ScreenContainer } from '../../components/ui/ScreenContainer';
import { colors } from '../../constants/colors';
import { typography } from '../../constants/typography';
import { spacing } from '../../constants/spacing';

export default function AnalyticsScreen() {
  return (
    <ScreenContainer scroll={true} padding={true}>
      <View style={styles.header}>
        <Text style={styles.title}>Analytics</Text>
      </View>

      <View style={styles.placeholder}>
        <Text style={styles.placeholderText}>📊</Text>
        <Text style={styles.placeholderTitle}>Analytics Screen</Text>
        <Text style={styles.placeholderSubtitle}>
          Multi-metric trend graphs and insights will be displayed here.
        </Text>
      </View>
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  header: {
    marginTop: spacing.sm,
    marginBottom: spacing.xxl,
  },
  title: {
    fontSize: typography.fontSize.screenTitle,
    fontWeight: typography.fontWeight.bold,
    color: colors.textPrimary,
  },
  placeholder: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: spacing.massive,
  },
  placeholderText: {
    fontSize: 64,
    marginBottom: spacing.lg,
  },
  placeholderTitle: {
    fontSize: 18,
    fontWeight: typography.fontWeight.semibold,
    color: colors.textPrimary,
    marginBottom: spacing.sm,
  },
  placeholderSubtitle: {
    fontSize: 14,
    color: colors.textSecondary,
    textAlign: 'center',
    paddingHorizontal: spacing.xxl,
  },
});
