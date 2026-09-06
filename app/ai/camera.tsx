import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { ScreenContainer } from '../../components/ui/ScreenContainer';
import { Button } from '../../components/ui/Button';
import { colors } from '../../constants/colors';
import { typography } from '../../constants/typography';
import { spacing } from '../../constants/spacing';

export default function CameraFeedScreen() {
  const router = useRouter();

  return (
    <ScreenContainer scroll={true} padding={true}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => router.back()}>
          <Ionicons name="arrow-back" size={24} color={colors.textPrimary} />
        </TouchableOpacity>
        <Text style={styles.title}>Camera Feed</Text>
        <View style={{ width: 24 }} />
      </View>

      <View style={styles.placeholder}>
        <Text style={styles.placeholderText}>📷</Text>
        <Text style={styles.placeholderTitle}>Live Camera Feed</Text>
        <Text style={styles.placeholderSubtext}>
          Automatic plant monitoring camera stream will be displayed here.
        </Text>
        <View style={styles.buttonWrapper}>
          <Button
            title="View Scan Result"
            onPress={() => router.push('/ai/result')}
            variant="primary"
            fullWidth
          />
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
    marginBottom: spacing.xl,
  },
  title: {
    fontSize: typography.fontSize.navTitle,
    fontWeight: typography.fontWeight.bold,
    color: colors.textPrimary,
  },
  placeholder: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  placeholderText: {
    fontSize: 64,
    marginBottom: spacing.lg,
  },
  placeholderTitle: {
    fontSize: 18,
    fontWeight: typography.fontWeight.semibold,
    color: colors.textPrimary,
    marginBottom: spacing.sm,
  },
  placeholderSubtext: {
    fontSize: 14,
    color: colors.textSecondary,
    textAlign: 'center',
    paddingHorizontal: spacing.xl,
    marginBottom: spacing.xl,
  },
  buttonWrapper: {
    width: '100%',
    maxWidth: 280,
  },
});
