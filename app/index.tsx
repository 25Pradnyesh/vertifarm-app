import React, { useEffect } from 'react';
import { View, ActivityIndicator, StyleSheet } from 'react-native';
import { useRouter } from 'expo-router';
import { authService } from '../services/authService';
import { colors } from '../constants/colors';

export default function Index() {
  const router = useRouter();

  useEffect(() => {
    let isMounted = true;

    async function checkAuthSession() {
      try {
        const user = await authService.restoreSession();
        if (!isMounted) return;

        if (user) {
          router.replace('/(tabs)');
        } else {
          router.replace('/(auth)/splash');
        }
      } catch {
        if (isMounted) {
          router.replace('/(auth)/splash');
        }
      }
    }

    checkAuthSession();

    return () => {
      isMounted = false;
    };
  }, [router]);

  return (
    <View style={styles.container}>
      <ActivityIndicator size="large" color={colors.primary} />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
    justifyContent: 'center',
    alignItems: 'center',
  },
});
