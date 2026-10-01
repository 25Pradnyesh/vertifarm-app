import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, Alert } from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { ScreenContainer } from '../../components/ui/ScreenContainer';
import { Card } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import { Button } from '../../components/ui/Button';
import { colors } from '../../constants/colors';
import { typography } from '../../constants/typography';
import { spacing } from '../../constants/spacing';
import { radii } from '../../constants/radii';
import { alertService } from '../../services/alertService';
import { AlertItem } from '../../types';

export default function AlertDetailsScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const router = useRouter();
  const [alert, setAlert] = useState<AlertItem | null>(null);
  const [isResolving, setIsResolving] = useState(false);

  useEffect(() => {
    if (id) {
      alertService.getAlertById(id).then(setAlert);
    }
  }, [id]);

  const handleResolve = async () => {
    if (!id) return;
    setIsResolving(true);
    await alertService.resolveAlert(id);
    setIsResolving(false);
    Alert.alert('Alert Resolved', 'Status has been updated to normal.', [
      { text: 'OK', onPress: () => router.back() },
    ]);
  };

  const getSeverityColor = (sev?: string) => {
    if (sev === 'critical') return colors.status.critical.primary;
    if (sev === 'warning') return colors.status.warning.primary;
    return colors.status.healthy.primary;
  };

  const getSeverityBg = (sev?: string) => {
    if (sev === 'critical') return colors.status.critical.background;
    if (sev === 'warning') return colors.status.warning.background;
    return colors.status.healthy.background;
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
        <Text style={styles.title}>Alert Details</Text>
        <View style={{ width: 24 }} />
      </View>

      {/* Hero Severity Card */}
      <Card variant="default" padding="large" style={styles.heroCard}>
        <View
          style={[
            styles.heroIconCircle,
            { backgroundColor: getSeverityBg(alert?.severity) },
          ]}
        >
          <Ionicons
            name={alert?.severity === 'info' ? 'checkmark-circle' : 'warning'}
            size={40}
            color={getSeverityColor(alert?.severity)}
          />
        </View>

        <Text style={styles.alertTitle}>{alert?.title || 'Alert'}</Text>
        <Text style={styles.alertTime}>{alert?.timestamp} • {alert?.zoneName || 'Greenhouse 1'}</Text>

        <Badge
          status={alert?.severity || 'warning'}
          label={alert?.severity ? alert.severity.toUpperCase() : 'ALERT'}
          variant="solid"
          style={styles.heroBadge}
        />
      </Card>

      {/* Telemetry Comparison: Current vs Threshold */}
      <View style={styles.comparisonRow}>
        <Card variant="default" padding="medium" style={styles.comparisonCard}>
          <Text style={styles.comparisonLabel}>Current Value</Text>
          <Text style={[styles.comparisonValue, { color: getSeverityColor(alert?.severity) }]}>
            {alert?.currentValue || '--'}
          </Text>
        </Card>

        <Card variant="default" padding="medium" style={styles.comparisonCard}>
          <Text style={styles.comparisonLabel}>Threshold Trigger</Text>
          <Text style={styles.comparisonValue}>
            {alert?.thresholdValue || '--'}
          </Text>
        </Card>
      </View>

      {/* Agronomic Recommendation */}
      <Card variant="default" padding="large" style={styles.recommendationCard}>
        <View style={styles.recHeader}>
          <Ionicons name="bulb-outline" size={22} color={colors.primary} />
          <Text style={styles.recTitle}>Recommended Action</Text>
        </View>
        <Text style={styles.recBody}>
          {alert?.recommendation || 'Check the greenhouse zone and restore environmental settings to baseline.'}
        </Text>
      </Card>

      {/* Action Buttons */}
      <View style={styles.actionsContainer}>
        {alert?.metric && (
          <Button
            title="Inspect Live Telemetry"
            onPress={() => router.push(`/live-data/${alert.metric}` as any)}
            variant="outline"
            fullWidth
            style={styles.liveButton}
          />
        )}

        <Button
          title={alert?.isResolved ? 'Resolved' : 'Mark as Resolved'}
          onPress={handleResolve}
          variant="primary"
          fullWidth
          loading={isResolving}
          disabled={alert?.isResolved}
        />
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
  backButton: {
    padding: spacing.xs,
  },
  title: {
    fontSize: typography.fontSize.navTitle,
    fontWeight: typography.fontWeight.bold,
    color: colors.textPrimary,
  },
  heroCard: {
    alignItems: 'center',
    marginBottom: spacing.lg,
    borderRadius: radii.card,
  },
  heroIconCircle: {
    width: 72,
    height: 72,
    borderRadius: 36,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: spacing.md,
  },
  alertTitle: {
    fontSize: 20,
    fontWeight: typography.fontWeight.bold,
    color: colors.textPrimary,
    textAlign: 'center',
    marginBottom: 4,
  },
  alertTime: {
    fontSize: 13,
    color: colors.textSecondary,
    marginBottom: spacing.md,
  },
  heroBadge: {
    paddingHorizontal: spacing.lg,
    paddingVertical: 4,
  },
  comparisonRow: {
    flexDirection: 'row',
    gap: spacing.md,
    marginBottom: spacing.lg,
  },
  comparisonCard: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: radii.card,
  },
  comparisonLabel: {
    fontSize: 12,
    color: colors.textMuted,
    marginBottom: 4,
  },
  comparisonValue: {
    fontSize: 22,
    fontWeight: typography.fontWeight.bold,
    color: colors.textPrimary,
  },
  recommendationCard: {
    borderRadius: radii.card,
    marginBottom: spacing.xl,
    backgroundColor: colors.surfaceSubtle,
    borderWidth: 1,
    borderColor: colors.border,
  },
  recHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
    marginBottom: spacing.sm,
  },
  recTitle: {
    fontSize: 15,
    fontWeight: typography.fontWeight.semibold,
    color: colors.primary,
  },
  recBody: {
    fontSize: 14,
    color: colors.textPrimary,
    lineHeight: 20,
  },
  actionsContainer: {
    gap: spacing.md,
    marginBottom: spacing.xxl,
  },
  liveButton: {
    marginBottom: spacing.xs,
  },
});
