import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView, Alert, Image } from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { ScreenContainer } from '../components/ui/ScreenContainer';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { colors } from '../constants/colors';
import { typography } from '../constants/typography';
import { spacing } from '../constants/spacing';
import { radii } from '../constants/radii';
import { aiService } from '../services/aiService';
import { AIScan } from '../types';

const DAYS = [
  { day: 19, active: false },
  { day: 20, active: false },
  { day: 21, active: false },
  { day: 22, active: false },
  { day: 23, active: false },
  { day: 24, active: false },
  { day: 25, active: true },
];

const TIMELINE_EVENTS = [
  {
    id: 'h-1',
    time: '10:28 AM',
    title: 'Soil Moisture is Low',
    type: 'critical' as const,
    icon: 'warning' as const,
    iconColor: colors.status.critical.primary,
  },
  {
    id: 'h-2',
    time: '10:15 AM',
    title: 'pH Level is Slightly High',
    type: 'warning' as const,
    icon: 'warning-outline' as const,
    iconColor: colors.status.warning.primary,
  },
  {
    id: 'h-3',
    time: '09:55 AM',
    title: 'All parameters normal',
    type: 'info' as const,
    icon: 'checkmark-circle' as const,
    iconColor: colors.status.healthy.primary,
  },
  {
    id: 'h-4',
    time: '09:30 AM',
    title: 'Temperature is High',
    type: 'warning' as const,
    icon: 'warning-outline' as const,
    iconColor: colors.status.warning.primary,
  },
  {
    id: 'h-5',
    time: '09:10 AM',
    title: 'TDS Level Normal',
    type: 'info' as const,
    icon: 'water' as const,
    iconColor: colors.status.info.primary,
  },
];

