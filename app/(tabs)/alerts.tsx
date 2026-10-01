import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView } from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { ScreenContainer } from '../../components/ui/ScreenContainer';
import { Card } from '../../components/ui/Card';
import { colors } from '../../constants/colors';
import { typography } from '../../constants/typography';
import { spacing } from '../../constants/spacing';
import { radii } from '../../constants/radii';
import { alertService } from '../../services/alertService';
import { AlertItem } from '../../types';

export default function AlertsScreen() {
  const router = useRouter();
  const [filter, setFilter] = useState<'all' | 'critical' | 'warning' | 'info'>('all');
  const [alerts, setAlerts] = useState<AlertItem[]>([]);

  useEffect(() => {
    loadAlerts();
  }, [filter]);

  const loadAlerts = async () => {
    const data = await alertService.getAlertsBySeverity(filter);
    setAlerts(data);
  };

  const getAlertIcon = (alert: AlertItem) => {
    if (alert.severity === 'critical') {
      return <Ionicons name="warning" size={20} color={colors.status.critical.primary} />;
    }
    if (alert.severity === 'warning') {
      return <Ionicons name="warning-outline" size={20} color={colors.status.warning.primary} />;
    }
    return <Ionicons name="checkmark-circle" size={20} color={colors.status.healthy.primary} />;
  };

  const getAlertIconBg = (alert: AlertItem) => {
    if (alert.severity === 'critical') {
      return colors.status.critical.background;
    }
    if (alert.severity === 'warning') {
      return colors.status.warning.background;
    }
    return colors.status.healthy.background;
  };

  return (
    <ScreenContainer scroll={true} padding={true}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.title}>Alerts</Text>
        <TouchableOpacity style={styles.inboxButton} onPress={() => router.push('/history')}>
          <Ionicons name="archive-outline" size={22} color={colors.textPrimary} />
        </TouchableOpacity>
      </View>

      {/* Filter Chips */}
      <View style={styles.filterRow}>
        {(['all', 'critical', 'warning', 'info'] as const).map((type) => {
          const isActive = filter === type;
          const label = type.charAt(0).toUpperCase() + type.slice(1);
          return (
            <TouchableOpacity
              key={type}
              style={[styles.filterChip, isActive && styles.filterChipActive]}
              onPress={() => setFilter(type)}
              activeOpacity={0.7}
            >
              <Text
                style={[
                  styles.filterChipText,
                  isActive && styles.filterChipTextActive,
                ]}
              >
                {label}
              </Text>
            </TouchableOpacity>
          );
        })}
      </View>

      {/* Alerts List */}
      <View style={styles.alertsList}>
        {alerts.map((item) => (
          <TouchableOpacity
            key={item.id}
            onPress={() => router.push(`/alerts/${item.id}` as any)}
            activeOpacity={0.7}
          >
            <Card variant="default" padding="medium" style={styles.alertCard}>
              <View style={styles.alertRow}>
                <View
                  style={[
                    styles.iconCircle,
                    { backgroundColor: getAlertIconBg(item) },
                  ]}
                >
                  {getAlertIcon(item)}
                </View>

                <View style={styles.alertContent}>
                  <View style={styles.titleRow}>
                    <Text style={styles.alertTitle} numberOfLines={1}>
                      {item.title}
                    </Text>
                    <Text style={styles.timestamp}>{item.timestamp}</Text>
                  </View>
                  <Text style={styles.alertDescription} numberOfLines={1}>
                    {item.description}
                  </Text>
                </View>
              </View>
            </Card>
          </TouchableOpacity>
        ))}

        {alerts.length === 0 && (
          <View style={styles.emptyContainer}>
            <Ionicons name="checkmark-done-circle-outline" size={56} color={colors.leafGreen} />
            <Text style={styles.emptyTitle}>No Alerts</Text>
            <Text style={styles.emptySubtitle}>All parameters in this category are operating within threshold.</Text>
          </View>
        )}
      </View>
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
  inboxButton: {
    padding: spacing.xs,
  },
  filterRow: {
    flexDirection: 'row',
    gap: spacing.sm,
    marginBottom: spacing.lg,
  },
  filterChip: {
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.sm,
    borderRadius: radii.pill,
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
  },
  filterChipActive: {
    backgroundColor: colors.primary,
    borderColor: colors.primary,
  },
  filterChipText: {
    fontSize: 13,
    fontWeight: typography.fontWeight.medium,
    color: colors.textSecondary,
  },
  filterChipTextActive: {
    color: colors.textInverse,
    fontWeight: typography.fontWeight.semibold,
  },
  alertsList: {
    gap: spacing.md,
    paddingBottom: spacing.xxl,
  },
  alertCard: {
    borderRadius: radii.card,
  },
  alertRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  iconCircle: {
    width: 44,
    height: 44,
    borderRadius: 22,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: spacing.md,
  },
  alertContent: {
    flex: 1,
  },
  titleRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 3,
  },
  alertTitle: {
    fontSize: 15,
    fontWeight: typography.fontWeight.semibold,
    color: colors.textPrimary,
    flex: 1,
    marginRight: spacing.sm,
  },
  timestamp: {
    fontSize: 12,
    color: colors.textMuted,
  },
  alertDescription: {
    fontSize: 13,
    color: colors.textSecondary,
  },
  emptyContainer: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: spacing.xxl * 2,
    gap: spacing.sm,
  },
  emptyTitle: {
    fontSize: 18,
    fontWeight: typography.fontWeight.bold,
    color: colors.textPrimary,
  },
  emptySubtitle: {
    fontSize: 13,
    color: colors.textSecondary,
    textAlign: 'center',
    paddingHorizontal: spacing.xl,
  },
});
