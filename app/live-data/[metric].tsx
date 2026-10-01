import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView, Dimensions } from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { ScreenContainer } from '../../components/ui/ScreenContainer';
import { Card } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import { SingleMetricChart } from '../../components/charts/SingleMetricChart';
import { colors } from '../../constants/colors';
import { typography } from '../../constants/typography';
import { spacing } from '../../constants/spacing';
import { radii } from '../../constants/radii';
import { sensorService } from '../../services/sensorService';
import { TelemetrySummary, MetricType } from '../../types';

const { width } = Dimensions.get('window');

const ALL_METRICS: { key: MetricType; label: string }[] = [
  { key: 'temperature', label: 'Temperature' },
  { key: 'humidity', label: 'Humidity' },
  { key: 'soilMoisture', label: 'Soil Moisture' },
  { key: 'ph', label: 'Soil pH' },
  { key: 'tds', label: 'TDS' },
  { key: 'light', label: 'Light' },
];

const TIME_RANGES = ['30m', '1H', '6H', '24H', '7D'];

export default function LiveDataScreen() {
  const { metric } = useLocalSearchParams<{ metric: MetricType }>();
  const router = useRouter();

  const [activeMetric, setActiveMetric] = useState<MetricType>(metric || 'temperature');
  const [data, setData] = useState<TelemetrySummary | null>(null);
  const [activeRange, setActiveRange] = useState('1H');
  const [showMetricPicker, setShowMetricPicker] = useState(false);

  useEffect(() => {
    if (metric) {
      setActiveMetric(metric);
    }
  }, [metric]);

  useEffect(() => {
    sensorService.getTelemetryByMetric(activeMetric).then(setData);
  }, [activeMetric]);

  const getMetricAccentColor = (m: MetricType) => {
    switch (m) {
      case 'temperature':
        return colors.leafGreen;
      case 'humidity':
        return colors.metrics.humidity;
      case 'soilMoisture':
        return colors.metrics.soilMoisture;
      case 'ph':
        return colors.metrics.ph;
      case 'tds':
        return colors.metrics.tds;
      case 'light':
        return colors.metrics.light;
      default:
        return colors.leafGreen;
    }
  };

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
        <TouchableOpacity
          style={styles.actionButton}
          onPress={() => router.push('/(tabs)/analytics')}
        >
          <Ionicons name="sparkles-outline" size={22} color={colors.textPrimary} />
        </TouchableOpacity>
      </View>

      {/* Metric Selector Dropdown Pill */}
      <View style={styles.dropdownWrapper}>
        <TouchableOpacity
          style={styles.dropdownButton}
          onPress={() => setShowMetricPicker(!showMetricPicker)}
          activeOpacity={0.7}
        >
          <Text style={styles.dropdownText}>{data?.name || 'Temperature'}</Text>
          <Ionicons
            name={showMetricPicker ? 'chevron-up' : 'chevron-down'}
            size={18}
            color={colors.textSecondary}
          />
        </TouchableOpacity>

        {showMetricPicker && (
          <Card variant="elevated" padding="small" style={styles.dropdownMenu}>
            {ALL_METRICS.map((item) => (
              <TouchableOpacity
                key={item.key}
                style={[
                  styles.dropdownItem,
                  activeMetric === item.key && styles.dropdownItemActive,
                ]}
                onPress={() => {
                  setActiveMetric(item.key);
                  setShowMetricPicker(false);
                }}
              >
                <Text
                  style={[
                    styles.dropdownItemText,
                    activeMetric === item.key && styles.dropdownItemTextActive,
                  ]}
                >
                  {item.label}
                </Text>
                {activeMetric === item.key && (
                  <Ionicons name="checkmark" size={16} color={colors.primary} />
                )}
              </TouchableOpacity>
            ))}
          </Card>
        )}
      </View>

      {/* Live Value & Status Header */}
      <View style={styles.valueRow}>
        <View style={styles.valueGroup}>
          <Text style={styles.largeValue}>
            {data?.currentValue !== undefined ? data.currentValue : '--'}
            <Text style={styles.unitText}> {data?.unit || ''}</Text>
          </Text>
          {data && (
            <Badge
              status={data.status}
              label={data.statusLabel}
              variant="subtle"
              style={styles.valueBadge}
            />
          )}
        </View>

        <TouchableOpacity style={styles.moreOptionsButton}>
          <Ionicons name="ellipsis-horizontal" size={20} color={colors.textSecondary} />
        </TouchableOpacity>
      </View>

      {/* Real SVG Trend Chart Card */}
      <Card variant="default" padding="medium" style={styles.chartCard}>
        <SingleMetricChart
          data={data?.trend || []}
          timestamps={data?.timestamps || []}
          color={getMetricAccentColor(activeMetric)}
          height={200}
          width={width - spacing.screenPadding * 2 - spacing.md * 2}
          unit={data?.unit}
        />
      </Card>

      {/* Time Range Filter Pills */}
      <View style={styles.timeRangeContainer}>
        {TIME_RANGES.map((range) => {
          const isActive = activeRange === range;
          return (
            <TouchableOpacity
              key={range}
              style={[styles.rangePill, isActive && styles.rangePillActive]}
              onPress={() => setActiveRange(range)}
              activeOpacity={0.7}
            >
              <Text style={[styles.rangeText, isActive && styles.rangeTextActive]}>
                {range}
              </Text>
            </TouchableOpacity>
          );
        })}
      </View>

      {/* 3 Stats in a Row (Min / Max / Avg) */}
      <View style={styles.statsRow}>
        <Card variant="default" padding="medium" style={styles.statCard}>
          <Text style={styles.statValue}>
            {data?.min ?? '--'}
            <Text style={styles.statUnit}> {data?.unit || ''}</Text>
          </Text>
          <Text style={styles.statLabel}>Min</Text>
        </Card>

        <Card variant="default" padding="medium" style={styles.statCard}>
          <Text style={styles.statValue}>
            {data?.max ?? '--'}
            <Text style={styles.statUnit}> {data?.unit || ''}</Text>
          </Text>
          <Text style={styles.statLabel}>Max</Text>
        </Card>

        <Card variant="default" padding="medium" style={styles.statCard}>
          <Text style={styles.statValue}>
            {data?.avg ?? '--'}
            <Text style={styles.statUnit}> {data?.unit || ''}</Text>
          </Text>
          <Text style={styles.statLabel}>Avg</Text>
        </Card>
      </View>

      {/* Bottom Optimal Range Card */}
      <Card variant="default" padding="medium" style={styles.optimalCard}>
        <View style={styles.optimalIconCircle}>
          <Ionicons name="leaf" size={22} color={colors.leafGreen} />
        </View>
        <View style={styles.optimalTextGroup}>
          <Text style={styles.optimalTitle}>
            Optimal Range: {data?.optimalMin ?? 20}{data?.unit || '°C'} – {data?.optimalMax ?? 30}{data?.unit || '°C'}
          </Text>
          <Text style={styles.optimalSubtitle}>
            {data?.optimalText || 'For healthy growth'}
          </Text>
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
    marginBottom: spacing.lg,
  },
  backButton: {
    padding: spacing.xs,
  },
  title: {
    fontSize: typography.fontSize.navTitle,
    fontWeight: typography.fontWeight.bold,
    color: colors.textPrimary,
  },
  actionButton: {
    padding: spacing.xs,
  },
  dropdownWrapper: {
    position: 'relative',
    zIndex: 10,
    marginBottom: spacing.md,
  },
  dropdownButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: colors.surface,
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.sm + 2,
    borderRadius: radii.pill,
    borderWidth: 1,
    borderColor: colors.border,
    alignSelf: 'flex-start',
    gap: spacing.sm,
    shadowColor: colors.shadowColor,
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 1,
  },
  dropdownText: {
    fontSize: 15,
    fontWeight: typography.fontWeight.semibold,
    color: colors.textPrimary,
  },
  dropdownMenu: {
    position: 'absolute',
    top: 44,
    left: 0,
    width: 200,
    zIndex: 20,
    borderRadius: radii.card,
  },
  dropdownItem: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: spacing.sm,
    paddingHorizontal: spacing.md,
    borderRadius: radii.sm,
  },
  dropdownItemActive: {
    backgroundColor: colors.primaryMuted,
  },
  dropdownItemText: {
    fontSize: 14,
    color: colors.textPrimary,
    fontWeight: typography.fontWeight.medium,
  },
  dropdownItemTextActive: {
    color: colors.primary,
    fontWeight: typography.fontWeight.bold,
  },
  valueRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: spacing.md,
  },
  valueGroup: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.md,
  },
  largeValue: {
    fontSize: 34,
    fontWeight: typography.fontWeight.bold,
    color: colors.textPrimary,
  },
  unitText: {
    fontSize: 22,
    fontWeight: typography.fontWeight.medium,
    color: colors.textSecondary,
  },
  valueBadge: {
    marginTop: 2,
  },
  moreOptionsButton: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: colors.surface,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: colors.border,
  },
  chartCard: {
    marginBottom: spacing.lg,
    overflow: 'hidden',
  },
  timeRangeContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    backgroundColor: colors.surface,
    borderRadius: radii.pill,
    padding: 4,
    marginBottom: spacing.lg,
    borderWidth: 1,
    borderColor: colors.border,
  },
  rangePill: {
    flex: 1,
    paddingVertical: spacing.sm,
    alignItems: 'center',
    borderRadius: radii.pill,
  },
  rangePillActive: {
    backgroundColor: colors.primary,
  },
  rangeText: {
    fontSize: 13,
    fontWeight: typography.fontWeight.medium,
    color: colors.textSecondary,
  },
  rangeTextActive: {
    color: colors.textInverse,
    fontWeight: typography.fontWeight.semibold,
  },
  statsRow: {
    flexDirection: 'row',
    gap: spacing.md,
    marginBottom: spacing.lg,
  },
  statCard: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: spacing.md,
  },
  statValue: {
    fontSize: 17,
    fontWeight: typography.fontWeight.bold,
    color: colors.textPrimary,
    marginBottom: 2,
  },
  statUnit: {
    fontSize: 12,
    fontWeight: typography.fontWeight.regular,
    color: colors.textSecondary,
  },
  statLabel: {
    fontSize: 12,
    color: colors.textMuted,
    fontWeight: typography.fontWeight.medium,
  },
  optimalCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#EBF5ED',
    borderWidth: 1,
    borderColor: '#CBE5D2',
    borderRadius: radii.card,
    paddingVertical: spacing.md,
    paddingHorizontal: spacing.lg,
    marginBottom: spacing.xxl,
  },
  optimalIconCircle: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: colors.surface,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: spacing.md,
  },
  optimalTextGroup: {
    flex: 1,
  },
  optimalTitle: {
    fontSize: 15,
    fontWeight: typography.fontWeight.semibold,
    color: colors.textPrimary,
    marginBottom: 2,
  },
  optimalSubtitle: {
    fontSize: 13,
    color: colors.textSecondary,
  },
});
