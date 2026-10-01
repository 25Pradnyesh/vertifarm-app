import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView } from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { ScreenContainer } from '../components/ui/ScreenContainer';
import { Card } from '../components/ui/Card';
import { colors } from '../constants/colors';
import { typography } from '../constants/typography';
import { spacing } from '../constants/spacing';
import { radii } from '../constants/radii';
import { aiService } from '../services/aiService';
import { RecommendationItem } from '../types';

export default function RecommendationsScreen() {
  const router = useRouter();
  const [activeTab, setActiveTab] = useState<'forYou' | 'general'>('forYou');
  const [items, setItems] = useState<RecommendationItem[]>([]);

  useEffect(() => {
    aiService.getRecommendations(activeTab).then(setItems);
  }, [activeTab]);

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'irrigation':
        return <Ionicons name="sunny" size={22} color={colors.metrics.light} />;
      case 'ph':
        return <Ionicons name="flask" size={22} color={colors.leafGreen} />;
      case 'nutrition':
        return <Ionicons name="speedometer" size={22} color={colors.metrics.tds} />;
      case 'environment':
        return <Ionicons name="globe" size={22} color={colors.metrics.humidity} />;
      default:
        return <Ionicons name="bulb" size={22} color={colors.primary} />;
    }
  };

  const getCategoryBg = (category: string) => {
    switch (category) {
      case 'irrigation':
        return '#FEF3C7';
      case 'ph':
        return '#E8F5E9';
      case 'nutrition':
        return '#E6FFFA';
      case 'environment':
        return '#E0F2FE';
      default:
        return colors.backgroundSecondary;
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
        <Text style={styles.title}>Recommendations</Text>
        <View style={{ width: 24 }} />
      </View>

      {/* Tab Switcher Pills (For You / General) */}
      <View style={styles.tabsRow}>
        <TouchableOpacity
          style={[styles.tabPill, activeTab === 'forYou' && styles.tabPillActive]}
          onPress={() => setActiveTab('forYou')}
          activeOpacity={0.7}
        >
          <Text style={[styles.tabText, activeTab === 'forYou' && styles.tabTextActive]}>
            For You
          </Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.tabPill, activeTab === 'general' && styles.tabPillActive]}
          onPress={() => setActiveTab('general')}
          activeOpacity={0.7}
        >
          <Text style={[styles.tabText, activeTab === 'general' && styles.tabTextActive]}>
            General
          </Text>
        </TouchableOpacity>
      </View>

      {/* Recommendation Cards List */}
      <View style={styles.recommendationsList}>
        {items.map((item) => (
          <TouchableOpacity
            key={item.id}
            onPress={() => {
              if (item.actionableLink) {
                router.push(item.actionableLink as any);
              }
            }}
            activeOpacity={0.7}
          >
            <Card variant="default" padding="medium" style={styles.recCard}>
              <View style={styles.recRow}>
                <View
                  style={[
                    styles.iconCircle,
                    { backgroundColor: getCategoryBg(item.category) },
                  ]}
                >
                  {getCategoryIcon(item.category)}
                </View>

                <View style={styles.textGroup}>
                  <Text style={styles.recTitle}>{item.title}</Text>
                  <Text style={styles.recDesc}>{item.description}</Text>
                </View>

                <Ionicons name="chevron-forward" size={18} color={colors.textMuted} />
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
  backButton: {
    padding: spacing.xs,
  },
  title: {
    fontSize: typography.fontSize.screenTitle,
    fontWeight: typography.fontWeight.bold,
    color: colors.textPrimary,
  },
  tabsRow: {
    flexDirection: 'row',
    gap: spacing.sm,
    marginBottom: spacing.lg,
  },
  tabPill: {
    paddingHorizontal: spacing.xl,
    paddingVertical: spacing.sm,
    borderRadius: radii.pill,
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
  },
  tabPillActive: {
    backgroundColor: colors.primary,
    borderColor: colors.primary,
  },
  tabText: {
    fontSize: 13,
    fontWeight: typography.fontWeight.medium,
    color: colors.textSecondary,
  },
  tabTextActive: {
    color: colors.textInverse,
    fontWeight: typography.fontWeight.semibold,
  },
  recommendationsList: {
    gap: spacing.md,
    paddingBottom: spacing.xxl,
  },
  recCard: {
    borderRadius: radii.card,
  },
  recRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  iconCircle: {
    width: 44,
    height: 44,
    borderRadius: 22,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: spacing.md,
  },
  textGroup: {
    flex: 1,
    marginRight: spacing.sm,
  },
  recTitle: {
    fontSize: 15,
    fontWeight: typography.fontWeight.semibold,
    color: colors.textPrimary,
    marginBottom: 3,
  },
  recDesc: {
    fontSize: 13,
    color: colors.textSecondary,
    lineHeight: 18,
  },
});
