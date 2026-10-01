import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { ScreenContainer } from '../../components/ui/ScreenContainer';
import { Card } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import { colors } from '../../constants/colors';
import { typography } from '../../constants/typography';
import { spacing } from '../../constants/spacing';
import { radii } from '../../constants/radii';
import { sensorService } from '../../services/sensorService';
import { SensorDevice } from '../../types';

export default function SensorStatusScreen() {
  const router = useRouter();
  const [sensors, setSensors] = useState<SensorDevice[]>([]);

  useEffect(() => {
    sensorService.getSensorDevices().then(setSensors);
  }, []);

  const getSensorIcon = (metric: string) => {
    switch (metric) {
      case 'temperature':
        return <Ionicons name="thermometer-outline" size={20} color={colors.metrics.temperature} />;
      case 'soilMoisture':
        return <Ionicons name="water-outline" size={20} color={colors.metrics.humidity} />;
      case 'ph':
        return <Ionicons name="flask-outline" size={20} color={colors.metrics.ph} />;
      case 'tds':
        return <Ionicons name="speedometer-outline" size={20} color={colors.metrics.tds} />;
      case 'light':
        return <Ionicons name="sunny-outline" size={20} color={colors.metrics.light} />;
      case 'camera':
        return <Ionicons name="camera-outline" size={20} color={colors.primary} />;
      default:
        return <Ionicons name="hardware-chip-outline" size={20} color={colors.primary} />;
    }
  };

  const getSensorIconBg = (metric: string) => {
    switch (metric) {
      case 'temperature':
        return '#FEE2E2';
      case 'soilMoisture':
        return '#E0F2FE';
      case 'ph':
        return '#F3E8FF';
      case 'tds':
        return '#CCFBF1';
      case 'light':
        return '#FEF3C7';
      case 'camera':
        return colors.primaryMuted;
      default:
        return colors.backgroundSecondary;
    }
  };

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
          <Text style={styles.title}>Sensor Status</Text>
        </View>

        <View style={styles.headerActions}>
          <TouchableOpacity
            style={styles.actionIcon}
            onPress={() => router.push('/sensors/add')}
            hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
          >
            <Ionicons name="add-circle-outline" size={24} color={colors.primary} />
          </TouchableOpacity>
          <TouchableOpacity
            style={styles.actionIcon}
            onPress={() => router.push('/ai/camera')}
            hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
          >
            <Ionicons name="scan-outline" size={22} color={colors.textPrimary} />
          </TouchableOpacity>
        </View>
      </View>

      {/* Top Health Status Banner */}
      <View style={styles.statusBanner}>
        <Ionicons name="checkmark-circle" size={28} color={colors.leafGreen} />
        <View style={styles.bannerTextContainer}>
          <Text style={styles.bannerTitle}>All systems operational</Text>
          <Text style={styles.bannerSubtitle}>Last updated: 10:30 AM</Text>
        </View>
      </View>

      {/* Sensor List */}
      <View style={styles.sensorList}>
        {sensors.map((sensor) => (
          <Card key={sensor.id} variant="default" padding="medium" style={styles.sensorCard}>
            <View style={styles.sensorRow}>
              <View
                style={[
                  styles.sensorIconContainer,
                  { backgroundColor: getSensorIconBg(sensor.metric) },
                ]}
              >
                {getSensorIcon(sensor.metric)}
              </View>

              <View style={styles.sensorInfo}>
                <Text style={styles.sensorName}>{sensor.name}</Text>
                <Text style={styles.sensorType}>{sensor.type}</Text>
              </View>

              <Badge
                status="healthy"
                label="Active"
                variant="subtle"
                style={styles.activeBadge}
              />
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
  headerActions: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
  },
  actionIcon: {
    padding: spacing.xs,
  },
  statusBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#E8F5E9',
    borderWidth: 1,
    borderColor: '#C8E6C9',
    borderRadius: radii.card,
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.md,
    marginBottom: spacing.lg,
    gap: spacing.md,
  },
  bannerTextContainer: {
    flex: 1,
  },
  bannerTitle: {
    fontSize: 15,
    fontWeight: typography.fontWeight.bold,
    color: '#1B5E20',
  },
  bannerSubtitle: {
    fontSize: 12,
    color: '#388E3C',
    marginTop: 2,
  },
  sensorList: {
    gap: spacing.md,
    paddingBottom: spacing.xxl,
  },
  sensorCard: {
    borderRadius: radii.card,
  },
  sensorRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  sensorIconContainer: {
    width: 44,
    height: 44,
    borderRadius: 22,
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
    marginBottom: 2,
  },
  sensorType: {
    fontSize: 12,
    color: colors.textSecondary,
  },
  activeBadge: {
    paddingHorizontal: spacing.md,
  },
});