export default function HistoryScreen() {
  const router = useRouter();
  const [activeTab, setActiveTab] = useState<'alerts' | 'scans'>('alerts');
  const [selectedDay, setSelectedDay] = useState(25);
  const [scans, setScans] = useState<AIScan[]>([]);

  useEffect(() => {
    aiService.getRecentScans().then(setScans);
  }, []);

  return (
    <ScreenContainer scroll={true} padding={true}>
      {/* Header */}
      <View style={styles.header}>
        <View style={styles.headerLeft}>
          <TouchableOpacity
            style={styles.backButton}
            onPress={() => router.back()}
            hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
          >
            <Ionicons name="arrow-back" size={24} color={colors.textPrimary} />
          </TouchableOpacity>
          <Text style={styles.title}>History</Text>
        </View>

        <TouchableOpacity
          style={styles.refreshButton}
          onPress={() => Alert.alert('Sync Telemetry', 'Historical records refreshed.')}
        >
          <Ionicons name="sync-outline" size={22} color={colors.textPrimary} />
        </TouchableOpacity>
      </View>

      {/* Tab Switcher (Alerts / Scans) */}
      <View style={styles.tabRow}>
        <TouchableOpacity
          style={[styles.tabButton, activeTab === 'alerts' && styles.tabButtonActive]}
          onPress={() => setActiveTab('alerts')}
          activeOpacity={0.7}
        >
          <Text style={[styles.tabButtonText, activeTab === 'alerts' && styles.tabButtonTextActive]}>
            Alerts
          </Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.tabButton, activeTab === 'scans' && styles.tabButtonActive]}
          onPress={() => setActiveTab('scans')}
          activeOpacity={0.7}
        >
          <Text style={[styles.tabButtonText, activeTab === 'scans' && styles.tabButtonTextActive]}>
            Scans
          </Text>
        </TouchableOpacity>
      </View>

      {/* Month Header */}
      <View style={styles.monthHeader}>
        <Text style={styles.monthText}>May 2025 &gt;</Text>
      </View>

      {/* Horizontal Day Selector */}
      <View style={styles.daysRow}>
        {DAYS.map((item) => {
          const isSelected = selectedDay === item.day;
          return (
            <TouchableOpacity
              key={`day-${item.day}`}
              style={[styles.dayItem, isSelected && styles.dayItemActive]}
              onPress={() => setSelectedDay(item.day)}
              activeOpacity={0.7}
            >
              <Text style={[styles.dayText, isSelected && styles.dayTextActive]}>
                {item.day}
              </Text>
            </TouchableOpacity>
          );
        })}
      </View>

      {/* Timeline Items List */}
      {activeTab === 'alerts' ? (
        <View style={styles.timelineList}>
          {TIMELINE_EVENTS.map((event) => (
            <Card key={event.id} variant="default" padding="medium" style={styles.timelineCard}>
              <View style={styles.timelineRow}>
                <Text style={styles.timeText}>{event.time}</Text>

                <View style={styles.iconWrapper}>
                  <Ionicons name={event.icon} size={18} color={event.iconColor} />
                </View>

                <Text style={styles.eventTitle} numberOfLines={1}>
                  {event.title}
                </Text>

                <Badge
                  status={event.type}
                  label={event.type.charAt(0).toUpperCase() + event.type.slice(1)}
                  variant="subtle"
                  style={styles.badgeStyle}
                />
              </View>
            </Card>
          ))}
        </View>
      ) : (
        <View style={styles.timelineList}>
          {scans.map((scan) => (
            <TouchableOpacity
              key={scan.id}
              onPress={() => router.push('/ai/result')}
              activeOpacity={0.7}
            >
              <Card variant="default" padding="medium" style={styles.timelineCard}>
                <View style={styles.scanRow}>
                  <Image source={{ uri: scan.imageUrl }} style={styles.scanThumb} />
                  <View style={styles.scanTextGroup}>
                    <Text style={styles.scanTitle}>{scan.diseaseName}</Text>
                    <Text style={styles.scanSub}>{scan.plantType} • {scan.timestamp}</Text>
                  </View>
                  <Badge
                    status={scan.isHealthy ? 'healthy' : 'warning'}
                    label={`${scan.confidence}%`}
                    variant="subtle"
                  />
                </View>
              </Card>
            </TouchableOpacity>
          ))}
        </View>
      )}

      {/* View Full History Link */}
      <TouchableOpacity
        style={styles.fullHistoryLink}
        onPress={() => Alert.alert('History Archive', 'Full 30-day historical log exported to telemetry storage.')}
      >
        <Text style={styles.fullHistoryText}>View Full History</Text>
      </TouchableOpacity>
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
  headerLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
  },
  backButton: {
    padding: spacing.xs,
  },
  title: {
    fontSize: typography.fontSize.screenTitle,
    fontWeight: typography.fontWeight.bold,
    color: colors.textPrimary,
  },
  refreshButton: {
    padding: spacing.xs,
  },
  tabRow: {
    flexDirection: 'row',
    backgroundColor: colors.surface,
    borderRadius: radii.pill,
    padding: 4,
    marginBottom: spacing.lg,
    borderWidth: 1,
    borderColor: colors.border,
  },
  tabButton: {
    flex: 1,
    paddingVertical: spacing.sm,
    alignItems: 'center',
    borderRadius: radii.pill,
  },
  tabButtonActive: {
    backgroundColor: colors.primary,
  },
  tabButtonText: {
    fontSize: 13,
    fontWeight: typography.fontWeight.medium,
    color: colors.textSecondary,
  },
  tabButtonTextActive: {
    color: colors.textInverse,
    fontWeight: typography.fontWeight.semibold,
  },
  monthHeader: {
    marginBottom: spacing.sm,
  },
  monthText: {
    fontSize: 15,
    fontWeight: typography.fontWeight.bold,
    color: colors.textPrimary,
  },
  daysRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: spacing.xl,
    paddingHorizontal: 2,
  },
  dayItem: {
    width: 36,
    height: 36,
    borderRadius: 18,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
  },
  dayItemActive: {
    backgroundColor: colors.primary,
    borderColor: colors.primary,
  },
  dayText: {
    fontSize: 13,
    fontWeight: typography.fontWeight.semibold,
    color: colors.textPrimary,
  },
  dayTextActive: {
    color: colors.textInverse,
  },
  timelineList: {
    gap: spacing.md,
    marginBottom: spacing.xl,
  },
  timelineCard: {
    borderRadius: radii.card,
  },
  timelineRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  timeText: {
    fontSize: 12,
    color: colors.textMuted,
    width: 62,
  },
  iconWrapper: {
    marginRight: spacing.sm,
  },
  eventTitle: {
    flex: 1,
    fontSize: 14,
    fontWeight: typography.fontWeight.medium,
    color: colors.textPrimary,
    marginRight: spacing.sm,
  },
  badgeStyle: {
    paddingHorizontal: spacing.sm,
    paddingVertical: 3,
  },
  scanRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  scanThumb: {
    width: 40,
    height: 40,
    borderRadius: radii.sm,
    marginRight: spacing.md,
    backgroundColor: colors.backgroundSecondary,
  },
  scanTextGroup: {
    flex: 1,
  },
  scanTitle: {
    fontSize: 14,
    fontWeight: typography.fontWeight.semibold,
    color: colors.textPrimary,
    marginBottom: 2,
  },
  scanSub: {
    fontSize: 12,
    color: colors.textSecondary,
  },
  fullHistoryLink: {
    alignItems: 'center',
    paddingVertical: spacing.md,
    marginBottom: spacing.xxl,
  },
  fullHistoryText: {
    fontSize: 14,
    fontWeight: typography.fontWeight.semibold,
    color: colors.primary,
  },
});
