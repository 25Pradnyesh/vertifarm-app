import { Platform } from 'react-native';
import { AuthSessionResult } from 'expo-auth-session';
import { AuthUser } from '../types';
import { config } from '../constants/config';
import { apiClient } from './apiClient';

const STORAGE_KEY = '@vertifarm_user_session';

const memoryStore: Record<string, string> = {};

/**
 * Universal safe persistent storage helper
 * Uses window.localStorage on Web, in-memory fallback for non-web environments without extra dependencies
 */
const storage = {
  getItem(key: string): string | null {
    try {
      if (typeof window !== 'undefined' && window.localStorage) {
        return window.localStorage.getItem(key);
      }
    } catch (e) {
      console.warn('[authService] storage getItem error:', e);
    }
    return memoryStore[key] ?? null;
  },
  setItem(key: string, value: string): void {
    try {
      if (typeof window !== 'undefined' && window.localStorage) {
        window.localStorage.setItem(key, value);
      }
    } catch (e) {
      console.warn('[authService] storage setItem error:', e);
    }
    memoryStore[key] = value;
  },
  removeItem(key: string): void {
    try {
      if (typeof window !== 'undefined' && window.localStorage) {
        window.localStorage.removeItem(key);
      }
    } catch (e) {
      console.warn('[authService] storage removeItem error:', e);
    }
    delete memoryStore[key];
  },
};

function decodeBase64(base64: string): string {
  let cleanBase64 = base64.replace(/-/g, '+').replace(/_/g, '/');
  while (cleanBase64.length % 4 !== 0) {
    cleanBase64 += '=';
  }

  if (typeof atob === 'function') {
    try {
      const binary = atob(cleanBase64);
      if (typeof TextDecoder !== 'undefined') {
        const bytes = new Uint8Array(binary.length);
        for (let i = 0; i < binary.length; i++) {
          bytes[i] = binary.charCodeAt(i);
        }
        return new TextDecoder().decode(bytes);
      }
      return decodeURIComponent(escape(binary));
    } catch {
      // Fall through to Buffer or manual decoding fallback
    }
  }

  const globalBuffer = (globalThis as any).Buffer;
  if (typeof globalBuffer !== 'undefined') {
    return globalBuffer.from(cleanBase64, 'base64').toString('utf8');
  }

  // Pure JavaScript base64 decoding fallback
  const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=';
  let str = '';
  let i = 0;
  const filtered = cleanBase64.replace(/[^A-Za-z0-9+/=]/g, '');
  while (i < filtered.length) {
    const enc1 = chars.indexOf(filtered.charAt(i++));
    const enc2 = chars.indexOf(filtered.charAt(i++));
    const enc3 = chars.indexOf(filtered.charAt(i++));
    const enc4 = chars.indexOf(filtered.charAt(i++));

    const chr1 = (enc1 << 2) | (enc2 >> 4);
    const chr2 = ((enc2 & 15) << 4) | (enc3 >> 2);
    const chr3 = ((enc3 & 3) << 6) | enc4;

    str += String.fromCharCode(chr1);
    if (enc3 !== 64 && enc3 !== -1) str += String.fromCharCode(chr2);
    if (enc4 !== 64 && enc4 !== -1) str += String.fromCharCode(chr3);
  }
  try {
    return decodeURIComponent(escape(str));
  } catch {
    return str;
  }
}

/**
 * Helper to safely decode a JWT payload without external dependencies
 */
function decodeJwtPayload(token: string): Record<string, any> | null {
  try {
    const parts = token.split('.');
    if (parts.length < 2) return null;
    const base64Url = parts[1];
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
    const decoded = decodeBase64(base64);
    return JSON.parse(decoded);
  } catch (err) {
    console.warn('[authService] Unable to decode JWT payload:', err);
  }
  return null;
}

// Session state in memory
let currentUserSession: AuthUser | null = null;
type AuthStateListener = (user: AuthUser | null) => void;
const authListeners = new Set<AuthStateListener>();

// Eager restore from local storage if in browser environment
try {
  const initial = storage.getItem(STORAGE_KEY);
  if (initial) {
    currentUserSession = JSON.parse(initial);
  }
} catch {
  // Ignore parsing errors during initial sync
}

