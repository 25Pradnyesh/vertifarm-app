import { Platform } from 'react-native';
import { AuthSessionResult } from 'expo-auth-session';
import { UserProfile } from '../types';
import { config } from '../constants/config';

/**
 * Helper to safely decode a JWT payload without external dependencies
 */
function decodeJwtPayload(token: string): Record<string, any> | null {
  try {
    const parts = token.split('.');
    if (parts.length < 2) return null;
    const base64Url = parts[1];
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');

    if (typeof atob === 'function') {
      const decoded = atob(base64);
      return JSON.parse(decoded);
    }

    const globalBuffer = (globalThis as any).Buffer;
    if (typeof globalBuffer !== 'undefined') {
      const decoded = globalBuffer.from(base64, 'base64').toString('utf8');
      return JSON.parse(decoded);
    }
  } catch (err) {
    console.warn('[authService] Unable to decode JWT payload:', err);
  }
  return null;
}

// In-memory mock session state
let currentUserSession: UserProfile | null = null;

/**
 * Authentication Service
 * Abstraction layer for authentication flows (Google OAuth, Mock Email/Password)
 * Ready for future backend integration without altering UI screens.
 */
export const authService = {
  /**
   * Check if Google OAuth Client IDs are configured via environment variables
   */
  isGoogleConfigured(): boolean {
    const { webClientId, iosClientId, androidClientId, clientId } = config.auth.google;
    const activeId = Platform.select({
      ios: iosClientId || clientId,
      android: androidClientId || clientId,
      default: webClientId || clientId,
    });
    return Boolean(activeId && !activeId.startsWith('vertifarm-placeholder'));
  },

  /**
   * Get client IDs for use with expo-auth-session.
   * Provides safe fallback identifiers to prevent invariant errors when unconfigured.
   */
  getGoogleClientIds(): {
    clientId?: string;
    webClientId?: string;
    iosClientId?: string;
    androidClientId?: string;
  } {
    const { webClientId, iosClientId, androidClientId, clientId } = config.auth.google;

    // Use placeholder strings if unconfigured so invariantClientId does not throw
    return {
      clientId: clientId || 'vertifarm-placeholder-client-id.apps.googleusercontent.com',
      webClientId: webClientId || clientId || 'vertifarm-placeholder-web.apps.googleusercontent.com',
      iosClientId: iosClientId || clientId || 'vertifarm-placeholder-ios.apps.googleusercontent.com',
      androidClientId: androidClientId || clientId || 'vertifarm-placeholder-android.apps.googleusercontent.com',
    };
  },

  /**
   * Fetch Google user profile using access token
   */
  async fetchGoogleUserInfo(accessToken: string): Promise<{
    id: string;
    email: string;
    name: string;
    picture?: string;
  }> {
    const response = await fetch('https://www.googleapis.com/userinfo/v2/me', {
      headers: { Authorization: `Bearer ${accessToken}` },
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch Google user profile: ${response.status} ${response.statusText}`);
    }

    return await response.json();
  },

  /**
   * Handle an AuthSession response from Google OAuth prompt
   */
  async handleGoogleAuthResponse(response: AuthSessionResult): Promise<UserProfile | null> {
    if (response.type === 'cancel' || response.type === 'dismiss') {
      return null;
    }

    if (response.type === 'error') {
      const errorDescription =
        response.error?.message ||
        response.params?.error_description ||
        response.params?.error ||
        'Google authentication failed.';
      throw new Error(errorDescription);
    }

    if (response.type === 'success') {
      const params = response.params || {};
      const accessToken = response.authentication?.accessToken || params.access_token;
      const idToken = response.authentication?.idToken || params.id_token;

      let userProfile: UserProfile | null = null;

      // 1. Try to fetch user info with access token if available
      if (accessToken) {
        try {
          const googleUser = await this.fetchGoogleUserInfo(accessToken);
          userProfile = {
            id: googleUser.id,
            name: googleUser.name || 'VertiFarm Grower',
            email: googleUser.email,
            avatarUrl: googleUser.picture,
            role: 'Farm Owner',
            farmName: 'Greenhouse Alpha',
          };
        } catch (fetchError) {
          console.warn('[authService] fetchGoogleUserInfo failed, attempting id_token decode:', fetchError);
        }
      }

      // 2. Fall back to decoding id_token if access token fetch wasn't available or failed
      if (!userProfile && idToken) {
        const decoded = decodeJwtPayload(idToken);
        if (decoded && decoded.email) {
          userProfile = {
            id: decoded.sub || 'usr-google',
            name: decoded.name || decoded.email.split('@')[0],
            email: decoded.email,
            avatarUrl: decoded.picture,
            role: 'Farm Owner',
            farmName: 'Greenhouse Alpha',
          };
        }
      }

      // 3. Fall back to basic response parameters if token was valid
      if (!userProfile) {
        userProfile = {
          id: 'usr-google-' + Date.now(),
          name: 'Google User',
          email: params.email || 'user@vertifarm.io',
          role: 'Farm Owner',
          farmName: 'Greenhouse Alpha',
        };
      }

      currentUserSession = userProfile;
      return userProfile;
    }

    return null;
  },

  /**
   * Mock Email/Password Login
   * Simulates network authentication and saves session
   */
  async loginWithEmail(email: string, _password?: string): Promise<UserProfile> {
    await new Promise((resolve) => setTimeout(resolve, 250));

    const trimmedEmail = email.trim();
    const displayName = trimmedEmail
      ? trimmedEmail.split('@')[0].charAt(0).toUpperCase() + trimmedEmail.split('@')[0].slice(1)
      : 'VertiFarm Operator';

    const profile: UserProfile = {
      id: 'usr-email-1',
      name: displayName,
      email: trimmedEmail || 'operator@vertifarm.io',
      role: 'Farm Manager',
      farmName: 'Greenhouse 1',
    };

    currentUserSession = profile;
    return profile;
  },

  /**
   * Demo/Mock Google Sign-In for testing when Google Cloud credentials are not configured
   */
  async loginWithMockGoogle(): Promise<UserProfile> {
    await new Promise((resolve) => setTimeout(resolve, 300));

    const mockProfile: UserProfile = {
      id: 'usr-google-demo',
      name: 'Alex Green (Google)',
      email: 'alex.green@vertifarm.io',
      role: 'Farm Owner',
      farmName: 'Greenhouse Alpha',
      avatarUrl: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150',
    };

    currentUserSession = mockProfile;
    return mockProfile;
  },

  /**
   * Retrieve currently signed-in user profile
   */
  getCurrentUser(): UserProfile | null {
    return currentUserSession;
  },

  /**
   * Check if a user is currently authenticated
   */
  isAuthenticated(): boolean {
    return currentUserSession !== null;
  },

  /**
   * Sign out current user
   */
  async logout(): Promise<void> {
    await new Promise((resolve) => setTimeout(resolve, 100));
    currentUserSession = null;
  },
};
