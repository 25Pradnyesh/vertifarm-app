import React, { useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView, Dimensions } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { ScreenContainer } from '../../components/ui/ScreenContainer';
import { Card } from '../../components/ui/Card';
import { MultiMetricChart, MetricSeries } from '../../components/charts/MultiMetricChart';
import { colors } from '../../constants/colors';
import { typography } from '../../constants/typography';
import { spacing } from '../../constants/spacing';
import { radii } from '../../constants/radii';

const { width } = Dimensions.get('window');

const METRIC_TABS = [
  { id: 'temperature', label: 'Temperature', color: colors.metrics.temperature },
  { id: 'humidity', label: 'Humidity', color: colors.metrics.humidity },
  { id: 'soil', label: 'Soil', color: colors.metrics.soilMoisture },
  { id: 'ph', label: 'pH', color: colors.metrics.ph },
  { id: 'tds', label: 'TDS', color: colors.metrics.tds },
];

const TIME_OPTIONS = ['Last 24 Hours', 'Last 7 Days', 'Last 30 Days'];

export default function AnalyticsScreen() {
  const [selectedMetric, setSelectedMetric] = useState('temperature');
  const [timeFilter, setTimeFilter] = useState('Last 24 Hours');
  const [showTimeDropdown, setShowTimeDropdown] = useState(false);

  // Scaled 0-100 realistic telemetry curves matching reference visual
  const seriesData: MetricSeries[] = [
    {
      id: 'temperature',
      name: 'Temperature',
      color: colors.metrics.temperature,
      data: [65, 78, 82, 70, 75, 88, 86],
      visible: true,
    },
    {
      id: 'humidity',
      name: 'Humidity',
      color: colors.metrics.humidity,
      data: [50, 56, 68, 62, 58, 64, 60],
      visible: true,
    },
    {
      id: 'soil',
      name: 'Soil Moisture',
      color: colors.metrics.soilMoisture,
      data: [42, 45, 48, 52, 46, 44, 48],
      visible: true,
    },
    {
      id: 'ph',
      name: 'pH',
      color: colors.metrics.ph,
      data: [35, 32, 40, 36, 25, 28, 30],
      visible: true,
    },
    {
      id: 'tds',
      name: 'TDS',
      color: colors.metrics.tds,
      data: [72, 70, 65, 58, 62, 60, 63],
      visible: true,
    },
  ];

  return (
    <ScreenContainer scroll={true} padding={true}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.title}>Analytics</Text>
        <TouchableOpacity style={styles.filterButton}>
          <Ionicons name="options-outline" size={24} color={colors.textPrimary} />
        </TouchableOpacity>
      </View>

      {/* Horizontal Metric Selector Pills */}
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={styles.metricsPillsContainer}
      >
        {METRIC_TABS.map((item) => {
          const isActive = selectedMetric === item.id;
          return (
            <TouchableOpacity
              key={item.id}
              style={[styles.metricPill, isActive && styles.metricPillActive]}
              onPress={() => setSelectedMetric(item.id)}
              activeOpacity={0.7}
            >
              <Text
                style={[
                  styles.metricPillText,
                  isActive && styles.metricPillTextActive,
                ]}
              >
                {item.label}
              </Text>
            </TouchableOpacity>
          );
        })}
      </ScrollView>

      {/* Time Range Selector Dropdown */}
      <View style={styles.dropdownContainer}>
        <TouchableOpacity
          style={styles.timeDropdownButton}
          onPress={() => setShowTimeDropdown(!showTimeDropdown)}
          activeOpacity={0.7}
        >
          <Text style={styles.timeDropdownText}>{timeFilter}</Text>
          <Ionicons
            name={showTimeDropdown ? 'chevron-up' : 'chevron-down'}
            size={16}
            color={colors.textSecondary}
          />
        </TouchableOpacity>

        {showTimeDropdown && (
          <Card variant="elevated" padding="small" style={styles.timeDropdownMenu}>
            {TIME_OPTIONS.map((opt) => (
              <TouchableOpacity
                key={opt}
                style={[
                  styles.timeDropdownItem,
                  timeFilter === opt && styles.timeDropdownItemActive,
                ]}
                onPress={() => {
                  setTimeFilter(opt);
                  setShowTimeDropdown(false);
                }}
              >
                <Text
                  style={[
                    styles.timeDropdownItemText,
                    timeFilter === opt && styles.timeDropdownItemTextActive,
                  ]}
                >
                  {opt}
                </Text>
                {timeFilter === opt && (
                  <Ionicons name="checkmark" size={16} color={colors.primary} />
                )}
              </TouchableOpacity>
            ))}
          </Card>
        )}
      </View>

      {/* Multi-Line Trend Chart Card */}
      <Card variant="default" padding="medium" style={styles.chartCard}>
        <MultiMetricChart
          series={seriesData}
          timestamps={['00:00', '06:00', '12:00', '18:00', '24:00']}
          height={230}
          width={width - spacing.screenPadding * 2 - spacing.md * 2}
        />
      </Card>

      {/* Bottom Insight Card */}
      <Card variant="default" padding="medium" style={styles.insightCard}>
        <View style={styles.insightIconCircle}>
          <Ionicons name="sunny" size={24} color={colors.leafGreen} />
        </View>
        <View style={styles.insightTextGroup}>
          <Text style={styles.insightTitle}>Insight</Text>
          <Text style={styles.insightDescription}>
            Temperature and humidity have been stable today.
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
  title: {
    fontSize: typography.fontSize.screenTitle,
    fontWeight: typography.fontWeight.bold,
    color: colors.textPrimary,
  },
  filterButton: {
    padding: spacing.xs,
  },
  metricsPillsContainer: {
    flexDirection: 'row',
    gap: spacing.sm,
    paddingBottom: spacing.sm,
    marginBottom: spacing.sm,
  },
  metricPill: {
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.sm,
    borderRadius: radii.pill,
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
  },
  metricPillActive: {
    backgroundColor: colors.primary,
    borderColor: colors.primary,
  },
  metricPillText: {
    fontSize: 13,
    fontWeight: typography.fontWeight.medium,
    color: colors.textSecondary,
  },
  metricPillTextActive: {
    color: colors.textInverse,
    fontWeight: typography.fontWeight.semibold,
  },
  dropdownContainer: {
    position: 'relative',
    zIndex: 10,
    marginBottom: spacing.md,
  },
  timeDropdownButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: colors.surface,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.xs + 2,
    borderRadius: radii.pill,
    borderWidth: 1,
    borderColor: colors.border,
    alignSelf: 'flex-start',
    gap: spacing.xs,
  },
  timeDropdownText: {
    fontSize: 13,
    color: colors.textSecondary,
    fontWeight: typography.fontWeight.medium,
  },
  timeDropdownMenu: {
    position: 'absolute',
    top: 36,
    left: 0,
    width: 170,
    zIndex: 20,
    borderRadius: radii.card,
  },
  timeDropdownItem: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: spacing.sm,
    paddingHorizontal: spacing.md,
    borderRadius: radii.sm,
  },
  timeDropdownItemActive: {
    backgroundColor: colors.primaryMuted,
  },
  timeDropdownItemText: {
    fontSize: 13,
    color: colors.textPrimary,
  },
  timeDropdownItemTextActive: {
    fontWeight: typography.fontWeight.bold,
    color: colors.primary,
  },
  chartCard: {
    marginBottom: spacing.lg,
    alignItems: 'center',
    paddingVertical: spacing.lg,
  },
  insightCard: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: spacing.xxl,
    borderRadius: radii.card,
    paddingVertical: spacing.md,
    paddingHorizontal: spacing.lg,
  },
  insightIconCircle: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: colors.leafGreenLight,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: spacing.md,
  },
  insightTextGroup: {
    flex: 1,
  },
  insightTitle: {
    fontSize: 16,
    fontWeight: typography.fontWeight.bold,
    color: colors.textPrimary,
    marginBottom: 2,
  },
  insightDescription: {
    fontSize: 13,
    color: colors.textSecondary,
    lineHeight: 18,
  },
});
