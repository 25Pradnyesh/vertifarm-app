import React, { useEffect, useState } from 'react';
import { Stack, useRouter, useSegments } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { colors } from '../constants/colors';
import { authService } from '../services/authService';

export default function RootLayout() {
  const segments = useSegments();
  const router = useRouter();
  const [isReady, setIsReady] = useState(false);

  useEffect(() => {
    let mounted = true;
    authService.restoreSession().finally(() => {
      if (mounted) {
        setIsReady(true);
      }
    });

    const unsubscribe = authService.onAuthStateChange((user) => {
      if (!mounted) return;
      const firstSegment = segments[0] as string | undefined;
      if (!firstSegment) return;
      const inAuthGroup = firstSegment === '(auth)';
      if (!user && !inAuthGroup) {
        router.replace('/(auth)/login');
      } else if (user && inAuthGroup) {
        router.replace('/(tabs)');
      }
    });

    return () => {
      mounted = false;
      unsubscribe();
    };
  }, [segments, router]);

  useEffect(() => {
    if (!isReady) return;

    const firstSegment = segments[0] as string | undefined;
    if (!firstSegment) return;

    const inAuthGroup = firstSegment === '(auth)';
    const authenticated = authService.isAuthenticated();

    if (!authenticated && !inAuthGroup) {
      // Unauthenticated users remain in the auth flow
      router.replace('/(auth)/login');
    } else if (authenticated && inAuthGroup) {
      // Authenticated users are routed to the dashboard
      router.replace('/(tabs)');
    }
  }, [isReady, segments, router]);

  return (
    <SafeAreaProvider>
      <StatusBar style="dark" />
      <Stack
        screenOptions={{
          headerShown: false,
          contentStyle: { backgroundColor: colors.background },
          animation: 'slide_from_right',
        }}
      >
        {/* Auth Group */}
        <Stack.Screen name="(auth)" options={{ headerShown: false }} />

        {/* Main Tabs */}
        <Stack.Screen name="(tabs)" options={{ headerShown: false }} />

        {/* Stack Routes */}
        <Stack.Screen
          name="live-data/[metric]"
          options={{
            headerShown: false,
            presentation: 'card',
          }}
        />
        <Stack.Screen
          name="alerts/[id]"
          options={{
            headerShown: false,
            presentation: 'card',
          }}
        />
        <Stack.Screen
          name="sensors/index"
          options={{
            headerShown: false,
            presentation: 'card',
          }}
        />
        <Stack.Screen
          name="sensors/add"
          options={{
            headerShown: false,
            presentation: 'card',
          }}
        />
        <Stack.Screen
          name="ai/camera"
          options={{
            headerShown: false,
            presentation: 'card',
          }}
        />
        <Stack.Screen
          name="ai/result"
          options={{
            headerShown: false,
            presentation: 'card',
          }}
        />
        <Stack.Screen
          name="farms"
          options={{
            headerShown: false,
            presentation: 'card',
          }}
        />
        <Stack.Screen
          name="recommendations"
          options={{
            headerShown: false,
            presentation: 'card',
          }}
        />
        <Stack.Screen
          name="history"
          options={{
            headerShown: false,
            presentation: 'card',
          }}
        />
        <Stack.Screen
          name="settings"
          options={{
            headerShown: false,
            presentation: 'card',
          }}
        />
      </Stack>
    </SafeAreaProvider>
  );
}
