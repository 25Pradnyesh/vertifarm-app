import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Image,
  Dimensions,
} from 'react-native';
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
import { TelemetrySummary, MetricType } from '../../types';

const { width } = Dimensions.get('window');
const cardWidth = (width - spacing.screenPadding * 2 - spacing.cardGap) / 2;

export default function DashboardScreen() {
  const router = useRouter();
  const [telemetry, setTelemetry] = useState<TelemetrySummary[]>([]);
  const [healthStatus, setHealthStatus] = useState({
    status: 'healthy' as 'healthy' | 'warning' | 'critical',
    message: 'All systems are running smoothly.',
  });

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    const data = await sensorService.getTelemetrySummaries();
    const status = await sensorService.getFarmHealthStatus();
    setTelemetry(data);
    setHealthStatus(status);
  };

  const getMetricIcon = (metric: MetricType) => {
    switch (metric) {
      case 'temperature':
        return <Ionicons name="thermometer-outline" size={24} color={colors.metrics.temperature} />;
      case 'humidity':
        return <Ionicons name="water-outline" size={24} color={colors.metrics.humidity} />;
      case 'soilMoisture':
        return <Ionicons name="leaf-outline" size={24} color={colors.metrics.soilMoisture} />;
      case 'ph':
        return <Ionicons name="flask-outline" size={24} color={colors.metrics.ph} />;
      case 'tds':
        return <Ionicons name="shield-checkmark-outline" size={24} color={colors.metrics.tds} />;
      case 'light':
        return <Ionicons name="sunny-outline" size={24} color={colors.metrics.light} />;
      default:
        return <Ionicons name="hardware-chip-outline" size={24} color={colors.primary} />;
    }
  };

  return (
    <ScreenContainer scroll={true} padding={true}>
      {/* Header */}
      <View style={styles.header}>
        <View>
          <Text style={styles.greeting}>Good Morning,</Text>
          <TouchableOpacity
            style={styles.farmSelector}
            onPress={() => router.push('/farms')}
            activeOpacity={0.7}
          >
            <Text style={styles.farmName}>Greenhouse 1</Text>
            <Ionicons name="chevron-down" size={18} color={colors.textPrimary} />
          </TouchableOpacity>
          <Text style={styles.systemStatus}>{healthStatus.message}</Text>
        </View>

        <View style={styles.headerActions}>
          <TouchableOpacity
            style={styles.iconButton}
            onPress={() => router.push('/(tabs)/alerts')}
          >
            <Ionicons name="notifications-outline" size={22} color={colors.textPrimary} />
            <View style={styles.notificationDot} />
          </TouchableOpacity>
          <TouchableOpacity
            style={styles.avatarButton}
            onPress={() => router.push('/settings')}
          >
            <Image
              source={{
                uri: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=100',
              }}
              style={styles.avatar}
            />
          </TouchableOpacity>
        </View>
      </View>

      {/* Hero Banner Card */}
      <Card variant="hero" padding="none" style={styles.heroCard}>
        <View style={styles.heroContent}>
          <View style={styles.heroTextContainer}>
            <Text style={styles.heroTitle}>Healthy</Text>
            <Text style={styles.heroTitle}>Plants</Text>
            <Text style={styles.heroTitle}>Brighter</Text>
            <Text style={styles.heroTitle}>Future</Text>
          </View>
          <Image
            source={{
              uri: 'https://images.unsplash.com/photo-1530836369250-ef72a3f5cda8?w=400',
            }}
            style={styles.heroImage}
            resizeMode="cover"
          />
          <TouchableOpacity
            style={styles.heroArrowButton}
            onPress={() => router.push('/(tabs)/ai-scan')}
          >
            <Ionicons name="arrow-forward" size={18} color={colors.primary} />
          </TouchableOpacity>
        </View>
      </Card>

      {/* Sensor Grid (2 Columns) */}
      <View style={styles.sensorGrid}>
        {telemetry.map((item) => (
          <TouchableOpacity
            key={item.metric}
            style={styles.sensorCardWrapper}
            onPress={() => router.push(`/live-data/${item.metric}`)}
            activeOpacity={0.7}
          >
            <Card variant="default" padding="medium" style={styles.sensorCard}>
              <View style={styles.sensorCardTop}>
                {getMetricIcon(item.metric)}
                <Badge status={item.status} label={item.statusLabel} size="small" />
              </View>

              <View style={styles.sensorValueContainer}>
                <Text style={styles.sensorValue}>
                  {item.currentValue}
                  <Text style={styles.sensorUnit}> {item.unit}</Text>
                </Text>
                <Text style={styles.sensorName}>{item.name}</Text>
              </View>
            </Card>
          </TouchableOpacity>
        ))}
      </View>

      {/* Bottom Status Card */}
      <Card variant="default" padding="medium" style={styles.summaryCard}>
        <View style={styles.summaryRow}>
          <View style={styles.summaryIconCircle}>
            <Ionicons name="leaf" size={24} color={colors.leafGreen} />
          </View>
          <View style={styles.summaryTextContainer}>
            <Text style={styles.summaryTitle}>All Parameters</Text>
            <Text style={styles.summarySubtitle}>Normal condition</Text>
          </View>
          <Ionicons name="chevron-forward" size={20} color={colors.textSecondary} />
        </View>
      </Card>
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginTop: spacing.sm,
    marginBottom: spacing.lg,
  },
  greeting: {
    fontSize: 14,
    color: colors.textSecondary,
  },
  farmSelector: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.xs,
    marginTop: 2,
  },
  farmName: {
    fontSize: typography.fontSize.screenTitle,
    fontWeight: typography.fontWeight.bold,
    color: colors.textPrimary,
  },
  systemStatus: {
    fontSize: 12,
    color: colors.textSecondary,
    marginTop: 2,
  },
  headerActions: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.md,
  },
  iconButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: colors.surface,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: colors.borderLight,
  },
  notificationDot: {
    position: 'absolute',
    top: 10,
    right: 10,
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: colors.status.critical.primary,
  },
  avatarButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    overflow: 'hidden',
  },
  avatar: {
    width: '100%',
    height: '100%',
  },
  heroCard: {
    height: 140,
    marginBottom: spacing.xl,
    overflow: 'hidden',
  },
  heroContent: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: spacing.lg,
  },
  heroTextContainer: {
    justifyContent: 'center',
  },
  heroTitle: {
    fontSize: 18,
    fontWeight: typography.fontWeight.bold,
    color: colors.textInverse,
    lineHeight: 22,
  },
  heroImage: {
    position: 'absolute',
    right: 0,
    top: 0,
    bottom: 0,
    width: '50%',
    opacity: 0.85,
  },
  heroArrowButton: {
    position: 'absolute',
    right: spacing.lg,
    bottom: spacing.lg,
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: colors.surface,
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 10,
  },
  sensorGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: spacing.cardGap,
    marginBottom: spacing.lg,
  },
  sensorCardWrapper: {
    width: cardWidth,
  },
  sensorCard: {
    height: 120,
    justifyContent: 'space-between',
  },
  sensorCardTop: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  sensorValueContainer: {
    marginTop: spacing.xs,
  },
  sensorValue: {
    fontSize: 22,
    fontWeight: typography.fontWeight.bold,
    color: colors.textPrimary,
  },
  sensorUnit: {
    fontSize: 14,
    fontWeight: typography.fontWeight.regular,
    color: colors.textSecondary,
  },
  sensorName: {
    fontSize: 13,
    color: colors.textSecondary,
    marginTop: 2,
  },
  summaryCard: {
    marginBottom: spacing.xxl,
  },
  summaryRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  summaryIconCircle: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: colors.primaryMuted,
    alignItems: 'center',
    justifyContent: 'center',
  },
  summaryTextContainer: {
    flex: 1,
    marginLeft: spacing.md,
  },
  summaryTitle: {
    fontSize: 15,
    fontWeight: typography.fontWeight.semibold,
    color: colors.textPrimary,
  },
  summarySubtitle: {
    fontSize: 12,
    color: colors.textSecondary,
  },
});
