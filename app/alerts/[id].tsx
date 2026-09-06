import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { ScreenContainer } from '../../components/ui/ScreenContainer';
import { Card } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import { Button } from '../../components/ui/Button';
import { colors } from '../../constants/colors';
import { typography } from '../../constants/typography';
import { spacing } from '../../constants/spacing';
import { alertService } from '../../services/alertService';
import { AlertItem } from '../../types';

export default function AlertDetailsScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const router = useRouter();
  const [alert, setAlert] = useState<AlertItem | null>(null);

  useEffect(() => {
    if (id) {
      alertService.getAlertById(id).then(setAlert);
    }
  }, [id]);

  const handleResolve = async () => {
    if (id) {
      await alertService.resolveAlert(id);
      router.back();
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
        <Text style={styles.title}>Alert Details</Text>
        <View style={{ width: 24 }} />
      </View>

      {/* Severity Icon & Title */}
      <View style={styles.severitySection}>
        <View style={styles.severityIconCircle}>
          <Ionicons
            name="alert-circle"
            size={48}
            color={colors.status.critical.primary}
          />
        </View>
        <Text style={styles.alertTitle}>{alert?.title || 'Alert'}</Text>
        <Badge
          status={alert?.severity || 'critical'}
          label={alert?.severity ? alert.severity.toUpperCase() : 'ALERT'}
          variant="solid"
          size="medium"
        />
      </View>

      {/* Details Grid */}
      <View style={styles.detailsGrid}>
        <Card variant="subtle" padding="medium" style={styles.detailCard}>
          <Text style={styles.detailLabel}>Current Value</Text>
          <Text style={styles.detailValue}>{alert?.currentValue || '--'}</Text>
        </Card>
        <Card variant="subtle" padding="medium" style={styles.detailCard}>
          <Text style={styles.detailLabel}>Threshold</Text>
          <Text style={styles.detailValue}>{alert?.thresholdValue || '--'}</Text>
        </Card>
      </View>

      {/* Metadata Card */}
      <Card variant="default" padding="medium" style={styles.metaCard}>
        <View style={styles.metaRow}>
          <Text style={styles.metaLabel}>Time Detected</Text>
          <Text style={styles.metaValue}>{alert?.timestamp || '--'}</Text>
        </View>
        <View style={styles.metaRow}>
          <Text style={styles.metaLabel}>Location</Text>
          <Text style={styles.metaValue}>{alert?.zoneName || '--'}</Text>
        </View>
      </Card>

      {/* What's Happening */}
      <View style={styles.section}>
        <Text style={styles.sectionHeader}>WHAT'S HAPPENING?</Text>
        <Card variant="default" padding="medium">
          <Text style={styles.sectionBody}>
            The system detected a deviation from the configured optimal parameters. Immediate action is suggested to maintain healthy growth conditions.
          </Text>
        </Card>
      </View>

      {/* Recommended Action */}
      <View style={styles.section}>
        <Text style={styles.sectionHeader}>RECOMMENDED ACTION</Text>
        <Card variant="default" padding="medium">
          <Text style={styles.sectionBody}>
            {alert?.recommendation || 'No recommendation available.'}
          </Text>
        </Card>
      </View>

      {/* Primary Action Button */}
      <View style={styles.buttonWrapper}>
        <Button
          title="Mark as Resolved"
          onPress={handleResolve}
          variant="primary"
          fullWidth
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
    marginBottom: spacing.xl,
  },
  backButton: {},
  title: {
    fontSize: typography.fontSize.navTitle,
    fontWeight: typography.fontWeight.bold,
    color: colors.textPrimary,
  },
  severitySection: {
    alignItems: 'center',
    marginBottom: spacing.xl,
  },
  severityIconCircle: {
    marginBottom: spacing.md,
  },
  alertTitle: {
    fontSize: 22,
    fontWeight: typography.fontWeight.bold,
    color: colors.textPrimary,
    textAlign: 'center',
    marginBottom: spacing.sm,
  },
  detailsGrid: {
    flexDirection: 'row',
    gap: spacing.md,
    marginBottom: spacing.lg,
  },
  detailCard: {
    flex: 1,
    alignItems: 'center',
  },
  detailLabel: {
    fontSize: 12,
    color: colors.textSecondary,
    marginBottom: 4,
  },
  detailValue: {
    fontSize: 20,
    fontWeight: typography.fontWeight.bold,
    color: colors.textPrimary,
  },
  metaCard: {
    marginBottom: spacing.lg,
    gap: spacing.sm,
  },
  metaRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  metaLabel: {
    fontSize: 13,
    color: colors.textSecondary,
  },
  metaValue: {
    fontSize: 13,
    fontWeight: typography.fontWeight.semibold,
    color: colors.textPrimary,
  },
  section: {
    marginBottom: spacing.lg,
  },
  sectionHeader: {
    fontSize: 12,
    fontWeight: typography.fontWeight.bold,
    color: colors.textSecondary,
    marginBottom: spacing.sm,
    letterSpacing: 0.5,
  },
  sectionBody: {
    fontSize: 14,
    color: colors.textPrimary,
    lineHeight: 20,
  },
  buttonWrapper: {
    marginTop: spacing.lg,
    marginBottom: spacing.xxl,
  },
});
