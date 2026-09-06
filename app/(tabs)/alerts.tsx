import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView } from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { ScreenContainer } from '../../components/ui/ScreenContainer';
import { Card } from '../../components/ui/Card';
import { colors } from '../../constants/colors';
import { typography } from '../../constants/typography';
import { spacing } from '../../constants/spacing';
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

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'critical':
        return (
          <Ionicons
            name="alert-circle"
            size={24}
            color={colors.status.critical.primary}
          />
        );
      case 'warning':
        return (
          <Ionicons name="warning" size={24} color={colors.status.warning.primary} />
        );
      case 'info':
        return (
          <Ionicons
            name="checkmark-circle"
            size={24}
            color={colors.status.healthy.primary}
          />
        );
      default:
        return (
          <Ionicons name="information-circle" size={24} color={colors.status.info.primary} />
        );
    }
  };

  const getSeverityBgColor = (severity: string) => {
    switch (severity) {
      case 'critical':
        return colors.status.critical.background;
      case 'warning':
        return colors.status.warning.background;
      case 'info':
        return colors.status.healthy.background;
      default:
        return colors.status.info.background;
    }
  };

  return (
    <ScreenContainer scroll={false} padding={false}>
      <View style={styles.header}>
        <Text style={styles.title}>Alerts</Text>
      </View>

      {/* Filter Pills */}
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        style={styles.filterContainer}
        contentContainerStyle={styles.filterContent}
      >
        {(['all', 'critical', 'warning', 'info'] as const).map((item) => (
          <TouchableOpacity
            key={item}
            style={[
              styles.filterPill,
              filter === item && styles.filterPillActive,
            ]}
            onPress={() => setFilter(item)}
          >
            <Text
              style={[
                styles.filterText,
                filter === item && styles.filterTextActive,
              ]}
            >
              {item.charAt(0).toUpperCase() + item.slice(1)}
            </Text>
          </TouchableOpacity>
        ))}
      </ScrollView>

      {/* Alert List */}
      <ScrollView
        style={styles.alertList}
        contentContainerStyle={styles.alertListContent}
        showsVerticalScrollIndicator={false}
      >
        {alerts.map((alert) => (
          <TouchableOpacity
            key={alert.id}
            onPress={() => router.push(`/alerts/${alert.id}`)}
            activeOpacity={0.7}
          >
            <Card
              variant="default"
              padding="medium"
              style={[
                styles.alertCard,
                { backgroundColor: getSeverityBgColor(alert.severity) },
              ] as any}
            >
              <View style={styles.alertContent}>
                <View style={styles.alertIconContainer}>
                  {getSeverityIcon(alert.severity)}
                </View>

                <View style={styles.alertTextContainer}>
                  <Text style={styles.alertTitle}>{alert.title}</Text>
                  <Text style={styles.alertDescription}>
                    {alert.description}
                  </Text>
                  <Text style={styles.alertTimestamp}>{alert.timestamp}</Text>
                </View>
              </View>
            </Card>
          </TouchableOpacity>
        ))}
      </ScrollView>
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  header: {
    paddingHorizontal: spacing.screenPadding,
    marginTop: spacing.sm,
    marginBottom: spacing.lg,
  },
  title: {
    fontSize: typography.fontSize.screenTitle,
    fontWeight: typography.fontWeight.bold,
    color: colors.textPrimary,
  },
  filterContainer: {
    marginBottom: spacing.lg,
  },
  filterContent: {
    paddingHorizontal: spacing.screenPadding,
    gap: spacing.sm,
  },
  filterPill: {
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.sm,
    borderRadius: 999,
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
  },
  filterPillActive: {
    backgroundColor: colors.primary,
    borderColor: colors.primary,
  },
  filterText: {
    fontSize: 13,
    fontWeight: typography.fontWeight.medium,
    color: colors.textSecondary,
  },
  filterTextActive: {
    color: colors.textInverse,
  },
  alertList: {
    flex: 1,
  },
  alertListContent: {
    paddingHorizontal: spacing.screenPadding,
    paddingBottom: spacing.xxl,
  },
  alertCard: {
    marginBottom: spacing.md,
  },
  alertContent: {
    flexDirection: 'row',
    alignItems: 'flex-start',
  },
  alertIconContainer: {
    marginRight: spacing.md,
  },
  alertTextContainer: {
    flex: 1,
  },
  alertTitle: {
    fontSize: 15,
    fontWeight: typography.fontWeight.semibold,
    color: colors.textPrimary,
    marginBottom: spacing.xs,
  },
  alertDescription: {
    fontSize: 13,
    color: colors.textSecondary,
    marginBottom: spacing.xs,
  },
  alertTimestamp: {
    fontSize: 11,
    color: colors.textMuted,
  },
});
