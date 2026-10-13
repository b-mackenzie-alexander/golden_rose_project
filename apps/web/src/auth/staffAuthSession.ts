import { useEffect, useState } from 'react';

export type StaffAuthProvider = 'synthetic' | 'google' | 'unsupported';

export type StaffAuthConfig = {
  authMode: 'synthetic' | 'staff_oidc';
  provider: StaffAuthProvider;
  googleClientId: string | null;
};

export type StaffAuthConfigResult =
  | { ok: true; value: StaffAuthConfig }
  | { ok: false; failure: 'unavailable' | 'unexpected' };

export type StaffAuthSessionSnapshot = {
  idToken: string | null;
};

const authConfigKeys = new Set(['auth_mode', 'provider', 'google_client_id']);
const providers = new Set<StaffAuthProvider>(['synthetic', 'google', 'unsupported']);
const listeners = new Set<() => void>();
const sessionStorageKey = 'golden-rose-staff-id-token-v1';

type StoredStaffToken = {
  idToken: string;
  expiresAt: number;
};

function browserSessionStorage(): Storage | null {
  try {
    return window.sessionStorage;
  } catch {
    return null;
  }
}

function clearStoredStaffToken() {
  browserSessionStorage()?.removeItem(sessionStorageKey);
}

function readStoredStaffToken(): StoredStaffToken | null {
  const storage = browserSessionStorage();
  if (storage === null) return null;
  const rawValue = storage.getItem(sessionStorageKey);
  if (rawValue === null) return null;
  try {
    const parsed = JSON.parse(rawValue) as unknown;
    if (
      !object(parsed)
      || typeof parsed.idToken !== 'string'
      || typeof parsed.expiresAt !== 'number'
      || !Number.isSafeInteger(parsed.expiresAt)
    ) {
      clearStoredStaffToken();
      return null;
    }
    const expiresAt = parsed.expiresAt;
    if (expiresAt <= 0 || Date.now() >= expiresAt) {
      clearStoredStaffToken();
      return null;
    }
    return {
      idToken: parsed.idToken,
      expiresAt,
    };
  } catch {
    clearStoredStaffToken();
    return null;
  }
}

function persistStaffToken(token: string, expiresAt: number | null) {
  const storage = browserSessionStorage();
  if (storage === null) return;
  if (expiresAt === null || expiresAt <= Date.now()) {
    clearStoredStaffToken();
    return;
  }
  try {
    storage.setItem(sessionStorageKey, JSON.stringify({ idToken: token, expiresAt }));
  } catch {
    clearStoredStaffToken();
  }
}

const storedStaffToken = readStoredStaffToken();
let idToken: string | null = storedStaffToken?.idToken ?? null;
let tokenExpiresAt = storedStaffToken?.expiresAt ?? 0;

function object(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

function parseConfig(value: unknown): StaffAuthConfig | null {
  if (!object(value)) return null;
  if (Object.keys(value).some((key) => !authConfigKeys.has(key))) return null;
  if (value.auth_mode !== 'synthetic' && value.auth_mode !== 'staff_oidc') return null;
  if (typeof value.provider !== 'string' || !providers.has(value.provider as StaffAuthProvider)) return null;
  if (value.google_client_id !== null && typeof value.google_client_id !== 'string') return null;
  return {
    authMode: value.auth_mode,
    provider: value.provider as StaffAuthProvider,
    googleClientId: value.google_client_id,
  };
}

function notify() {
  for (const listener of listeners) listener();
}

export function getStaffAuthSnapshot(): StaffAuthSessionSnapshot {
  if (idToken !== null && tokenExpiresAt > 0 && Date.now() >= tokenExpiresAt) {
    idToken = null;
    tokenExpiresAt = 0;
    clearStoredStaffToken();
  }
  return { idToken };
}

export function subscribeStaffAuth(listener: () => void) {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}

export function setStaffIdToken(token: string, expiresAt: number | null) {
  idToken = token;
  tokenExpiresAt = expiresAt ?? 0;
  persistStaffToken(token, expiresAt);
  notify();
}

export function clearStaffIdToken() {
  idToken = null;
  tokenExpiresAt = 0;
  clearStoredStaffToken();
  notify();
}

export function bearerHeaders(headers: HeadersInit | undefined): Headers {
  const next = new Headers(headers);
  const snapshot = getStaffAuthSnapshot();
  if (snapshot.idToken !== null && !next.has('Authorization')) {
    next.set('Authorization', `Bearer ${snapshot.idToken}`);
  }
  return next;
}

export async function staffApiFetch(input: RequestInfo | URL, init: RequestInit = {}): Promise<Response> {
  const snapshot = getStaffAuthSnapshot();
  if (snapshot.idToken === null) return fetch(input, init);
  return fetch(input, {
    ...init,
    headers: bearerHeaders(init.headers),
  });
}

export async function getStaffAuthConfig(): Promise<StaffAuthConfigResult> {
  let response: Response;
  try {
    response = await fetch('/api/staff/v1/staff-auth-config', {
      cache: 'no-store',
      credentials: 'same-origin',
      mode: 'same-origin',
      redirect: 'error',
      referrerPolicy: 'no-referrer',
      headers: { Accept: 'application/json' },
    });
  } catch {
    return { ok: false, failure: 'unavailable' };
  }
  if (!(response instanceof Response)) return { ok: false, failure: 'unavailable' };
  if (response.status < 200 || response.status >= 300) return { ok: false, failure: 'unavailable' };
  if (!/^application\/(?:json|problem\+json)(?:\s*;.*)?$/i.test(response.headers.get('Content-Type') ?? '')) {
    await response.body?.cancel();
    return { ok: false, failure: 'unexpected' };
  }
  try {
    const parsed = parseConfig(await response.json());
    return parsed === null ? { ok: false, failure: 'unexpected' } : { ok: true, value: parsed };
  } catch {
    return { ok: false, failure: 'unexpected' };
  }
}

export function getJwtExpiration(token: string): number | null {
  const parts = token.split('.');
  if (parts.length < 2) return null;
  const payloadPart = parts[1];
  if (payloadPart === undefined) return null;
  try {
    const payload = JSON.parse(window.atob(payloadPart.replace(/-/g, '+').replace(/_/g, '/'))) as unknown;
    if (!object(payload) || !Number.isSafeInteger(payload.exp)) return null;
    return Number(payload.exp) * 1000;
  } catch {
    return null;
  }
}

export function useStaffAuthSession() {
  const [snapshot, setSnapshot] = useState(getStaffAuthSnapshot);

  useEffect(() => subscribeStaffAuth(() => {
    setSnapshot(getStaffAuthSnapshot());
  }), []);

  return snapshot;
}
