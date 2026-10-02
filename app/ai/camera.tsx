import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Image,
  Alert,
  ActivityIndicator,
} from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import * as ImagePicker from 'expo-image-picker';
import { ScreenContainer } from '../../components/ui/ScreenContainer';
import { Card } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { colors } from '../../constants/colors';
import { typography } from '../../constants/typography';
import { spacing } from '../../constants/spacing';
import { radii } from '../../constants/radii';
import { aiService } from '../../services/aiService';

const SAMPLE_LEAF_IMAGES = [
  {
    name: 'Coriander Sample',
    uri: 'https://images.unsplash.com/photo-1540420773420-3366772f4999?w=400',
  },
  {
    name: 'Fenugreek Sample',
    uri: 'https://images.unsplash.com/photo-1530836369250-ef72a3f5cda8?w=400',
  },
  {
    name: 'Leaf Spot Sample',
    uri: 'https://images.unsplash.com/photo-1592417817098-8f3d6910a566?w=400',
  },
  {
    name: 'Healthy Foliage',
    uri: 'https://images.unsplash.com/photo-1518531933037-91b2f5f229cc?w=400',
  },
];

export default function CameraFeedScreen() {
  const router = useRouter();
  const [isDiagnosing, setIsDiagnosing] = useState(false);
  const [selectedUri, setSelectedUri] = useState<string>(
    'https://images.unsplash.com/photo-1530836369250-ef72a3f5cda8?w=800'
  );
  const [analysisStatus, setAnalysisStatus] = useState<string>('');

  /**
   * Run diagnosis on an image URI and navigate to results screen
   */
  const processImageForDiagnosis = async (uri: string, filename?: string) => {
    try {
      setIsDiagnosing(true);
      setAnalysisStatus('Uploading leaf image to AI engine...');

      const diagnosis = await aiService.diagnoseImage(uri, {
        filename,
        farmId: 'farm-1',
      });

      setAnalysisStatus('Classifying leaf morphology...');
      router.push({
        pathname: '/ai/result',
        params: {
          diagnosis: JSON.stringify(diagnosis),
        },
      });
    } catch (err: any) {
      console.error('Diagnosis failed:', err);
      Alert.alert(
        'Diagnosis Error',
        err?.message || 'Failed to analyze the leaf image. Please try again.',
        [{ text: 'OK' }]
      );
    } finally {
      setIsDiagnosing(false);
      setAnalysisStatus('');
    }
  };

  /**
   * Launch device camera to snap a real leaf photo
   */
  const handleTakePhoto = async () => {
    try {
      const permission = await ImagePicker.requestCameraPermissionsAsync();
      if (!permission.granted) {
        Alert.alert(
          'Camera Permission Required',
          'VertiFarm needs access to your camera to take leaf diagnostic photos.',
          [{ text: 'OK' }]
        );
        return;
      }

      const result = await ImagePicker.launchCameraAsync({
        mediaTypes: ['images'],
        allowsEditing: true,
        aspect: [1, 1],
        quality: 0.85,
      });

      if (!result.canceled && result.assets && result.assets.length > 0) {
        const asset = result.assets[0];
        setSelectedUri(asset.uri);
        await processImageForDiagnosis(asset.uri, asset.fileName || 'camera_leaf.jpg');
      }
    } catch (err: any) {
      console.error('Camera launch failed:', err);
      Alert.alert('Camera Error', 'Could not open camera on this device.');
    }
  };

  /**
   * Pick an image from photo library
   */
  const handlePickFromGallery = async () => {
    try {
      const permission = await ImagePicker.requestMediaLibraryPermissionsAsync();
      if (!permission.granted) {
        Alert.alert(
          'Photo Library Access Required',
          'VertiFarm needs access to your photo library to select leaf images.',
          [{ text: 'OK' }]
        );
        return;
      }

      const result = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: ['images'],
        allowsEditing: true,
        aspect: [1, 1],
        quality: 0.85,
      });

      if (!result.canceled && result.assets && result.assets.length > 0) {
        const asset = result.assets[0];
        setSelectedUri(asset.uri);
        await processImageForDiagnosis(asset.uri, asset.fileName || 'gallery_leaf.jpg');
      }
    } catch (err: any) {
      console.error('Gallery pick failed:', err);
      Alert.alert('Gallery Error', 'Could not open photo library.');
    }
  };

  /**
   * Diagnose the current preview or trigger edge camera capture
   */
  const handleCaptureNow = async () => {
    if (selectedUri) {
      await processImageForDiagnosis(selectedUri, 'viewfinder_leaf.jpg');
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
        <Text style={styles.title}>Camera Feed & AI</Text>
        <TouchableOpacity
          style={styles.headerIcon}
          onPress={handlePickFromGallery}
          hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
        >
          <Ionicons name="images-outline" size={22} color={colors.textPrimary} />
        </TouchableOpacity>
      </View>

      {/* Main Viewfinder Card */}
      <View style={styles.viewfinderCard}>
        {/* Top Info Bar */}
        <View style={styles.viewfinderHeader}>
          <Text style={styles.liveViewText}>Target Viewfinder</Text>
          <View style={styles.onBadge}>
            <View style={styles.greenDot} />
            <Text style={styles.onText}>AI READY</Text>
          </View>
        </View>

        {/* Camera Image with Targeting Reticle */}
        <View style={styles.cameraFrame}>
          <Image
            source={{ uri: selectedUri }}
            style={styles.cameraStream}
            resizeMode="cover"
          />

          {/* Viewfinder Target Brackets */}
          <View style={[styles.cornerBracket, styles.topLeft]} />
          <View style={[styles.cornerBracket, styles.topRight]} />
          <View style={[styles.cornerBracket, styles.bottomLeft]} />
          <View style={[styles.cornerBracket, styles.bottomRight]} />

          {/* Center Scan Reticle */}
          <View style={styles.centerReticle}>
            <Ionicons name="scan" size={40} color="rgba(255, 255, 255, 0.5)" />
          </View>

          {/* Analyzing Overlay */}
          {isDiagnosing && (
            <View style={styles.analyzingOverlay}>
              <ActivityIndicator size="large" color={colors.leafGreen} />
              <Text style={styles.analyzingText}>MobileNetV3 Inference</Text>
              <Text style={styles.analyzingSubtext}>{analysisStatus}</Text>
            </View>
          )}
        </View>

        {/* Capture Timer Status */}
        <View style={styles.captureInfoRow}>
          <Ionicons name="radio-button-on" size={14} color={colors.leafGreen} />
          <Text style={styles.captureTimerText}>
            Align leaf within brackets for 224x224 classification
          </Text>
        </View>

        {/* Quick Sample Presets */}
        <Text style={styles.sampleSectionLabel}>Sample Leaf Presets</Text>
        <View style={styles.thumbnailsRow}>
          {SAMPLE_LEAF_IMAGES.map((sample, index) => (
            <TouchableOpacity
              key={`sample-${index}`}
              style={[
                styles.thumbnailWrapper,
                selectedUri === sample.uri && styles.selectedThumbnail,
              ]}
              onPress={() => setSelectedUri(sample.uri)}
              disabled={isDiagnosing}
            >
              <Image source={{ uri: sample.uri }} style={styles.thumbnail} />
            </TouchableOpacity>
          ))}
        </View>
      </View>

      {/* Action Buttons */}
      <View style={styles.actionButtonsColumn}>
        <Button
          title={isDiagnosing ? 'Analyzing...' : 'Diagnose Leaf in Viewfinder'}
          onPress={handleCaptureNow}
          variant="primary"
          loading={isDiagnosing}
          disabled={isDiagnosing}
          fullWidth
          style={styles.mainActionButton}
        />

        <View style={styles.secondaryActionsRow}>
          <TouchableOpacity
            style={styles.secondaryButton}
            onPress={handleTakePhoto}
            disabled={isDiagnosing}
            activeOpacity={0.7}
          >
            <Ionicons name="camera" size={20} color={colors.primary} />
            <Text style={styles.secondaryButtonText}>Take Photo</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.secondaryButton}
            onPress={handlePickFromGallery}
            disabled={isDiagnosing}
            activeOpacity={0.7}
          >
            <Ionicons name="image" size={20} color={colors.primary} />
            <Text style={styles.secondaryButtonText}>Upload Image</Text>
          </TouchableOpacity>
        </View>
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
    marginBottom: spacing.lg,
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
    height: 250,
    borderRadius: radii.lg,
    overflow: 'hidden',
    position: 'relative',
    marginBottom: spacing.md,
    backgroundColor: '#000000',
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
  centerReticle: {
    position: 'absolute',
    top: '50%',
    left: '50%',
    transform: [{ translateX: -20 }, { translateY: -20 }],
  },
  analyzingOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(15, 24, 19, 0.88)',
    alignItems: 'center',
    justifyContent: 'center',
    padding: spacing.md,
  },
  analyzingText: {
    marginTop: spacing.sm,
    color: '#FFFFFF',
    fontSize: 15,
    fontWeight: typography.fontWeight.bold,
  },
  analyzingSubtext: {
    marginTop: 4,
    color: '#A0B4A8',
    fontSize: 12,
    textAlign: 'center',
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
  sampleSectionLabel: {
    fontSize: 11,
    fontWeight: typography.fontWeight.semibold,
    color: '#71887C',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginBottom: spacing.xs,
    paddingHorizontal: spacing.xs,
  },
  thumbnailsRow: {
    flexDirection: 'row',
    gap: spacing.sm,
    paddingTop: spacing.xs,
  },
  thumbnailWrapper: {
    flex: 1,
    aspectRatio: 1,
    borderRadius: radii.sm,
    overflow: 'hidden',
    borderWidth: 1.5,
    borderColor: 'rgba(255, 255, 255, 0.2)',
  },
  selectedThumbnail: {
    borderColor: colors.leafGreen,
    borderWidth: 2,
  },
  thumbnail: {
    width: '100%',
    height: '100%',
  },
  actionButtonsColumn: {
    gap: spacing.md,
    marginBottom: spacing.xxl,
  },
  mainActionButton: {
    width: '100%',
  },
  secondaryActionsRow: {
    flexDirection: 'row',
    gap: spacing.md,
  },
  secondaryButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: spacing.sm,
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: radii.button,
    paddingVertical: spacing.md,
  },
  secondaryButtonText: {
    fontSize: 14,
    fontWeight: typography.fontWeight.semibold,
    color: colors.primary,
  },
});
