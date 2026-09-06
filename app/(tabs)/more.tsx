import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView } from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { ScreenContainer } from '../../components/ui/ScreenContainer';
import { Card } from '../../components/ui/Card';
import { colors } from '../../constants/colors';
import { typography } from '../../constants/typography';
import { spacing } from '../../constants/spacing';
import { radii } from '../../constants/radii';

export default function MoreScreen() {
  const router = useRouter();

  const menuItems = [
    {
      title: 'Sensor Status',
      subtitle: 'View active hardware devices and heartbeats',
      icon: 'hardware-chip-outline',
      route: '/sensors',
    },
    {
      title: 'My Farms',
      subtitle: 'Manage farm locations and greenhouses',
      icon: 'business-outline',
      route: '/farms',
    },
    {
      title: 'Recommendations',
      subtitle: 'Agronomic suggestions and care tips',
      icon: 'bulb-outline',
      route: '/recommendations',
    },
    {
      title: 'History',
      subtitle: 'Review past telemetry, scans, and alerts',
      icon: 'time-outline',
      route: '/history',
    },
    {
      title: 'Settings',
      subtitle: 'Thresholds, units, preferences, and account',
      icon: 'settings-outline',
      route: '/settings',
    },
  ];

  return (
    <ScreenContainer scroll={true} padding={true}>
      <View style={styles.header}>
        <Text style={styles.title}>More</Text>
      </View>

      <View style={styles.menuContainer}>
        {menuItems.map((item, index) => (
          <TouchableOpacity
            key={item.title}
            style={styles.menuItemWrapper}
            onPress={() => router.push(item.route as any)}
            activeOpacity={0.7}
          >
            <Card variant="default" padding="medium" style={styles.menuCard}>
              <View style={styles.menuContent}>
                <View style={styles.iconCircle}>
                  <Ionicons name={item.icon as any} size={22} color={colors.primary} />
                </View>

                <View style={styles.menuTextContainer}>
                  <Text style={styles.menuTitle}>{item.title}</Text>
                  <Text style={styles.menuSubtitle}>{item.subtitle}</Text>
                </View>

                <Ionicons name="chevron-forward" size={20} color={colors.textMuted} />
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
    marginTop: spacing.sm,
    marginBottom: spacing.xl,
  },
  title: {
    fontSize: typography.fontSize.screenTitle,
    fontWeight: typography.fontWeight.bold,
    color: colors.textPrimary,
  },
  menuContainer: {
    gap: spacing.md,
    paddingBottom: spacing.xxl,
  },
  menuItemWrapper: {
    width: '100%',
  },
  menuCard: {},
  menuContent: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  iconCircle: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: colors.primaryMuted,
    alignItems: 'center',
    justifyContent: 'center',
  },
  menuTextContainer: {
    flex: 1,
    marginLeft: spacing.md,
  },
  menuTitle: {
    fontSize: 16,
    fontWeight: typography.fontWeight.semibold,
    color: colors.textPrimary,
    marginBottom: 2,
  },
  menuSubtitle: {
    fontSize: 12,
    color: colors.textSecondary,
  },
});
