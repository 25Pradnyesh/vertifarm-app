import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Image,
  ScrollView,
  Share,
  Alert,
} from 'react-native';
import { useRouter, useLocalSearchParams } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { ScreenContainer } from '../../components/ui/ScreenContainer';
import { Card } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import { Button } from '../../components/ui/Button';
import { colors } from '../../constants/colors';
import { typography } from '../../constants/typography';
import { spacing } from '../../constants/spacing';
import { radii } from '../../constants/radii';
import { aiService } from '../../services/aiService';
import { ScanDiagnosisResponse, AIScan } from '../../types';

export default function AIScanResultScreen() {
  const router = useRouter();
  const params = useLocalSearchParams<{ diagnosis?: string; id?: string }>();
  const [scan, setScan] = useState<ScanDiagnosisResponse | AIScan | null>(null);

  useEffect(() => {
    if (params.diagnosis) {
      try {
        const parsed = JSON.parse(params.diagnosis) as ScanDiagnosisResponse;
        setScan(parsed);
        return;
      } catch (err) {
        console.warn('Failed to parse diagnosis from params:', err);
      }
    }

    if (params.id) {
      aiService.getScanById(params.id).then((found) => {
        if (found) setScan(found);
      });
      return;
    }

    aiService.getRecentScans().then((scans) => {
      if (scans.length > 0) {
        setScan(scans[0]);
      }
    });
  }, [params.diagnosis, params.id]);

  const diagnosisResponse = scan as ScanDiagnosisResponse | null;
  const isHealthy = scan?.isHealthy ?? true;
  const confidence = scan?.confidence ?? 94.2;
  const isUncertain = diagnosisResponse?.isUncertain ?? confidence < 60;
  const topPredictions = diagnosisResponse?.topPredictions || [];

  const recommendations = scan?.recommendations && scan.recommendations.length > 0
    ? scan.recommendations
    : isHealthy
    ? [
        'Foliage demonstrates strong chlorophyll density and healthy leaf morphology.',
        'Maintain current EC, pH, and photoperiod targets.',
        'Ensure continuous air circulation to prevent microclimate moisture pockets.',
      ]
    : [
        'Isolate symptomatic plants or affected trays immediately.',
        'Prune severely spotted or necrotic foliage with sterilized tools.',
        'Adjust greenhouse canopy humidity below 65% RH to suppress sporulation.',
        'Apply targeted organic or copper-based treatment as indicated.',
      ];

  const handleShare = async () => {
    try {
      await Share.share({
        message: `VertiFarm AI Diagnosis: ${scan?.plantType || 'Plant'} - ${
          scan?.diseaseName || 'Healthy'
        } (${confidence.toFixed(1)}% confidence).`,
      });
    } catch (err) {
      console.warn('Share dismissed or failed', err);
    }
  };

  const getStatusColor = () => {
    if (isUncertain) return colors.status.warning.primary;
    if (isHealthy) return colors.status.healthy.primary;
    return colors.status.critical.primary;
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
        <Text style={styles.title}>AI Diagnosis</Text>
        <TouchableOpacity
          style={styles.headerIcon}
          onPress={handleShare}
          hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
        >
          <Ionicons name="share-outline" size={22} color={colors.textPrimary} />
        </TouchableOpacity>
      </View>

      {/* Hero Leaf Photograph */}
      <View style={styles.imageCard}>
        <Image
          source={{
            uri:
              scan?.imageUrl ||
              'https://images.unsplash.com/photo-1592417817098-8f3d6910a566?w=800',
          }}
          style={styles.leafPhoto}
          resizeMode="cover"
        />
        <View style={styles.cropBadgeOverlay}>
          <Text style={styles.cropBadgeText}>{scan?.plantType || 'Crop'}</Text>
        </View>
      </View>

      {/* Uncertainty Warning Banner */}
      {isUncertain && (
        <View style={styles.uncertaintyCard}>
          <View style={styles.uncertaintyIconWrapper}>
            <Ionicons name="warning-outline" size={22} color={colors.status.warning.primary} />
          </View>
          <View style={styles.uncertaintyContent}>
            <Text style={styles.uncertaintyTitle}>Low Confidence / Ambiguous</Text>
            <Text style={styles.uncertaintyDescription}>
              {diagnosisResponse?.uncertaintyMessage ||
                'Confidence is below the 0.60 diagnostic threshold. Symptoms may be early-stage or image lighting was non-optimal. Physical inspection recommended.'}
            </Text>
          </View>
        </View>
      )}

      {/* Disease Diagnosis Overview Card */}
      <Card variant="default" padding="large" style={styles.diagnosisCard}>
        <View style={styles.diagnosisHeaderRow}>
          <View>
            <Text style={styles.sectionLabel}>Identified Condition</Text>
            <Text style={styles.diseaseTitle}>{scan?.diseaseName || 'Healthy'}</Text>
          </View>
          <Badge
            status={isHealthy ? 'healthy' : isUncertain ? 'warning' : 'critical'}
            label={isHealthy ? 'Healthy' : isUncertain ? 'Uncertain' : 'Disease Detected'}
            size="medium"
          />
        </View>

        {/* Confidence Row */}
        <View style={styles.confidenceRow}>
          <Text style={styles.confidenceLabel}>Confidence Score</Text>
          <Text style={[styles.confidenceValue, { color: getStatusColor() }]}>
            {confidence.toFixed(1)}%
          </Text>
        </View>

        {/* Progress Bar */}
        <View style={styles.progressBarTrack}>
          <View
            style={[
              styles.progressBarFill,
              {
                width: `${Math.min(100, Math.max(5, confidence))}%`,
                backgroundColor: getStatusColor(),
              },
            ]}
          />
        </View>
      </Card>

      {/* Top Multi-Class Predictions (if available) */}
      {topPredictions.length > 0 && (
        <Card variant="default" padding="large" style={styles.predictionsCard}>
          <Text style={styles.recHeading}>Multi-Class Probabilities</Text>
          <Text style={styles.predictionsSubtitle}>
            MobileNetV3 Softmax distribution across all 6 classes
          </Text>

          <View style={styles.predictionsList}>
            {topPredictions.map((pred, idx) => (
              <View key={`pred-${idx}`} style={styles.predictionRow}>
                <View style={styles.predictionLabelGroup}>
                  <Text style={styles.predictionCropText}>
                    {pred.crop} —{' '}
                    <Text style={pred.is_healthy ? styles.healthyText : styles.diseaseText}>
                      {pred.disease}
                    </Text>
                  </Text>
                  <Text style={styles.predictionPercent}>
                    {pred.confidence.toFixed(1)}%
                  </Text>
                </View>
                <View style={styles.miniBarTrack}>
                  <View
                    style={[
                      styles.miniBarFill,
                      {
                        width: `${Math.min(100, Math.max(2, pred.confidence))}%`,
                        backgroundColor: pred.is_healthy
                          ? colors.status.healthy.primary
                          : idx === 0
                          ? colors.status.critical.primary
                          : colors.textMuted,
                      },
                    ]}
                  />
                </View>
              </View>
            ))}
          </View>
        </Card>
      )}

      {/* Agronomic Recommendations Section */}
      <Card variant="default" padding="large" style={styles.recommendationsCard}>
        <View style={styles.recHeaderRow}>
          <Ionicons name="shield-checkmark-outline" size={20} color={colors.primary} />
          <Text style={styles.recHeading}>Agronomic Recommendations</Text>
        </View>

        {recommendations.map((item, index) => (
          <View key={`rec-${index}`} style={styles.recItem}>
            <View style={styles.bulletDot} />
            <Text style={styles.recText}>{item}</Text>
          </View>
        ))}
      </Card>

      {/* Bottom Action Buttons */}
      <View style={styles.buttonWrapper}>
        <Button
          title="Scan Another Plant"
          onPress={() => router.push('/ai/camera')}
          variant="primary"
          fullWidth
          style={styles.actionBtn}
        />
        <Button
          title="View Historical Scans"
          onPress={() => router.push('/history')}
          variant="secondary"
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
  headerIcon: {
    padding: spacing.xs,
  },
  imageCard: {
    width: '100%',
    height: 220,
    borderRadius: radii.huge,
    overflow: 'hidden',
    backgroundColor: '#1E3A2B',
    marginBottom: spacing.md,
    position: 'relative',
  },
  leafPhoto: {
    width: '100%',
    height: '100%',
  },
  cropBadgeOverlay: {
    position: 'absolute',
    top: spacing.md,
    left: spacing.md,
    backgroundColor: 'rgba(27, 59, 43, 0.85)',
    paddingHorizontal: spacing.md,
    paddingVertical: 4,
    borderRadius: radii.pill,
  },
  cropBadgeText: {
    color: '#FFFFFF',
    fontSize: 12,
    fontWeight: typography.fontWeight.bold,
  },
  uncertaintyCard: {
    flexDirection: 'row',
    backgroundColor: colors.status.warning.background,
    borderColor: colors.status.warning.border,
    borderWidth: 1,
    borderRadius: radii.lg,
    padding: spacing.md,
    marginBottom: spacing.md,
    alignItems: 'flex-start',
    gap: spacing.sm,
  },
  uncertaintyIconWrapper: {
    marginTop: 2,
  },
  uncertaintyContent: {
    flex: 1,
  },
  uncertaintyTitle: {
    fontSize: 14,
    fontWeight: typography.fontWeight.bold,
    color: colors.status.warning.text,
    marginBottom: 2,
  },
  uncertaintyDescription: {
    fontSize: 12,
    color: colors.status.warning.text,
    lineHeight: 17,
  },
  diagnosisCard: {
    borderRadius: radii.huge,
    marginBottom: spacing.md,
  },
  diagnosisHeaderRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: spacing.md,
  },
  sectionLabel: {
    fontSize: 12,
    color: colors.textMuted,
    fontWeight: typography.fontWeight.medium,
    marginBottom: 4,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  diseaseTitle: {
    fontSize: 24,
    fontWeight: typography.fontWeight.bold,
    color: colors.textPrimary,
  },
  confidenceRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'baseline',
    marginBottom: spacing.xs,
  },
  confidenceLabel: {
    fontSize: 13,
    color: colors.textSecondary,
    fontWeight: typography.fontWeight.medium,
  },
  confidenceValue: {
    fontSize: 22,
    fontWeight: typography.fontWeight.bold,
  },
  progressBarTrack: {
    height: 8,
    backgroundColor: '#E8F5E9',
    borderRadius: 4,
    overflow: 'hidden',
  },
  progressBarFill: {
    height: '100%',
    borderRadius: 4,
  },
  predictionsCard: {
    borderRadius: radii.huge,
    marginBottom: spacing.md,
  },
  predictionsSubtitle: {
    fontSize: 12,
    color: colors.textMuted,
    marginBottom: spacing.md,
    marginTop: -4,
  },
  predictionsList: {
    gap: spacing.sm,
  },
  predictionRow: {
    gap: 4,
  },
  predictionLabelGroup: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  predictionCropText: {
    fontSize: 13,
    fontWeight: typography.fontWeight.medium,
    color: colors.textPrimary,
  },
  healthyText: {
    color: colors.status.healthy.primary,
    fontWeight: typography.fontWeight.bold,
  },
  diseaseText: {
    color: colors.textPrimary,
    fontWeight: typography.fontWeight.semibold,
  },
  predictionPercent: {
    fontSize: 12,
    fontWeight: typography.fontWeight.bold,
    color: colors.textSecondary,
  },
  miniBarTrack: {
    height: 5,
    backgroundColor: colors.backgroundSecondary,
    borderRadius: 3,
    overflow: 'hidden',
  },
  miniBarFill: {
    height: '100%',
    borderRadius: 3,
  },
  recommendationsCard: {
    borderRadius: radii.huge,
    marginBottom: spacing.xl,
  },
  recHeaderRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.xs,
    marginBottom: spacing.sm,
  },
  recHeading: {
    fontSize: 15,
    fontWeight: typography.fontWeight.bold,
    color: colors.textPrimary,
  },
  recItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: spacing.sm,
  },
  bulletDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: colors.leafGreen,
    marginTop: 6,
    marginRight: spacing.sm,
  },
  recText: {
    fontSize: 14,
    color: colors.textSecondary,
    lineHeight: 20,
    flex: 1,
  },
  buttonWrapper: {
    gap: spacing.sm,
    marginBottom: spacing.xxl,
  },
  actionBtn: {
    marginBottom: spacing.xs,
  },
});
