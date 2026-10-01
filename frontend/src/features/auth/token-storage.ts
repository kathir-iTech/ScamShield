export type AuthRole = 'guest' | 'authenticated' | 'admin';

export interface AuthUser {
  id: string;
  email: string;
  role: AuthRole;
  display_name: string;
  created_at?: string;
  last_login_at?: string | null;
}

export interface TokenPair {
  access_token: string;
  refresh_token?: string;
  expires_in?: number;
}

interface AuthState {
  access_token?: string;
  refresh_token?: string;
  expires_in?: number;
  user?: AuthUser | null;
}

const STORAGE_KEY = 'scamshield.auth';

let memoryState: AuthState = {};

function canPersist(): boolean {
  try {
    return typeof window !== 'undefined' && typeof window.localStorage !== 'undefined';
  } catch {
    return false;
  }
}

function readState(): AuthState {
  if (!canPersist()) return memoryState;
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (raw) return JSON.parse(raw) as AuthState;
  } catch {
    /* storage unavailable or corrupted — fall back to memory */
  }
  return memoryState;
}

function writeState(next: AuthState): void {
  memoryState = next;
  if (!canPersist()) return;
  try {
    if (Object.keys(next).length > 0) {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
    } else {
      window.localStorage.removeItem(STORAGE_KEY);
    }
  } catch {
    /* quota exceeded or storage disabled — memory copy already updated */
  }
}

export function getAccessToken(): string | null {
  return readState().access_token || null;
}

export function getRefreshToken(): string | null {
  return readState().refresh_token || null;
}

export function setTokens(tokens: TokenPair): void {
  const state = readState();
  writeState({
    ...state,
    access_token: tokens.access_token,
    refresh_token: tokens.refresh_token ?? state.refresh_token,
    expires_in: tokens.expires_in ?? state.expires_in,
  });
}

export function clearTokens(): void {
  const state = readState();
  const next: AuthState = { ...state };
  delete next.access_token;
  delete next.refresh_token;
  delete next.expires_in;
  writeState(next);
}

export function getUser(): AuthUser | null {
  return readState().user ?? null;
}

export function setUser(user: AuthUser): void {
  writeState({ ...readState(), user });
}

export function clearUser(): void {
  const state = readState();
  const next: AuthState = { ...state };
  delete next.user;
  writeState(next);
}

export function isAuthenticated(): boolean {
  return Boolean(getAccessToken());
}
