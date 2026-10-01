import React, { useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, Image, Dimensions, ActivityIndicator } from 'react-native';
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

const { width } = Dimensions.get('window');

const PREVIOUS_CAPTURES = [
  'https://images.unsplash.com/photo-1540420773420-3366772f4999?w=150',
  'https://images.unsplash.com/photo-1530836369250-ef72a3f5cda8?w=150',
  'https://images.unsplash.com/photo-1550989460-0adf9ea622e2?w=150',
  'https://images.unsplash.com/photo-1592417817098-8f3d6910a566?w=150',
  'https://images.unsplash.com/photo-1518531933037-91b2f5f229cc?w=150',
];

export default function CameraFeedScreen() {
  const router = useRouter();
  const [isCapturing, setIsCapturing] = useState(false);
  const [countdown, setCountdown] = useState('04:52');

  const handleCaptureNow = async () => {
    setIsCapturing(true);
    await aiService.captureImage();
    setIsCapturing(false);
    router.push('/ai/result');
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
        <Text style={styles.title}>Camera Feed</Text>
        <TouchableOpacity style={styles.headerIcon}>
          <Ionicons name="scan-outline" size={22} color={colors.textPrimary} />
        </TouchableOpacity>
      </View>

      {/* Main Viewfinder Card */}
      <View style={styles.viewfinderCard}>
        {/* Top Info Bar */}
        <View style={styles.viewfinderHeader}>
          <Text style={styles.liveViewText}>Live View</Text>
          <View style={styles.onBadge}>
            <View style={styles.greenDot} />
            <Text style={styles.onText}>ON</Text>
          </View>
        </View>

        {/* Camera Image with Targeting Reticle */}
        <View style={styles.cameraFrame}>
          <Image
            source={{
              uri: 'https://images.unsplash.com/photo-1530836369250-ef72a3f5cda8?w=800',
            }}
            style={styles.cameraStream}
            resizeMode="cover"
          />

          {/* Viewfinder Target Brackets */}
          <View style={[styles.cornerBracket, styles.topLeft]} />
          <View style={[styles.cornerBracket, styles.topRight]} />
          <View style={[styles.cornerBracket, styles.bottomLeft]} />
          <View style={[styles.cornerBracket, styles.bottomRight]} />
        </View>

        {/* Capture Timer Status */}
        <View style={styles.captureInfoRow}>
          <Ionicons name="radio-button-on" size={14} color={colors.leafGreen} />
          <Text style={styles.captureTimerText}>Next capture in {countdown}</Text>
        </View>

        {/* Thumbnail Carousel of Past Captures */}
        <View style={styles.thumbnailsRow}>
          {PREVIOUS_CAPTURES.map((imgUri, index) => (
            <TouchableOpacity
              key={`thumb-${index}`}
              style={styles.thumbnailWrapper}
              onPress={() => router.push('/ai/result')}
            >
              <Image source={{ uri: imgUri }} style={styles.thumbnail} />
            </TouchableOpacity>
          ))}
        </View>
      </View>

      {/* Bottom Controls */}
      <View style={styles.controlsRow}>
        <Button
          title={isCapturing ? 'Analyzing...' : 'Capture Now'}
          onPress={handleCaptureNow}
          variant="primary"
          loading={isCapturing}
          style={styles.captureButton}
        />
        <TouchableOpacity
          style={styles.settingsButton}
          onPress={() => router.push('/settings')}
          activeOpacity={0.7}
        >
          <Ionicons name="settings-outline" size={22} color={colors.textPrimary} />
        </TouchableOpacity>
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
  viewfinderCard: {
    backgroundColor: '#0F1813',
    borderRadius: radii.huge,
    padding: spacing.md,
    marginBottom: spacing.xl,
    overflow: 'hidden',
  },
  viewfinderHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: spacing.sm,
    paddingHorizontal: spacing.xs,
  },
  liveViewText: {
    fontSize: 16,
    fontWeight: typography.fontWeight.bold,
    color: '#FFFFFF',
  },
  onBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(52, 168, 83, 0.2)',
    paddingHorizontal: spacing.sm,
    paddingVertical: 3,
    borderRadius: radii.pill,
    gap: 4,
  },
  greenDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: colors.leafGreen,
  },
  onText: {
    fontSize: 11,
    fontWeight: typography.fontWeight.bold,
    color: '#34A853',
  },
  cameraFrame: {
    width: '100%',
    height: 240,
    borderRadius: radii.lg,
    overflow: 'hidden',
    position: 'relative',
    marginBottom: spacing.md,
  },
  cameraStream: {
    width: '100%',
    height: '100%',
  },
  cornerBracket: {
    position: 'absolute',
    width: 24,
    height: 24,
    borderColor: '#FFFFFF',
  },
  topLeft: {
    top: 16,
    left: 16,
    borderTopWidth: 2,
    borderLeftWidth: 2,
  },
  topRight: {
    top: 16,
    right: 16,
    borderTopWidth: 2,
    borderRightWidth: 2,
  },
  bottomLeft: {
    bottom: 16,
    left: 16,
    borderBottomWidth: 2,
    borderLeftWidth: 2,
  },
  bottomRight: {
    bottom: 16,
    right: 16,
    borderBottomWidth: 2,
    borderRightWidth: 2,
  },
  captureInfoRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginBottom: spacing.sm,
    paddingHorizontal: spacing.xs,
  },
  captureTimerText: {
    fontSize: 12,
    color: '#A0B4A8',
    fontWeight: typography.fontWeight.medium,
  },
  thumbnailsRow: {
    flexDirection: 'row',
    gap: spacing.sm,
    paddingTop: spacing.xs,
    justifyContent: 'space-between',
  },
  thumbnailWrapper: {
    flex: 1,
    aspectRatio: 1,
    borderRadius: radii.sm,
    overflow: 'hidden',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.2)',
  },
  thumbnail: {
    width: '100%',
    height: '100%',
  },
  controlsRow: {
    flexDirection: 'row',
    gap: spacing.md,
    alignItems: 'center',
    marginBottom: spacing.xxl,
  },
  captureButton: {
    flex: 1,
  },
  settingsButton: {
    width: 48,
    height: 48,
    borderRadius: radii.button,
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
    alignItems: 'center',
    justifyContent: 'center',
  },
});
