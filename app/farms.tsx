import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView, Alert } from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { ScreenContainer } from '../components/ui/ScreenContainer';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { colors } from '../constants/colors';
import { typography } from '../constants/typography';
import { spacing } from '../constants/spacing';
import { radii } from '../constants/radii';
import { farmService } from '../services/farmService';
import { Farm } from '../types';

export default function FarmsScreen() {
  const router = useRouter();
  const [farms, setFarms] = useState<Farm[]>([]);

  useEffect(() => {
    farmService.getFarms().then(setFarms);
  }, []);

  const handleAddFarm = () => {
    Alert.alert(
      'Add New Farm Facility',
      'Enter new greenhouse details or connect an STM32 controller.',
      [{ text: 'Dismiss' }, { text: 'Configure', onPress: () => {} }]
    );
  };

  return (
    <ScreenContainer scroll={true} padding={true}>
      {/* Header */}
      <View style={styles.header}>
        <View style={styles.headerLeft}>
          <TouchableOpacity
            style={styles.backButton}
            onPress={() => router.back()}
            hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
          >
            <Ionicons name="arrow-back" size={24} color={colors.textPrimary} />
          </TouchableOpacity>
          <Text style={styles.title}>My Farms</Text>
        </View>

        <TouchableOpacity
          style={styles.addFarmButton}
          onPress={handleAddFarm}
          activeOpacity={0.8}
        >
          <Ionicons name="add" size={16} color={colors.textInverse} />
          <Text style={styles.addFarmText}>Add Farm</Text>
        </TouchableOpacity>
      </View>

      {/* Farms List */}
      <View style={styles.farmsList}>
        {farms.map((farm) => (
          <TouchableOpacity
            key={farm.id}
            onPress={() => router.replace('/(tabs)')}
            activeOpacity={0.8}
          >
            <Card variant="default" padding="large" style={styles.farmCard}>
              <View style={styles.farmTopRow}>
                <View style={styles.farmTitleGroup}>
                  <Text style={styles.farmName}>{farm.name}</Text>
                  <Text style={styles.farmLocation}>{farm.location}</Text>
                </View>
                <Badge
                  status={farm.isActive ? 'healthy' : 'offline'}
                  label={farm.isActive ? 'Active' : 'Inactive'}
                  variant="subtle"
                  style={styles.farmBadge}
                />
              </View>

              <View style={styles.farmDivider} />

              <View style={styles.farmStatsRow}>
                <View style={styles.statItem}>
                  <Text style={styles.statNumber}>{farm.sensorCount}</Text>
                  <Text style={styles.statLabel}>Sensors</Text>
                </View>

                <View style={styles.statDivider} />

                <View style={styles.statItem}>
                  <Text style={styles.statNumber}>{farm.zoneCount}</Text>
                  <Text style={styles.statLabel}>Zones</Text>
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
    marginBottom: spacing.xl,
  },
  headerLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
  },
  backButton: {
    padding: spacing.xs,
  },
  title: {
    fontSize: typography.fontSize.screenTitle,
    fontWeight: typography.fontWeight.bold,
    color: colors.textPrimary,
  },
  addFarmButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.primary,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.xs + 3,
    borderRadius: radii.pill,
    gap: 4,
  },
  addFarmText: {
    fontSize: 13,
    fontWeight: typography.fontWeight.semibold,
    color: colors.textInverse,
  },
  farmsList: {
    gap: spacing.lg,
    paddingBottom: spacing.xxl,
  },
  farmCard: {
    borderRadius: radii.card,
  },
  farmTopRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
  },
  farmTitleGroup: {
    flex: 1,
  },
  farmName: {
    fontSize: 18,
    fontWeight: typography.fontWeight.bold,
    color: colors.textPrimary,
    marginBottom: 4,
  },
  farmLocation: {
    fontSize: 13,
    color: colors.textSecondary,
  },
  farmBadge: {
    paddingHorizontal: spacing.md,
  },
  farmDivider: {
    height: 1,
    backgroundColor: colors.divider,
    marginVertical: spacing.md,
  },
  farmStatsRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  statItem: {
    flexDirection: 'row',
    alignItems: 'baseline',
    gap: spacing.xs,
  },
  statNumber: {
    fontSize: 16,
    fontWeight: typography.fontWeight.bold,
    color: colors.textPrimary,
  },
  statLabel: {
    fontSize: 13,
    color: colors.textSecondary,
  },
  statDivider: {
    width: 1,
    height: 14,
    backgroundColor: colors.border,
    marginHorizontal: spacing.lg,
  },
});
