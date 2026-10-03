import { afterEach, describe, expect, it, vi } from 'vitest';

import { bearerHeaders, clearStaffIdToken, getJwtExpiration, getStaffAuthConfig, setStaffIdToken, staffApiFetch } from './staffAuthSession';

afterEach(() => {
  clearStaffIdToken();
  vi.restoreAllMocks();
});

describe('staffAuthSession', () => {
  it('attaches the staff bearer token without replacing existing headers', () => {
    setStaffIdToken('signed-token', Date.now() + 60_000);

    const headers = bearerHeaders({ Accept: 'application/json' });

    expect(headers.get('Authorization')).toBe('Bearer signed-token');
    expect(headers.get('Accept')).toBe('application/json');
  });

  it('does not attach expired or cleared tokens', () => {
    setStaffIdToken('expired-token', Date.now() - 1);

    expect(bearerHeaders(undefined).has('Authorization')).toBe(false);
  });

  it('preserves an explicit authorization header', () => {
    setStaffIdToken('signed-token', Date.now() + 60_000);

    const headers = bearerHeaders({ Authorization: 'Bearer explicit-token' });

    expect(headers.get('Authorization')).toBe('Bearer explicit-token');
  });

  it('parses JWT expirations without trusting malformed tokens', () => {
    const payload = window.btoa(JSON.stringify({ exp: 1_800_000_000 })).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/u, '');

    expect(getJwtExpiration(`header.${payload}.signature`)).toBe(1_800_000_000_000);
    expect(getJwtExpiration('not-a-jwt')).toBeNull();
    expect(getJwtExpiration('header.not-json.signature')).toBeNull();
    expect(getJwtExpiration(`header.${window.btoa(JSON.stringify({ sub: 'staff' }))}.signature`)).toBeNull();
  });

  it('loads the public staff auth config with no-store handling', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(JSON.stringify({
      auth_mode: 'staff_oidc',
      provider: 'google',
      google_client_id: 'google-client-id.apps.googleusercontent.com',
    }), { status: 200, headers: { 'Content-Type': 'application/json' } }));

    await expect(getStaffAuthConfig()).resolves.toEqual({
      ok: true,
      value: {
        authMode: 'staff_oidc',
        provider: 'google',
        googleClientId: 'google-client-id.apps.googleusercontent.com',
      },
    });
    expect(fetch).toHaveBeenCalledWith('/api/staff/v1/staff-auth-config', expect.objectContaining({
      cache: 'no-store',
      credentials: 'same-origin',
      mode: 'same-origin',
      redirect: 'error',
      referrerPolicy: 'no-referrer',
    }));
  });

  it('uses bearer headers for staff API fetches', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response('{}', { status: 200, headers: { 'Content-Type': 'application/json' } }));
    setStaffIdToken('signed-token', Date.now() + 60_000);

    await staffApiFetch('/api/staff/v1/session', { headers: { Accept: 'application/json' } });

    const call = vi.mocked(fetch).mock.calls[0];
    expect(call).toBeDefined();
    const init = call?.[1];
    expect(init?.headers).toBeInstanceOf(Headers);
    expect((init?.headers as Headers).get('Authorization')).toBe('Bearer signed-token');
    expect((init?.headers as Headers).get('Accept')).toBe('application/json');
  });

  it('leaves staff API fetches unchanged without a browser session token', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response('{}', { status: 200, headers: { 'Content-Type': 'application/json' } }));

    await staffApiFetch('/api/staff/v1/session', { headers: { Accept: 'application/json' } });

    expect(fetch).toHaveBeenCalledWith('/api/staff/v1/session', { headers: { Accept: 'application/json' } });
  });

  it('fails closed for malformed or unavailable public auth config responses', async () => {
    const fetchSpy = vi.spyOn(globalThis, 'fetch')
      .mockRejectedValueOnce(new TypeError('network unavailable'))
      .mockResolvedValueOnce(undefined as unknown as Response)
      .mockResolvedValueOnce(new Response('plain text', { status: 200, headers: { 'Content-Type': 'text/plain' } }))
      .mockResolvedValueOnce(new Response(JSON.stringify({
        auth_mode: 'staff_oidc',
        provider: 'google',
        google_client_id: 'google-client-id.apps.googleusercontent.com',
        issuer: 'https://accounts.google.com',
      }), { status: 200, headers: { 'Content-Type': 'application/json' } }))
      .mockResolvedValueOnce(new Response('{', { status: 200, headers: { 'Content-Type': 'application/json' } }));

    await expect(getStaffAuthConfig()).resolves.toEqual({ ok: false, failure: 'unavailable' });
    await expect(getStaffAuthConfig()).resolves.toEqual({ ok: false, failure: 'unavailable' });
    await expect(getStaffAuthConfig()).resolves.toEqual({ ok: false, failure: 'unexpected' });
    await expect(getStaffAuthConfig()).resolves.toEqual({ ok: false, failure: 'unexpected' });
    await expect(getStaffAuthConfig()).resolves.toEqual({ ok: false, failure: 'unexpected' });
    expect(fetchSpy).toHaveBeenCalledTimes(5);
  });
});
