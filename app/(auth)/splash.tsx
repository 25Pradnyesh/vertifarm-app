import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity, Image, Dimensions } from 'react-native';
import { useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { colors } from '../../constants/colors';
import { typography } from '../../constants/typography';
import { spacing } from '../../constants/spacing';
import { radii } from '../../constants/radii';

const { width } = Dimensions.get('window');

export default function SplashScreen() {
  const router = useRouter();

  return (
    <SafeAreaView style={styles.container}>
      {/* Top Branding Section */}
      <View style={styles.header}>
        <View style={styles.logoContainer}>
          <Ionicons name="leaf" size={44} color={colors.leafGreen} />
        </View>
        <Text style={styles.brandTitle}>VertiFarm</Text>
        <Text style={styles.brandSubtitle}>Smarter Farming</Text>
        <Text style={styles.brandSubtitle}>Healthier Tomorrow</Text>
      </View>

      {/* Hero Botanical Image */}
      <View style={styles.imageWrapper}>
        <Image
          source={{
            uri: 'https://images.unsplash.com/photo-1518531933037-91b2f5f229cc?w=800',
          }}
          style={styles.heroImage}
          resizeMode="cover"
        />

        {/* Carousel Pagination Dashes */}
        <View style={styles.paginationRow}>
          <View style={[styles.dash, styles.activeDash]} />
          <View style={styles.dash} />
          <View style={styles.dash} />
        </View>

        {/* Floating Bottom Action Banner */}
        <TouchableOpacity
          style={styles.ctaCard}
          onPress={() => router.push('/(auth)/login')}
          activeOpacity={0.88}
        >
          <Text style={styles.tagline}>Monitor. Analyze. Grow Better.</Text>
          <View style={styles.arrowButton}>
            <Ionicons name="arrow-forward" size={20} color={colors.primary} />
          </View>
        </TouchableOpacity>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
    justifyContent: 'space-between',
    paddingHorizontal: spacing.screenPadding,
  },
  header: {
    alignItems: 'center',
    paddingTop: spacing.xl,
    paddingBottom: spacing.sm,
  },
  logoContainer: {
    marginBottom: spacing.xs,
  },
  brandTitle: {
    fontSize: 34,
    fontWeight: typography.fontWeight.bold,
    color: colors.textPrimary,
    marginBottom: spacing.xs,
    letterSpacing: -0.5,
  },
  brandSubtitle: {
    fontSize: 16,
    color: colors.textSecondary,
    fontWeight: typography.fontWeight.medium,
    lineHeight: 22,
  },
  imageWrapper: {
    flex: 1,
    position: 'relative',
    marginTop: spacing.md,
    marginBottom: spacing.lg,
    borderRadius: radii.huge,
    overflow: 'hidden',
    backgroundColor: '#1E3A2B',
  },
  heroImage: {
    width: '100%',
    height: '100%',
  },
  paginationRow: {
    position: 'absolute',
    bottom: 84,
    left: spacing.xl,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  dash: {
    width: 14,
    height: 3,
    borderRadius: 2,
    backgroundColor: 'rgba(255, 255, 255, 0.4)',
  },
  activeDash: {
    width: 28,
    backgroundColor: '#FFFFFF',
  },
  ctaCard: {
    position: 'absolute',
    bottom: spacing.lg,
    left: spacing.md,
    right: spacing.md,
    backgroundColor: 'rgba(27, 59, 43, 0.92)',
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: spacing.md,
    paddingLeft: spacing.xl,
    paddingRight: spacing.sm,
    borderRadius: radii.pill,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.25,
    shadowRadius: 12,
    elevation: 6,
  },
  tagline: {
    fontSize: 14,
    fontWeight: typography.fontWeight.medium,
    color: colors.textInverse,
  },
  arrowButton: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: colors.surface,
    alignItems: 'center',
    justifyContent: 'center',
  },
});
