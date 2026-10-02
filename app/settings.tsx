import React, { useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, Image, Switch, Alert, ScrollView, Platform } from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { ScreenContainer } from '../components/ui/ScreenContainer';
import { Card } from '../components/ui/Card';
import { colors } from '../constants/colors';
import { typography } from '../constants/typography';
import { spacing } from '../constants/spacing';
import { radii } from '../constants/radii';
import { authService } from '../services/authService';

export default function SettingsScreen() {
  const router = useRouter();
  const [isDarkMode, setIsDarkMode] = useState(false);
  const currentUser = authService.getCurrentUser();

  const handleLogout = async () => {
    // Alert.alert with button callbacks does not work reliably on Expo Web;
    // use window.confirm for web and native Alert for iOS/Android.
    if (Platform.OS === 'web') {
      const confirmed = typeof window !== 'undefined' &&
        window.confirm('Are you sure you want to log out of your VertiFarm account?');
      if (confirmed) {
        await authService.logout();
        router.replace('/(auth)/login');
      }
    } else {
      Alert.alert('Sign Out', 'Are you sure you want to log out of your VertiFarm account?', [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Logout',
          style: 'destructive',
          onPress: async () => {
            await authService.logout();
            router.replace('/(auth)/login');
          },
        },
      ]);
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
        <Text style={styles.title}>Settings</Text>
        <View style={{ width: 24 }} />
      </View>

      {/* User Profile Card */}
      <Card variant="default" padding="medium" style={styles.profileCard}>
        <View style={styles.profileRow}>
          <Image
            source={{
              uri:
                currentUser?.avatarUrl ||
                'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=200',
            }}
            style={styles.avatar}
          />
          <View style={styles.profileInfo}>
            <Text style={styles.profileName}>
              {currentUser?.name || 'Greenhouse 1'}
            </Text>
            <Text style={styles.profileRole}>
              {currentUser?.role || 'Owner'}
            </Text>
          </View>

          <TouchableOpacity
            style={styles.editButton}
            onPress={() => Alert.alert('Edit Profile', 'Profile editing will sync across cloud accounts.')}
          >
            <Text style={styles.editButtonText}>Edit Profile</Text>
          </TouchableOpacity>
        </View>
      </Card>

      {/* Settings Navigation Menu */}
      <View style={styles.menuContainer}>
        {/* Farm / Greenhouse Settings */}
        <TouchableOpacity
          style={styles.menuItem}
          onPress={() => router.push('/farms')}
          activeOpacity={0.7}
        >
          <View style={styles.menuItemLeft}>
            <Ionicons name="business-outline" size={20} color={colors.textSecondary} />
            <Text style={styles.menuItemTitle}>Farm / Greenhouse Settings</Text>
          </View>
          <Ionicons name="chevron-forward" size={18} color={colors.textMuted} />
        </TouchableOpacity>

        {/* Sensor & Device Settings */}
        <TouchableOpacity
          style={styles.menuItem}
          onPress={() => router.push('/sensors')}
          activeOpacity={0.7}
        >
          <View style={styles.menuItemLeft}>
            <Ionicons name="hardware-chip-outline" size={20} color={colors.textSecondary} />
            <Text style={styles.menuItemTitle}>Sensor & Device Settings</Text>
          </View>
          <Ionicons name="chevron-forward" size={18} color={colors.textMuted} />
        </TouchableOpacity>

        {/* Alert Preferences */}
        <TouchableOpacity
          style={styles.menuItem}
          onPress={() => router.push('/(tabs)/alerts')}
          activeOpacity={0.7}
        >
          <View style={styles.menuItemLeft}>
            <Ionicons name="notifications-outline" size={20} color={colors.textSecondary} />
            <Text style={styles.menuItemTitle}>Alert Preferences</Text>
          </View>
          <Ionicons name="chevron-forward" size={18} color={colors.textMuted} />
        </TouchableOpacity>

        {/* Notification Settings */}
        <TouchableOpacity
          style={styles.menuItem}
          onPress={() => Alert.alert('Notification Settings', 'Push and threshold SMS preferences.')}
          activeOpacity={0.7}
        >
          <View style={styles.menuItemLeft}>
            <Ionicons name="volume-medium-outline" size={20} color={colors.textSecondary} />
            <Text style={styles.menuItemTitle}>Notification Settings</Text>
          </View>
          <Ionicons name="chevron-forward" size={18} color={colors.textMuted} />
        </TouchableOpacity>

        {/* Units */}
        <TouchableOpacity
          style={styles.menuItem}
          onPress={() => Alert.alert('Unit Preferences', 'Metric units: Celsius (°C), Percentage (%), Parts Per Million (ppm), Lux.')}
          activeOpacity={0.7}
        >
          <View style={styles.menuItemLeft}>
            <Ionicons name="options-outline" size={20} color={colors.textSecondary} />
            <Text style={styles.menuItemTitle}>Units</Text>
          </View>
          <View style={styles.unitsValueGroup}>
            <Text style={styles.unitsText}>°C, %, ppm</Text>
            <Ionicons name="chevron-forward" size={18} color={colors.textMuted} />
          </View>
        </TouchableOpacity>

        {/* Dark Mode Toggle */}
        <View style={styles.menuItem}>
          <View style={styles.menuItemLeft}>
            <Ionicons name="moon-outline" size={20} color={colors.textSecondary} />
            <Text style={styles.menuItemTitle}>Dark Mode</Text>
          </View>
          <Switch
            value={isDarkMode}
            onValueChange={setIsDarkMode}
            trackColor={{ false: colors.border, true: colors.primary }}
            thumbColor={colors.surface}
          />
        </View>

        {/* Help & Support */}
        <TouchableOpacity
          style={styles.menuItem}
          onPress={() => Alert.alert('Help & Support', 'Documentation: https://vertifarm.io/docs\nSupport email: help@vertifarm.io')}
          activeOpacity={0.7}
        >
          <View style={styles.menuItemLeft}>
            <Ionicons name="help-circle-outline" size={20} color={colors.textSecondary} />
            <Text style={styles.menuItemTitle}>Help & Support</Text>
          </View>
          <Ionicons name="chevron-forward" size={18} color={colors.textMuted} />
        </TouchableOpacity>

        {/* About App */}
        <TouchableOpacity
          style={styles.menuItem}
          onPress={() => Alert.alert('VertiFarm Mobile', 'Version 1.0.0\nIoT + AI Vertical Farming Platform\nBuilt for STM32 & Cloud Edge.')}
          activeOpacity={0.7}
        >
          <View style={styles.menuItemLeft}>
            <Ionicons name="information-circle-outline" size={20} color={colors.textSecondary} />
            <Text style={styles.menuItemTitle}>About App</Text>
          </View>
          <Ionicons name="chevron-forward" size={18} color={colors.textMuted} />
        </TouchableOpacity>
      </View>

      {/* Logout Button */}
      <TouchableOpacity style={styles.logoutButton} onPress={handleLogout} activeOpacity={0.7}>
        <Text style={styles.logoutText}>Logout</Text>
      </TouchableOpacity>
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
    fontSize: typography.fontSize.screenTitle,
    fontWeight: typography.fontWeight.bold,
    color: colors.textPrimary,
  },
  profileCard: {
    borderRadius: radii.card,
    marginBottom: spacing.xl,
  },
  profileRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  avatar: {
    width: 48,
    height: 48,
    borderRadius: 24,
    marginRight: spacing.md,
    backgroundColor: colors.backgroundSecondary,
  },
  profileInfo: {
    flex: 1,
  },
  profileName: {
    fontSize: 16,
    fontWeight: typography.fontWeight.bold,
    color: colors.textPrimary,
    marginBottom: 2,
  },
  profileRole: {
    fontSize: 13,
    color: colors.textSecondary,
  },
  editButton: {
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.xs + 2,
    borderRadius: radii.pill,
  },
  editButtonText: {
    fontSize: 12,
    fontWeight: typography.fontWeight.semibold,
    color: colors.textPrimary,
  },
  menuContainer: {
    backgroundColor: colors.surface,
    borderRadius: radii.card,
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.xs,
    borderWidth: 1,
    borderColor: colors.borderLight,
    marginBottom: spacing.xxl,
  },
  menuItem: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: spacing.md,
    borderBottomWidth: 1,
    borderBottomColor: colors.borderLight,
  },
  menuItemLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.md,
  },
  menuItemTitle: {
    fontSize: 14,
    fontWeight: typography.fontWeight.medium,
    color: colors.textPrimary,
  },
  unitsValueGroup: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  unitsText: {
    fontSize: 13,
    color: colors.textMuted,
  },
  logoutButton: {
    alignItems: 'center',
    paddingVertical: spacing.md,
    marginBottom: spacing.xxl,
  },
  logoutText: {
    fontSize: 15,
    fontWeight: typography.fontWeight.bold,
    color: colors.status.critical.primary,
  },
});
