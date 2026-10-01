import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, TextInput } from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { ScreenContainer } from '../../components/ui/ScreenContainer';
import { Button } from '../../components/ui/Button';
import { colors } from '../../constants/colors';
import { typography } from '../../constants/typography';
import { spacing } from '../../constants/spacing';
import { radii } from '../../constants/radii';

import { authService } from '../../services/authService';

export default function SignupScreen() {
  const router = useRouter();
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Redirect to dashboard if already authenticated
  useEffect(() => {
    if (authService.isAuthenticated()) {
      router.replace('/(tabs)');
    }
  }, [router]);

  const handleSignup = async () => {
    if (!name.trim()) {
      setErrorMessage('Please enter your full name.');
      return;
    }
    if (!email.trim()) {
      setErrorMessage('Please enter your email address.');
      return;
    }
    if (password && confirmPassword && password !== confirmPassword) {
      setErrorMessage('Passwords do not match.');
      return;
    }

    setIsLoading(true);
    setErrorMessage(null);
    try {
      await authService.signupWithEmail(name, email, password);
      router.replace('/(tabs)');
    } catch (err: any) {
      setErrorMessage(err.message || 'Signup failed.');
    } finally {
      setIsLoading(false);
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
      <Text style={styles.title}>Create Account</Text>
      <Text style={styles.subtitle}>Start monitoring your farm with VertiFarm</Text>

      {/* Error Message Box */}
      {errorMessage ? (
        <View style={styles.errorContainer}>
          <Ionicons name="alert-circle-outline" size={18} color={colors.status.critical.primary} />
          <Text style={styles.errorText}>{errorMessage}</Text>
        </View>
      ) : null}

      {/* Name Input */}
      <View style={styles.inputContainer}>
        <View style={styles.inputWrapper}>
          <Ionicons name="person-outline" size={20} color={colors.textSecondary} />
          <TextInput
            style={styles.input}
            placeholder="Full Name"
            placeholderTextColor={colors.textMuted}
            value={name}
            onChangeText={(text) => {
              setName(text);
              if (errorMessage) setErrorMessage(null);
            }}
          />
        </View>
      </View>

      {/* Email Input */}
      <View style={styles.inputContainer}>
        <View style={styles.inputWrapper}>
          <Ionicons name="mail-outline" size={20} color={colors.textSecondary} />
          <TextInput
            style={styles.input}
            placeholder="Email Address"
            placeholderTextColor={colors.textMuted}
            value={email}
            onChangeText={(text) => {
              setEmail(text);
              if (errorMessage) setErrorMessage(null);
            }}
            keyboardType="email-address"
            autoCapitalize="none"
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
            secureTextEntry
          />
        </View>
      </View>

      {/* Confirm Password Input */}
      <View style={styles.inputContainer}>
        <View style={styles.inputWrapper}>
          <Ionicons name="shield-checkmark-outline" size={20} color={colors.textSecondary} />
          <TextInput
            style={styles.input}
            placeholder="Confirm Password"
            placeholderTextColor={colors.textMuted}
            value={confirmPassword}
            onChangeText={(text) => {
              setConfirmPassword(text);
              if (errorMessage) setErrorMessage(null);
            }}
            secureTextEntry
          />
        </View>
      </View>

      {/* Signup Button */}
      <View style={styles.buttonWrapper}>
        <Button
          title="Create Account"
          onPress={handleSignup}
          variant="primary"
          fullWidth
          loading={isLoading}
        />
      </View>

      {/* Login Link */}
      <View style={styles.loginContainer}>
        <Text style={styles.loginText}>Already have an account? </Text>
        <TouchableOpacity onPress={() => router.push('/(auth)/login')}>
          <Text style={styles.loginLink}>Login</Text>
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
  buttonWrapper: {
    marginTop: spacing.xl,
  },
  loginContainer: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    marginTop: spacing.xxl,
    marginBottom: spacing.xxl,
  },
  loginText: {
    fontSize: 14,
    color: colors.textSecondary,
  },
  loginLink: {
    fontSize: 14,
    color: colors.primary,
    fontWeight: typography.fontWeight.semibold,
  },
});
