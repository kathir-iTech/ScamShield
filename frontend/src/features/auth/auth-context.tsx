import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from 'react';
import api, { clearAuthHeaders, setAuthHeaders } from '@/services/api';
import {
  clearTokens,
  clearUser,
  getAccessToken,
  getRefreshToken,
  getUser,
  isAuthenticated,
  setTokens,
  setUser as persistUser,
  type AuthRole,
  type AuthUser,
  type TokenPair,
} from './token-storage';

export interface SessionResponse extends TokenPair {
  token_type?: string;
  role?: AuthRole;
}

export interface AuthContextValue {
  user: AuthUser | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, displayName: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<AuthUser>;
  hasRole: (role: AuthRole) => boolean;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUserState] = useState<AuthUser | null>(() => getUser());
  const [loading, setLoading] = useState<boolean>(() => isAuthenticated());

  const applyUser = useCallback((next: AuthUser | null) => {
    if (next) persistUser(next);
    else clearUser();
    setUserState(next);
  }, []);

  const refreshUser = useCallback(async (): Promise<AuthUser> => {
    const { data } = await api.get<AuthUser>('/auth/me');
    applyUser(data);
    const token = getAccessToken();
    if (token) setAuthHeaders(token);
    return data;
  }, [applyUser]);

  const login = useCallback(
    async (email: string, password: string): Promise<void> => {
      const { data } = await api.post<SessionResponse>('/auth/login', {
        email,
        password,
      });
      setTokens(data);
      setAuthHeaders(data.access_token);
      try {
        await refreshUser();
      } catch {
        applyUser({ id: '', email, role: data.role ?? 'authenticated', display_name: '' });
      }
    },
    [applyUser, refreshUser]
  );

  const register = useCallback(
    async (email: string, password: string, displayName: string): Promise<void> => {
      await api.post('/auth/register', {
        email,
        password,
        display_name: displayName,
      });
      await login(email, password);
    },
    [login]
  );

  const logout = useCallback(async (): Promise<void> => {
    const refreshToken = getRefreshToken();
    if (refreshToken) {
      try {
        await api.post('/auth/logout', { refresh_token: refreshToken });
      } catch {
        /* server-side revocation is best effort — local session is cleared regardless */
      }
    }
    clearTokens();
    clearUser();
    clearAuthHeaders();
    setUserState(null);
  }, []);

  const hasRole = useCallback(
    (role: AuthRole): boolean => {
      const current: AuthRole = user?.role ?? (isAuthenticated() ? 'authenticated' : 'guest');
      if (role === 'guest') return current === 'guest';
      if (role === 'authenticated') return current === 'authenticated' || current === 'admin';
      return current === 'admin';
    },
    [user]
  );

  useEffect(() => {
    if (!isAuthenticated()) {
      setLoading(false);
      return;
    }
    let cancelled = false;
    const boot = async () => {
      try {
        await refreshUser();
      } catch {
        if (!cancelled) {
          clearTokens();
          clearUser();
          setUserState(null);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    void boot();
    return () => {
      cancelled = true;
    };
  }, [refreshUser]);

  const value = useMemo(
    () => ({ user, loading, login, register, logout, refreshUser, hasRole }),
    [user, loading, login, register, logout, refreshUser, hasRole]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
