import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, Image, ScrollView } from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { ScreenContainer } from '../../components/ui/ScreenContainer';
import { Card } from '../../components/ui/Card';
import { colors } from '../../constants/colors';
import { typography } from '../../constants/typography';
import { spacing } from '../../constants/spacing';
import { radii } from '../../constants/radii';
import { aiService } from '../../services/aiService';
import { AIScan } from '../../types';

export default function AIScanScreen() {
  const router = useRouter();
  const [scans, setScans] = useState<AIScan[]>([]);

  useEffect(() => {
    aiService.getRecentScans().then(setScans);
  }, []);

  return (
    <ScreenContainer scroll={true} padding={true}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.title}>AI Plant Health</Text>
        <TouchableOpacity
          style={styles.scanIconButton}
          onPress={() => router.push('/ai/camera')}
          hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
        >
          <Ionicons name="scan-outline" size={24} color={colors.textPrimary} />
        </TouchableOpacity>
      </View>

      {/* Top Automated Monitoring Banner Card */}
      <TouchableOpacity
        onPress={() => router.push('/ai/camera')}
        activeOpacity={0.85}
      >
        <Card variant="default" padding="medium" style={styles.monitoringCard}>
          <View style={styles.monitoringRow}>
            <View style={styles.leafIconCircle}>
              <Ionicons name="leaf" size={24} color={colors.leafGreen} />
            </View>
            <View style={styles.monitoringTextGroup}>
              <Text style={styles.monitoringTitle}>Automatic Plant Monitoring</Text>
              <Text style={styles.monitoringSubtitle}>
                Images are captured automatically and analyzed for plant health.
              </Text>
            </View>
          </View>
        </Card>
      </TouchableOpacity>

      {/* Recent Scans Section Header */}
      <View style={styles.sectionHeader}>
        <Text style={styles.sectionTitle}>Recent Scans</Text>
        <TouchableOpacity onPress={() => router.push('/history')}>
          <Text style={styles.viewAllText}>View All &gt;</Text>
        </TouchableOpacity>
      </View>

      {/* Scans List */}
      <View style={styles.scansList}>
        {scans.map((scan) => (
          <TouchableOpacity
            key={scan.id}
            onPress={() => router.push('/ai/result')}
            activeOpacity={0.7}
          >
            <Card variant="default" padding="medium" style={styles.scanCard}>
              <View style={styles.scanRow}>
                {/* Plant Thumbnail */}
                <Image
                  source={{ uri: scan.imageUrl }}
                  style={styles.scanThumbnail}
                  resizeMode="cover"
                />

                {/* Scan Info */}
                <View style={styles.scanInfo}>
                  <Text style={styles.diseaseName}>{scan.diseaseName}</Text>
                  <Text style={styles.plantType}>{scan.plantType}</Text>
                  <Text style={styles.scanTimestamp}>{scan.timestamp}</Text>
                </View>

                {/* Confidence Badge */}
                <View style={styles.confidencePill}>
                  <Text style={styles.confidenceText}>{scan.confidence}%</Text>
                </View>
              </View>
            </Card>
          </TouchableOpacity>
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
  title: {
    fontSize: typography.fontSize.screenTitle,
    fontWeight: typography.fontWeight.bold,
    color: colors.textPrimary,
  },
  scanIconButton: {
    padding: spacing.xs,
  },
  monitoringCard: {
    borderRadius: radii.card,
    marginBottom: spacing.xl,
    borderWidth: 1,
    borderColor: colors.border,
  },
  monitoringRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  leafIconCircle: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: '#E8F5E9',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: spacing.md,
  },
  monitoringTextGroup: {
    flex: 1,
  },
  monitoringTitle: {
    fontSize: 15,
    fontWeight: typography.fontWeight.bold,
    color: colors.textPrimary,
    marginBottom: 2,
  },
  monitoringSubtitle: {
    fontSize: 12,
    color: colors.textSecondary,
    lineHeight: 16,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: spacing.md,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: typography.fontWeight.bold,
    color: colors.textPrimary,
  },
  viewAllText: {
    fontSize: 13,
    color: colors.leafGreen,
    fontWeight: typography.fontWeight.semibold,
  },
  scansList: {
    gap: spacing.md,
    paddingBottom: spacing.xxl,
  },
  scanCard: {
    borderRadius: radii.card,
  },
  scanRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  scanThumbnail: {
    width: 54,
    height: 54,
    borderRadius: radii.md,
    backgroundColor: colors.backgroundSecondary,
    marginRight: spacing.md,
  },
  scanInfo: {
    flex: 1,
  },
  diseaseName: {
    fontSize: 15,
    fontWeight: typography.fontWeight.semibold,
    color: colors.textPrimary,
    marginBottom: 2,
  },
  plantType: {
    fontSize: 12,
    color: colors.textSecondary,
    marginBottom: 2,
  },
  scanTimestamp: {
    fontSize: 11,
    color: colors.textMuted,
  },
  confidencePill: {
    backgroundColor: '#E8F5E9',
    paddingHorizontal: spacing.md,
    paddingVertical: 5,
    borderRadius: radii.pill,
  },
  confidenceText: {
    fontSize: 13,
    fontWeight: typography.fontWeight.bold,
    color: '#2E7D32',
  },
});
