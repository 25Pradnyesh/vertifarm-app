import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  TextInput,
  ActivityIndicator,
  Alert,
  Platform,
} from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import * as WebBrowser from 'expo-web-browser';
import * as Google from 'expo-auth-session/providers/google';
import { ScreenContainer } from '../../components/ui/ScreenContainer';
import { Button } from '../../components/ui/Button';
import { colors } from '../../constants/colors';
import { typography } from '../../constants/typography';
import { spacing } from '../../constants/spacing';
import { radii } from '../../constants/radii';
import { authService } from '../../services/authService';

// Ensure pending auth sessions are completed upon redirect
WebBrowser.maybeCompleteAuthSession();

export default function LoginScreen() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [isEmailLoading, setIsEmailLoading] = useState(false);
  const [isGoogleLoading, setIsGoogleLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Warm up system browser on Android for smoother OAuth popup
  useEffect(() => {
    if (Platform.OS === 'android') {
      WebBrowser.warmUpAsync();
      return () => {
        WebBrowser.coolDownAsync();
      };
    }
  }, []);

  const googleClientIds = authService.getGoogleClientIds();
  const isGoogleConfigured = authService.isGoogleConfigured();

  // Configure Expo Google Auth Request Hook
  const [request, response, promptAsync] = Google.useAuthRequest({
    clientId: googleClientIds.clientId,
    webClientId: googleClientIds.webClientId,
    iosClientId: googleClientIds.iosClientId,
    androidClientId: googleClientIds.androidClientId,
    scopes: ['openid', 'profile', 'email'],
    selectAccount: true,
  });

  // Handle Google OAuth response lifecycle: success, cancellation, and error
  useEffect(() => {
    if (!response) return;

    // 1. Cancellation state: user dismissed or canceled dialog
    if (response.type === 'cancel' || response.type === 'dismiss') {
      setIsGoogleLoading(false);
      return;
    }

    // 2. Error state: provider or OAuth protocol error
    if (response.type === 'error') {
      setIsGoogleLoading(false);
      const msg =
        (response.error as any)?.message ||
        response.params?.error_description ||
        'Google sign-in was unsuccessful.';
      setErrorMessage(msg);
      return;
    }

    // 3. Success state: process tokens and sign user in
    if (response.type === 'success') {
      const accessToken = response.authentication?.accessToken || response.params?.access_token;
      const idToken = response.authentication?.idToken || response.params?.id_token;
      const authCode = response.params?.code;

      // If background code-to-token exchange is in flight, wait for fulfillment
      if (!accessToken && !idToken && authCode) {
        return;
      }

      const processLogin = async () => {
        try {
          setIsGoogleLoading(true);
          setErrorMessage(null);
          await authService.handleGoogleAuthResponse(response);
          router.replace('/(tabs)');
        } catch (err: any) {
          const msg = err.message || 'Failed to complete Google authentication.';
          setErrorMessage(msg);
        } finally {
          setIsGoogleLoading(false);
        }
      };

      processLogin();
    }
  }, [response, router]);

  // Redirect to dashboard if already authenticated
  useEffect(() => {
    if (authService.isAuthenticated()) {
      router.replace('/(tabs)');
    }
  }, [router]);

  const handleGoogleSignIn = async () => {
    setErrorMessage(null);

    // If Google OAuth credentials are not set up in .env yet, inform the user
    if (!isGoogleConfigured) {
      setErrorMessage(
        'Google OAuth is not configured. Please set EXPO_PUBLIC_GOOGLE_WEB_CLIENT_ID (or platform client ID) in your .env file.'
      );
      return;
    }

    if (!request) {
      Alert.alert('Initializing', 'Google Sign-In is initializing. Please try again.');
      return;
    }

    try {
      setIsGoogleLoading(true);
      const res = await promptAsync();
      if (res.type === 'cancel' || res.type === 'dismiss') {
        setIsGoogleLoading(false);
      }
    } catch (err: any) {
      setIsGoogleLoading(false);
      setErrorMessage(err.message || 'Could not open Google sign-in window.');
    }
  };

  const handleLogin = async () => {
    setIsEmailLoading(true);
    setErrorMessage(null);
    try {
      await authService.loginWithEmail(email, password);
      router.replace('/(tabs)');
    } catch (err: any) {
      setErrorMessage(err.message || 'Login failed. Please check your credentials.');
    } finally {
      setIsEmailLoading(false);
    }
  };

  return (
    <ScreenContainer scroll={true} padding={true}>
      {/* Back Button */}
      <TouchableOpacity
        style={styles.backButton}
        onPress={() => router.back()}
        hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
      >
        <Ionicons name="arrow-back" size={24} color={colors.textPrimary} />
      </TouchableOpacity>

      {/* Logo */}
      <View style={styles.logoContainer}>
        <Ionicons name="leaf" size={48} color={colors.leafGreen} />
      </View>

      {/* Title */}
      <Text style={styles.title}>Welcome Back</Text>
      <Text style={styles.subtitle}>Sign in to your VertiFarm account</Text>

      {/* Error Message Box */}
      {errorMessage ? (
        <View style={styles.errorContainer}>
          <Ionicons name="alert-circle-outline" size={18} color={colors.status.critical.primary} />
          <Text style={styles.errorText}>{errorMessage}</Text>
        </View>
      ) : null}

      {/* Email Input */}
      <View style={styles.inputContainer}>
        <View style={styles.inputWrapper}>
          <Ionicons name="mail-outline" size={20} color={colors.textSecondary} />
          <TextInput
            style={styles.input}
            placeholder="Email"
            placeholderTextColor={colors.textMuted}
            value={email}
            onChangeText={(text) => {
              setEmail(text);
              if (errorMessage) setErrorMessage(null);
            }}
            keyboardType="email-address"
            autoCapitalize="none"
            autoCorrect={false}
          />
        </View>
      </View>

      {/* Password Input */}
      <View style={styles.inputContainer}>
        <View style={styles.inputWrapper}>
          <Ionicons name="lock-closed-outline" size={20} color={colors.textSecondary} />
          <TextInput
            style={styles.input}
            placeholder="Password"
            placeholderTextColor={colors.textMuted}
            value={password}
            onChangeText={(text) => {
              setPassword(text);
              if (errorMessage) setErrorMessage(null);
            }}
            secureTextEntry={!showPassword}
            autoCapitalize="none"
            autoCorrect={false}
          />
          <TouchableOpacity onPress={() => setShowPassword(!showPassword)}>
            <Ionicons
              name={showPassword ? 'eye-outline' : 'eye-off-outline'}
              size={20}
              color={colors.textSecondary}
            />
          </TouchableOpacity>
        </View>
      </View>

      {/* Forgot Password */}
      <TouchableOpacity style={styles.forgotPassword}>
        <Text style={styles.forgotPasswordText}>Forgot Password?</Text>
      </TouchableOpacity>

      {/* Login Button */}
      <Button
        title="Login"
        onPress={handleLogin}
        variant="primary"
        fullWidth
        loading={isEmailLoading}
        disabled={isGoogleLoading || isEmailLoading}
      />

      {/* Divider */}
      <View style={styles.dividerContainer}>
        <View style={styles.divider} />
        <Text style={styles.dividerText}>or continue with</Text>
        <View style={styles.divider} />
      </View>

      {/* Social Login */}
      <View style={styles.socialContainer}>
        <TouchableOpacity
          style={[
            styles.socialButton,
            (!isGoogleConfigured || isGoogleLoading) && styles.socialButtonDisabled,
          ]}
          onPress={handleGoogleSignIn}
          disabled={!isGoogleConfigured || isGoogleLoading || isEmailLoading}
          activeOpacity={0.7}
        >
          {isGoogleLoading ? (
            <ActivityIndicator size="small" color={colors.textPrimary} />
          ) : (
            <>
              <Ionicons
                name="logo-google"
                size={20}
                color={isGoogleConfigured ? colors.textPrimary : colors.textMuted}
              />
              <Text
                style={[
                  styles.socialButtonText,
                  !isGoogleConfigured && styles.socialButtonTextDisabled,
                ]}
              >
                Google
              </Text>
            </>
          )}
        </TouchableOpacity>
        <TouchableOpacity style={styles.socialButton} activeOpacity={0.7}>
          <Ionicons name="call-outline" size={20} color={colors.textPrimary} />
          <Text style={styles.socialButtonText}>Phone</Text>
        </TouchableOpacity>
      </View>

      {/* OAuth Configuration Notice if credentials are not configured */}
      {!isGoogleConfigured && (
        <View style={styles.oauthNoticeContainer}>
          <Ionicons name="information-circle-outline" size={16} color={colors.textSecondary} />
          <Text style={styles.oauthNoticeText}>
            Google Sign-In is unavailable (OAuth credentials not configured in .env). Sign in using email and password above.
          </Text>
        </View>
      )}

      {/* Sign Up Link */}
      <View style={styles.signupContainer}>
        <Text style={styles.signupText}>Don't have an account? </Text>
        <TouchableOpacity onPress={() => router.push('/(auth)/signup')}>
          <Text style={styles.signupLink}>Sign Up</Text>
        </TouchableOpacity>
      </View>
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  backButton: {
    marginTop: spacing.md,
    marginBottom: spacing.xl,
  },
  logoContainer: {
    alignItems: 'center',
    marginBottom: spacing.xl,
  },
  title: {
    fontSize: 28,
    fontWeight: typography.fontWeight.bold,
    color: colors.textPrimary,
    marginBottom: spacing.sm,
  },
  subtitle: {
    fontSize: 14,
    color: colors.textSecondary,
    marginBottom: spacing.xxl,
  },
  errorContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.status.critical.background,
    borderWidth: 1,
    borderColor: colors.status.critical.border,
    borderRadius: radii.sm,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    marginBottom: spacing.lg,
    gap: spacing.xs,
  },
  errorText: {
    fontSize: 13,
    color: colors.status.critical.text,
    flex: 1,
  },
  inputContainer: {
    marginBottom: spacing.lg,
  },
  inputWrapper: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.surface,
    borderRadius: radii.input,
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.md,
    borderWidth: 1,
    borderColor: colors.borderLight,
  },
  input: {
    flex: 1,
    marginLeft: spacing.sm,
    fontSize: typography.fontSize.input,
    color: colors.textPrimary,
  },
  forgotPassword: {
    alignSelf: 'flex-end',
    marginBottom: spacing.xl,
  },
  forgotPasswordText: {
    fontSize: 13,
    color: colors.primary,
    fontWeight: typography.fontWeight.medium,
  },
  dividerContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginVertical: spacing.xxl,
  },
  divider: {
    flex: 1,
    height: 1,
    backgroundColor: colors.divider,
  },
  dividerText: {
    marginHorizontal: spacing.md,
    fontSize: 12,
    color: colors.textMuted,
  },
  socialContainer: {
    flexDirection: 'row',
    gap: spacing.md,
    marginBottom: spacing.xl,
  },
  socialButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: colors.surface,
    borderRadius: radii.button,
    paddingVertical: spacing.md,
    borderWidth: 1,
    borderColor: colors.border,
    gap: spacing.sm,
    minHeight: 48,
  },
  socialButtonDisabled: {
    opacity: 0.45,
    backgroundColor: colors.backgroundSecondary,
  },
  socialButtonText: {
    fontSize: 14,
    fontWeight: typography.fontWeight.medium,
    color: colors.textPrimary,
  },
  socialButtonTextDisabled: {
    color: colors.textMuted,
  },
  oauthNoticeContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.backgroundSecondary,
    borderWidth: 1,
    borderColor: colors.borderLight,
    borderRadius: radii.sm,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    marginBottom: spacing.lg,
    gap: spacing.xs,
  },
  oauthNoticeText: {
    fontSize: 12,
    color: colors.textSecondary,
    flex: 1,
    lineHeight: 16,
  },
  signupContainer: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    marginTop: spacing.lg,
    marginBottom: spacing.xxl,
  },
  signupText: {
    fontSize: 14,
    color: colors.textSecondary,
  },
  signupLink: {
    fontSize: 14,
    color: colors.primary,
    fontWeight: typography.fontWeight.semibold,
  },
});
