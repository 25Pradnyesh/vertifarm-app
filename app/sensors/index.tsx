import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView } from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { ScreenContainer } from '../../components/ui/ScreenContainer';
import { Card } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import { colors } from '../../constants/colors';
import { typography } from '../../constants/typography';
import { spacing } from '../../constants/spacing';
import { sensorService } from '../../services/sensorService';
import { SensorDevice } from '../../types';

export default function SensorStatusScreen() {
  const router = useRouter();
  const [sensors, setSensors] = useState<SensorDevice[]>([]);

  useEffect(() => {
    sensorService.getSensorDevices().then(setSensors);
  }, []);

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
        <Text style={styles.title}>Sensor Status</Text>
        <TouchableOpacity onPress={() => router.push('/sensors/add')}>
          <Ionicons name="add" size={26} color={colors.primary} />
        </TouchableOpacity>
      </View>

      {/* Summary Banner */}
      <Card variant="default" padding="medium" style={styles.summaryCard}>
        <View style={styles.summaryRow}>
          <Ionicons name="checkmark-circle" size={28} color={colors.status.healthy.primary} />
          <View style={styles.summaryTextContainer}>
            <Text style={styles.summaryTitle}>All systems operational</Text>
            <Text style={styles.summarySubtitle}>Last updated: 10:30 AM</Text>
          </View>
        </View>
      </Card>

      {/* Sensor List */}
      <View style={styles.sensorList}>
        {sensors.map((sensor) => (
          <Card key={sensor.id} variant="default" padding="medium" style={styles.sensorCard}>
            <View style={styles.sensorRow}>
              <View style={styles.sensorIconContainer}>
                <Ionicons name="hardware-chip-outline" size={22} color={colors.primary} />
              </View>

              <View style={styles.sensorInfo}>
                <Text style={styles.sensorName}>{sensor.name}</Text>
                <Text style={styles.sensorType}>{sensor.type}</Text>
              </View>

              <Badge status={sensor.status === 'active' ? 'healthy' : 'warning'} label={sensor.status.toUpperCase()} />
            </View>
          </Card>
        ))}
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
  summaryCard: {
    marginBottom: spacing.xl,
    backgroundColor: colors.status.healthy.background,
    borderColor: colors.status.healthy.border,
  },
  summaryRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  summaryTextContainer: {
    marginLeft: spacing.md,
  },
  summaryTitle: {
    fontSize: 15,
    fontWeight: typography.fontWeight.semibold,
    color: colors.status.healthy.text,
  },
  summarySubtitle: {
    fontSize: 12,
    color: colors.status.healthy.text,
    opacity: 0.8,
  },
  sensorList: {
    gap: spacing.md,
    paddingBottom: spacing.xxl,
  },
  sensorCard: {},
  sensorRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  sensorIconContainer: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: colors.primaryMuted,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: spacing.md,
  },
  sensorInfo: {
    flex: 1,
  },
  sensorName: {
    fontSize: 15,
    fontWeight: typography.fontWeight.semibold,
    color: colors.textPrimary,
  },
  sensorType: {
    fontSize: 12,
    color: colors.textSecondary,
    marginTop: 2,
  },
});
