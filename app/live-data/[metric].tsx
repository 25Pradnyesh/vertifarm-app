import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { ScreenContainer } from '../../components/ui/ScreenContainer';
import { Card } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import { colors } from '../../constants/colors';
import { typography } from '../../constants/typography';
import { spacing } from '../../constants/spacing';
import { sensorService } from '../../services/sensorService';
import { TelemetrySummary, MetricType } from '../../types';

export default function LiveDataScreen() {
  const { metric } = useLocalSearchParams<{ metric: MetricType }>();
  const router = useRouter();
  const [data, setData] = useState<TelemetrySummary | null>(null);

  useEffect(() => {
    if (metric) {
      sensorService.getTelemetryByMetric(metric).then(setData);
    }
  }, [metric]);

  return (
    <ScreenContainer scroll={true} padding={true}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity
          style={styles.backButton}
          onPress={() => router.back()}
          hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
        >
          <Ionicons name="arrow-back" size={24} color={colors.textPrimary} />
        </TouchableOpacity>
        <Text style={styles.title}>Live Data</Text>
        <View style={{ width: 24 }} />
      </View>

      {/* Main Metric Card */}
      <Card variant="default" padding="large" style={styles.mainCard}>
        <View style={styles.metricHeader}>
          <Text style={styles.metricName}>{data?.name || 'Metric'}</Text>
          {data && <Badge status={data.status} label={data.statusLabel} />}
        </View>

        <Text style={styles.largeValue}>
          {data?.currentValue || '--'}
          <Text style={styles.unitText}> {data?.unit || ''}</Text>
        </Text>

        <View style={styles.placeholderChart}>
          <Text style={styles.chartText}>📈 Live Trend Graph</Text>
          <Text style={styles.chartSubtext}>
            Interactive SVG chart will be implemented here
          </Text>
        </View>
      </Card>

      {/* Stats Row */}
      <View style={styles.statsRow}>
        <Card variant="subtle" padding="medium" style={styles.statCard}>
          <Text style={styles.statLabel}>Min</Text>
          <Text style={styles.statValue}>
            {data?.min || '--'} {data?.unit}
          </Text>
        </Card>
        <Card variant="subtle" padding="medium" style={styles.statCard}>
          <Text style={styles.statLabel}>Max</Text>
          <Text style={styles.statValue}>
            {data?.max || '--'} {data?.unit}
          </Text>
        </Card>
        <Card variant="subtle" padding="medium" style={styles.statCard}>
          <Text style={styles.statLabel}>Avg</Text>
          <Text style={styles.statValue}>
            {data?.avg || '--'} {data?.unit}
          </Text>
        </Card>
      </View>

      {/* Optimal Range Card */}
      <Card variant="default" padding="medium" style={styles.optimalCard}>
        <View style={styles.optimalRow}>
          <Ionicons name="leaf" size={24} color={colors.leafGreen} />
          <View style={styles.optimalTextContainer}>
            <Text style={styles.optimalTitle}>Optimal Range</Text>
            <Text style={styles.optimalRange}>
              {data?.optimalMin} {data?.unit} – {data?.optimalMax} {data?.unit}
            </Text>
            <Text style={styles.optimalSubtext}>{data?.optimalText}</Text>
          </View>
        </View>
      </Card>
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: spacing.sm,
    marginBottom: spacing.xl,
  },
  backButton: {},
  title: {
    fontSize: typography.fontSize.navTitle,
    fontWeight: typography.fontWeight.bold,
    color: colors.textPrimary,
  },
  mainCard: {
    marginBottom: spacing.lg,
  },
  metricHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: spacing.sm,
  },
  metricName: {
    fontSize: 16,
    color: colors.textSecondary,
    fontWeight: typography.fontWeight.medium,
  },
  largeValue: {
    fontSize: typography.fontSize.largeMetric,
    fontWeight: typography.fontWeight.bold,
    color: colors.textPrimary,
    marginBottom: spacing.lg,
  },
  unitText: {
    fontSize: 18,
    fontWeight: typography.fontWeight.regular,
    color: colors.textSecondary,
  },
  placeholderChart: {
    height: 180,
    backgroundColor: colors.backgroundSecondary,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
    padding: spacing.md,
  },
  chartText: {
    fontSize: 16,
    fontWeight: typography.fontWeight.semibold,
    color: colors.textPrimary,
    marginBottom: spacing.xs,
  },
  chartSubtext: {
    fontSize: 12,
    color: colors.textSecondary,
    textAlign: 'center',
  },
  statsRow: {
    flexDirection: 'row',
    gap: spacing.md,
    marginBottom: spacing.lg,
  },
  statCard: {
    flex: 1,
    alignItems: 'center',
  },
  statLabel: {
    fontSize: 12,
    color: colors.textSecondary,
    marginBottom: 2,
  },
  statValue: {
    fontSize: 16,
    fontWeight: typography.fontWeight.bold,
    color: colors.textPrimary,
  },
  optimalCard: {
    marginBottom: spacing.xxl,
  },
  optimalRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  optimalTextContainer: {
    marginLeft: spacing.md,
  },
  optimalTitle: {
    fontSize: 14,
    color: colors.textSecondary,
  },
  optimalRange: {
    fontSize: 16,
    fontWeight: typography.fontWeight.bold,
    color: colors.textPrimary,
    marginTop: 2,
  },
  optimalSubtext: {
    fontSize: 12,
    color: colors.leafGreen,
    marginTop: 2,
  },
});