/**
 * Authentication Service
 * Production-ready abstraction for Google OAuth and local sessions.
 * Preserves mock email authentication for development.
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
    return Boolean(activeId && !activeId.startsWith('vertifarm-placeholder') && activeId.trim().length > 0);
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

    // Use placeholder strings if unconfigured so invariantClientId does not throw during render
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
    verified_email?: boolean;
  }> {
    // 1. Try Google UserInfo v2 endpoint
    try {
      const response = await fetch('https://www.googleapis.com/userinfo/v2/me', {
        headers: { Authorization: `Bearer ${accessToken}` },
      });
      if (response.ok) {
        const data = await response.json();
        return {
          id: data.id || data.sub,
          email: data.email,
          name: data.name || (data.email ? data.email.split('@')[0] : 'VertiFarm Grower'),
          picture: data.picture,
          verified_email: data.verified_email,
        };
      }
    } catch (e) {
      console.warn('[authService] Google v2 userinfo fetch failed:', e);
    }

    // 2. Fallback to OpenID Connect userinfo endpoint
    const oidcResponse = await fetch('https://openidconnect.googleapis.com/v1/userinfo', {
      headers: { Authorization: `Bearer ${accessToken}` },
    });

    if (!oidcResponse.ok) {
      throw new Error(`Failed to fetch Google user profile: ${oidcResponse.status} ${oidcResponse.statusText}`);
    }

    const oidcData = await oidcResponse.json();
    return {
      id: oidcData.sub,
      email: oidcData.email,
      name: oidcData.name || (oidcData.email ? oidcData.email.split('@')[0] : 'VertiFarm Grower'),
      picture: oidcData.picture,
      verified_email: oidcData.email_verified,
    };
  },

  /**
   * Restore persisted local session from storage
   */
  async restoreSession(): Promise<AuthUser | null> {
    try {
      const stored = storage.getItem(STORAGE_KEY);
      if (stored) {
        currentUserSession = JSON.parse(stored) as AuthUser;
        // If stored session lacks an accessToken and backend is reachable, re-authenticate
        if (!currentUserSession.accessToken && apiClient.isConfigured() && currentUserSession.email) {
          try {
            const res = await apiClient.post<{ access_token: string; user: AuthUser }>('/auth/login', {
              email: currentUserSession.email,
            });
            currentUserSession.accessToken = res.access_token;
            storage.setItem(STORAGE_KEY, JSON.stringify(currentUserSession));
          } catch (e) {
            console.warn('[authService] Could not auto-refresh access token on restore:', e);
          }
        }
        return currentUserSession;
      }
    } catch (err) {
      console.warn('[authService] restoreSession error:', err);
    }
    return currentUserSession;
  },

  /**
   * Save user session locally
   */
  async saveSession(user: AuthUser | null): Promise<void> {
    currentUserSession = user;
    if (user) {
      storage.setItem(STORAGE_KEY, JSON.stringify(user));
    } else {
      storage.removeItem(STORAGE_KEY);
    }
    authListeners.forEach((listener) => {
      try {
        listener(user);
      } catch (e) {
        console.warn('[authService] listener error:', e);
      }
    });
  },

  /**
   * Handle an AuthSession response from Google OAuth prompt
   * Retrieves Google subject ID, name, email, and avatar picture,
   * creates persistent local session, and returns AuthUser.
   */
  async handleGoogleAuthResponse(response: AuthSessionResult): Promise<AuthUser | null> {
    if (response.type === 'cancel' || response.type === 'dismiss') {
      return null;
    }

    if (response.type === 'error') {
      const errorDescription =
        (response.error as any)?.message ||
        response.params?.error_description ||
        response.params?.error ||
        'Google authentication failed.';
      throw new Error(errorDescription);
    }

    if (response.type === 'success') {
      const params = response.params || {};
      const accessToken = response.authentication?.accessToken || params.access_token;
      const idToken = response.authentication?.idToken || params.id_token;

      let googleId = '';
      let email = '';
      let name = '';
      let avatarUrl: string | undefined = undefined;

      // 1. Try to fetch user info with access token if available
      if (accessToken) {
        try {
          const googleUser = await this.fetchGoogleUserInfo(accessToken);
          googleId = googleUser.id;
          email = googleUser.email;
          name = googleUser.name;
          avatarUrl = googleUser.picture;
        } catch (fetchError) {
          console.warn('[authService] fetchGoogleUserInfo failed, falling back to id_token decode:', fetchError);
        }
      }

      // 2. Fall back to decoding id_token if access token fetch wasn't available or failed
      if ((!email || !googleId) && idToken) {
        const decoded = decodeJwtPayload(idToken);
        if (decoded) {
          googleId = googleId || decoded.sub || '';
          email = email || decoded.email || '';
          name = name || decoded.name || (email ? email.split('@')[0] : '');
          avatarUrl = avatarUrl || decoded.picture;
        }
      }

      // In production OAuth, a real Google subject ID and email are strictly required
      if (!googleId || !email) {
        throw new Error('Could not retrieve verified Google account identity. Please try again.');
      }

      // If backend is configured, exchange Google ID token for authenticated backend JWT session
      if (apiClient.isConfigured() && idToken) {
        try {
          const backendRes = await apiClient.post<{
            access_token: string;
            token_type: string;
            user: AuthUser;
          }>('/auth/google', { id_token: idToken });

          const user: AuthUser = {
            ...backendRes.user,
            accessToken: backendRes.access_token,
            idToken,
            avatarUrl: avatarUrl || backendRes.user.avatarUrl,
            authProvider: 'google',
          };
          await this.saveSession(user);
          return user;
        } catch (backendErr) {
          console.warn('[authService] Backend Google auth exchange failed:', backendErr);
          if (!config.demoMode) {
            throw backendErr;
          }
        }
      }

      const user: AuthUser = {
        id: googleId,
        googleId,
        name: name.trim() || email.split('@')[0],
        email: email.trim(),
        avatarUrl,
        role: 'Farm Owner',
        farmName: 'Greenhouse Alpha',
        authProvider: 'google',
        accessToken: accessToken || 'test-token',
        idToken: idToken || undefined,
        createdAt: new Date().toISOString(),
      };

      await this.saveSession(user);
      return user;
    }

    return null;
  },

  /**
   * Email/Password Login
   * Authenticates against FastAPI backend and saves authenticated JWT session
   */
  async loginWithEmail(email: string, password?: string): Promise<AuthUser> {
    const trimmedEmail = email.trim() || 'operator@vertifarm.io';

    if (apiClient.isConfigured()) {
      try {
        const response = await apiClient.post<{
          access_token: string;
          token_type: string;
          user: AuthUser;
        }>('/auth/login', {
          email: trimmedEmail,
          password: password || undefined,
        });

        const authUser: AuthUser = {
          ...response.user,
          accessToken: response.access_token,
          authProvider: 'email',
        };

        await this.saveSession(authUser);
        return authUser;
      } catch (err: any) {
        if (!config.demoMode) {
          throw err;
        }
        console.warn('[authService] Backend login failed, falling back to demo mode:', err);
      }
    } else if (!config.demoMode && !__DEV__) {
      throw new Error('API backend is not configured. Please set EXPO_PUBLIC_API_URL or run the backend.');
    }

    // Explicit demo / offline mode
    await new Promise((resolve) => setTimeout(resolve, 250));
    const displayName = trimmedEmail
      ? trimmedEmail.split('@')[0].charAt(0).toUpperCase() + trimmedEmail.split('@')[0].slice(1)
      : 'VertiFarm Operator';

    const profile: AuthUser = {
      id: `usr-email-${Date.now()}`,
      name: displayName,
      email: trimmedEmail,
      role: 'Farm Manager',
      farmName: 'Greenhouse 1',
      authProvider: 'email',
      accessToken: 'test-token',
      createdAt: new Date().toISOString(),
    };

    await this.saveSession(profile);
    return profile;
  },

  /**
   * Email Signup
   * Registers a new account with the backend and saves authenticated JWT session
   */
  async signupWithEmail(name: string, email: string, password?: string): Promise<AuthUser> {
    const trimmedEmail = email.trim();
    const trimmedName = name.trim() || (trimmedEmail ? trimmedEmail.split('@')[0] : 'VertiFarm Grower');

    if (apiClient.isConfigured()) {
      try {
        const response = await apiClient.post<{
          access_token: string;
          token_type: string;
          user: AuthUser;
        }>('/auth/signup', {
          name: trimmedName,
          email: trimmedEmail,
          password: password || undefined,
        });

        const authUser: AuthUser = {
          ...response.user,
          accessToken: response.access_token,
          authProvider: 'email',
        };

        await this.saveSession(authUser);
        return authUser;
      } catch (err: any) {
        if (!config.demoMode) {
          throw err;
        }
        console.warn('[authService] Backend signup failed, falling back to demo mode:', err);
      }
    } else if (!config.demoMode && !__DEV__) {
      throw new Error('API backend is not configured. Please set EXPO_PUBLIC_API_URL or run the backend.');
    }

    // Explicit demo / offline mode
    await new Promise((resolve) => setTimeout(resolve, 250));
    const profile: AuthUser = {
      id: `usr-signup-${Date.now()}`,
      name: trimmedName,
      email: trimmedEmail || 'grower@vertifarm.io',
      role: 'Farm Owner',
      farmName: 'Greenhouse Alpha',
      authProvider: 'email',
      accessToken: 'test-token',
      createdAt: new Date().toISOString(),
    };

    await this.saveSession(profile);
    return profile;
  },

  /**
   * Retrieve currently signed-in user profile
   */
  getCurrentUser(): AuthUser | null {
    return currentUserSession;
  },

  /**
   * Check if a user is currently authenticated
   */
  isAuthenticated(): boolean {
    return currentUserSession !== null;
  },

  /**
   * Sign out current user and clear stored session
   */
  async logout(): Promise<void> {
    await new Promise((resolve) => setTimeout(resolve, 100));
    await this.saveSession(null);
  },

  /**
   * Subscribe to authentication session state changes
   */
  onAuthStateChange(listener: AuthStateListener): () => void {
    authListeners.add(listener);
    return () => {
      authListeners.delete(listener);
    };
  },
};
