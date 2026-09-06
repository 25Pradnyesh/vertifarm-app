import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { useRouter } from 'expo-router';
import { ScreenContainer } from '../../components/ui/ScreenContainer';
import { Button } from '../../components/ui/Button';
import { colors } from '../../constants/colors';
import { typography } from '../../constants/typography';
import { spacing } from '../../constants/spacing';

export default function AIScanScreen() {
  const router = useRouter();

  return (
    <ScreenContainer scroll={true} padding={true}>
      <View style={styles.header}>
        <Text style={styles.title}>AI Plant Health</Text>
      </View>

      <View style={styles.placeholder}>
        <Text style={styles.placeholderText}>🌿</Text>
        <Text style={styles.placeholderTitle}>AI Plant Health</Text>
        <Text style={styles.placeholderSubtitle}>
          Automatic plant monitoring, disease detection, and scan results will be displayed here.
        </Text>

        <View style={styles.buttonContainer}>
          <Button
            title="View Camera Feed"
            onPress={() => router.push('/ai/camera')}
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
    marginTop: spacing.sm,
    marginBottom: spacing.xxl,
  },
  title: {
    fontSize: typography.fontSize.screenTitle,
    fontWeight: typography.fontWeight.bold,
    color: colors.textPrimary,
  },
  placeholder: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: spacing.massive,
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
  placeholderSubtitle: {
    fontSize: 14,
    color: colors.textSecondary,
    textAlign: 'center',
    paddingHorizontal: spacing.xxl,
    marginBottom: spacing.xxl,
  },
  buttonContainer: {
    width: '100%',
    maxWidth: 300,
  },
});
