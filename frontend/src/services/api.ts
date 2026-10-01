import axios from 'axios';
import type { AxiosError, InternalAxiosRequestConfig } from 'axios';
import type { ApiError } from '@/types';
import { diagnostics } from '@/utils/diagnostics';
import { monitor } from '@/services/monitoring';
import {
  clearTokens,
  getAccessToken,
  getRefreshToken,
  setTokens,
  type TokenPair,
} from '@/features/auth/token-storage';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
  },
});

type RetriableConfig = InternalAxiosRequestConfig & { _retry?: boolean };

interface RefreshResponse extends TokenPair {
  token_type?: string;
}

let refreshInFlight: Promise<boolean> | null = null;

function isAuthEndpoint(url: string): boolean {
  return /\/auth\/(login|register|refresh|logout|token)(\/|\?|$)/.test(url);
}

function hasSession(): boolean {
  return Boolean(getAccessToken() || getRefreshToken());
}

async function performRefresh(): Promise<boolean> {
  const refreshToken = getRefreshToken();
  if (!refreshToken) {
    clearTokens();
    return false;
  }
  try {
    const baseURL = typeof api.defaults.baseURL === 'string' ? api.defaults.baseURL : '';
    const response = await axios.post<RefreshResponse>(
      `${baseURL}/auth/refresh`,
      { refresh_token: refreshToken },
      { timeout: 15000, headers: { 'Content-Type': 'application/json' } }
    );
    const data = response.data;
    if (!data || !data.access_token) {
      clearTokens();
      return false;
    }
    setTokens(data);
    return true;
  } catch {
    clearTokens();
    return false;
  }
}

export function refreshAccessToken(): Promise<boolean> {
  if (!refreshInFlight) {
    refreshInFlight = performRefresh().finally(() => {
      refreshInFlight = null;
    });
  }
  return refreshInFlight;
}

export function setAuthHeaders(token: string): void {
  api.defaults.headers.common.Authorization = `Bearer ${token}`;
}

export function clearAuthHeaders(): void {
  api.defaults.headers.common.Authorization = null;
}

function redirectToLogin(): void {
  if (typeof window === 'undefined' || typeof window.location === 'undefined') return;
  const path = window.location.pathname;
  if (path.startsWith('/login') || path.startsWith('/register')) return;
  try {
    window.location.assign('/login');
  } catch {
    /* navigation is best effort — the session is already cleared */
  }
}

api.interceptors.request.use(
  (config) => {
    if (!navigator.onLine) {
      return Promise.reject(new Error('No internet connection. Please check your network and try again.'));
    }
    const token = getAccessToken();
    if (token) {
      config.headers.set('Authorization', `Bearer ${token}`);
    } else {
      config.headers.delete('Authorization');
    }
    return config;
  },
  (error) => {
    diagnostics.recordNetworkError(error.message);
    monitor.error('Request error', { message: error.message });
    return Promise.reject(error);
  }
);

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError<ApiError>) => {
    const original = error.config as RetriableConfig | undefined;
    const status = error.response?.status || 0;

    if (status === 401 && original && !original._retry && hasSession() && !isAuthEndpoint(original.url || '')) {
      original._retry = true;
      const refreshed = await refreshAccessToken();
      if (refreshed) {
        return api(original);
      }
      clearAuthHeaders();
      redirectToLogin();
    }

    const endpoint = error.config?.url || 'unknown';
    const message =
      error.response?.data?.detail ||
      (status === 429 ? 'Too many requests. Please wait a moment and try again.' : undefined) ||
      (status === 422 ? 'The submitted data is invalid. Please check your input and try again.' : undefined) ||
      (status === 0 ? 'Unable to reach the server. Please check your connection.' : undefined) ||
      (status >= 500 ? 'The server encountered an error. Please try again later.' : undefined) ||
      error.message ||
      'An unexpected error occurred';

    if (status >= 400 || !error.response) {
      diagnostics.recordApiFailure(endpoint, status, message);
      monitor.error('API failure', { endpoint, status, message });
    }

    return Promise.reject(new Error(message));
  }
);

export default api;
