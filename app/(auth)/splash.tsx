import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity, Image } from 'react-native';
import { useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { colors } from '../../constants/colors';
import { typography } from '../../constants/typography';
import { spacing } from '../../constants/spacing';
import { radii } from '../../constants/radii';

export default function SplashScreen() {
  const router = useRouter();

  return (
    <SafeAreaView style={styles.container}>
      {/* Top Branding */}
      <View style={styles.header}>
        <View style={styles.logoContainer}>
          <Ionicons name="leaf" size={40} color={colors.leafGreen} />
        </View>
        <Text style={styles.brandTitle}>VertiFarm</Text>
        <Text style={styles.brandSubtitle}>Smarter Farming</Text>
        <Text style={styles.brandSubtitle}>Healthier Tomorrow</Text>
      </View>

      {/* Hero Botanical Image */}
      <View style={styles.imageContainer}>
        <Image
          source={{
            uri: 'https://images.unsplash.com/photo-1530836369250-ef72a3f5cda8?w=800',
          }}
          style={styles.heroImage}
          resizeMode="cover"
        />
      </View>

      {/* Bottom CTA Card */}
      <View style={styles.bottomContainer}>
        <TouchableOpacity
          style={styles.ctaButton}
          onPress={() => router.push('/(auth)/login')}
          activeOpacity={0.8}
        >
          <Text style={styles.tagline}>Monitor. Analyze. Grow Better.</Text>
          <View style={styles.arrowCircle}>
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
    backgroundColor: colors.primary,
    justifyContent: 'space-between',
    paddingHorizontal: spacing.screenPadding,
  },
  header: {
    alignItems: 'center',
    paddingTop: spacing.xxl,
  },
  logoContainer: {
    marginBottom: spacing.sm,
  },
  brandTitle: {
    fontSize: 32,
    fontWeight: typography.fontWeight.bold,
    color: colors.textInverse,
    marginBottom: spacing.xs,
    letterSpacing: -0.5,
  },
  brandSubtitle: {
    fontSize: 16,
    color: '#A8D5BA',
    fontWeight: typography.fontWeight.medium,
    lineHeight: 22,
  },
  imageContainer: {
    flex: 1,
    marginVertical: spacing.xl,
    borderRadius: radii.huge,
    overflow: 'hidden',
    backgroundColor: '#244D38',
  },
  heroImage: {
    width: '100%',
    height: '100%',
  },
  bottomContainer: {
    paddingBottom: spacing.xxl,
  },
  ctaButton: {
    backgroundColor: colors.surface,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: spacing.md,
    paddingHorizontal: spacing.xl,
    borderRadius: radii.pill,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.15,
    shadowRadius: 10,
    elevation: 4,
  },
  tagline: {
    fontSize: 15,
    fontWeight: typography.fontWeight.semibold,
    color: colors.primary,
  },
  arrowCircle: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: colors.primaryMuted,
    alignItems: 'center',
    justifyContent: 'center',
  },
});
