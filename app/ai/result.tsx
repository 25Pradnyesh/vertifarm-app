import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, Image, ScrollView, Dimensions } from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { ScreenContainer } from '../../components/ui/ScreenContainer';
import { Card } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { colors } from '../../constants/colors';
import { typography } from '../../constants/typography';
import { spacing } from '../../constants/spacing';
import { radii } from '../../constants/radii';
import { aiService } from '../../services/aiService';
import { AIScan } from '../../types';

const { width } = Dimensions.get('window');

export default function AIScanResultScreen() {
  const router = useRouter();
  const [scan, setScan] = useState<AIScan | null>(null);

  useEffect(() => {
    aiService.getRecentScans().then((scans) => {
      if (scans.length > 0) {
        setScan(scans[0]); // Default to first scan (Leaf Spot)
      }
    });
  }, []);

  const recommendations = scan?.recommendations || [
    'Remove affected leaves',
    'Improve air circulation',
    'Apply suitable fungicide',
    'Monitor humidity levels',
    'Avoid overhead watering',
  ];

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
        <Text style={styles.title}>Scan Result</Text>
        <TouchableOpacity style={styles.headerIcon}>
          <Ionicons name="share-outline" size={22} color={colors.textPrimary} />
        </TouchableOpacity>
      </View>

      {/* Hero Leaf Photograph */}
      <View style={styles.imageCard}>
        <Image
          source={{
            uri: scan?.imageUrl || 'https://images.unsplash.com/photo-1592417817098-8f3d6910a566?w=800',
          }}
          style={styles.leafPhoto}
          resizeMode="cover"
        />
      </View>

      {/* Disease Diagnosis Card */}
      <Card variant="default" padding="large" style={styles.diagnosisCard}>
        <Text style={styles.sectionLabel}>Disease Detected</Text>
        <Text style={styles.diseaseTitle}>{scan?.diseaseName || 'Leaf Spot'}</Text>

        {/* Confidence Row */}
        <View style={styles.confidenceRow}>
          <Text style={styles.confidenceLabel}>Confidence</Text>
          <Text style={styles.confidenceValue}>{scan?.confidence || 92.6} %</Text>
        </View>

        {/* Progress Bar */}
        <View style={styles.progressBarTrack}>
          <View
            style={[
              styles.progressBarFill,
              { width: `${Math.min(100, scan?.confidence || 92.6)}%` },
            ]}
          />
        </View>

        {/* Recommendations Section */}
        <View style={styles.recommendationsSection}>
          <Text style={styles.recHeading}>Recommendation</Text>
          {recommendations.map((item, index) => (
            <View key={`rec-${index}`} style={styles.recItem}>
              <View style={styles.bulletDot} />
              <Text style={styles.recText}>{item}</Text>
            </View>
          ))}
        </View>
      </Card>

      {/* View History Button */}
      <View style={styles.buttonWrapper}>
        <Button
          title="View History"
          onPress={() => router.push('/history')}
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
    marginBottom: spacing.lg,
  },
  leafPhoto: {
    width: '100%',
    height: '100%',
  },
  diagnosisCard: {
    borderRadius: radii.huge,
    marginBottom: spacing.xl,
  },
  sectionLabel: {
    fontSize: 12,
    color: colors.textMuted,
    fontWeight: typography.fontWeight.medium,
    marginBottom: 4,
  },
  diseaseTitle: {
    fontSize: 26,
    fontWeight: typography.fontWeight.bold,
    color: colors.textPrimary,
    marginBottom: spacing.md,
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
    color: '#2E7D32',
  },
  progressBarTrack: {
    height: 8,
    backgroundColor: '#E8F5E9',
    borderRadius: 4,
    overflow: 'hidden',
    marginBottom: spacing.xl,
  },
  progressBarFill: {
    height: '100%',
    backgroundColor: colors.leafGreen,
    borderRadius: 4,
  },
  recommendationsSection: {
    marginTop: spacing.xs,
  },
  recHeading: {
    fontSize: 15,
    fontWeight: typography.fontWeight.bold,
    color: colors.textPrimary,
    marginBottom: spacing.sm,
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
    marginBottom: spacing.xxl,
  },
});
