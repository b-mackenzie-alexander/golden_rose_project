import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { LanguageProvider } from '../i18n/LanguageProvider';
import { GoogleStaffSignIn } from './GoogleStaffSignIn';
import { clearStaffIdToken, setStaffIdToken } from './staffAuthSession';

type GoogleIdApi = NonNullable<NonNullable<NonNullable<Window['google']>['accounts']>['id']>;
type GoogleInitializeConfig = Parameters<GoogleIdApi['initialize']>[0];
type GoogleRenderParent = Parameters<GoogleIdApi['renderButton']>[0];

afterEach(() => {
  clearStaffIdToken();
  vi.restoreAllMocks();
  window.google = undefined;
});

function renderSignIn(onSignedIn = vi.fn()) {
  return render(
    <LanguageProvider>
      <GoogleStaffSignIn onSignedIn={onSignedIn} />
    </LanguageProvider>,
  );
}

function credentialWithExpiration(expiresAt = Date.now() + 60_000) {
  const payload = window.btoa(JSON.stringify({ exp: Math.floor(expiresAt / 1000) }))
    .replace(/\+/g, '-')
    .replace(/\//g, '_')
    .replace(/=+$/u, '');
  return `header.${payload}.signature`;
}

describe('GoogleStaffSignIn', () => {
  it('renders a Google sign-in button and stores the returned credential', async () => {
    let callback: ((response: { credential?: string }) => void) | null = null;
    const onSignedIn = vi.fn();
    const credential = credentialWithExpiration();
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(JSON.stringify({
      auth_mode: 'staff_oidc',
      provider: 'google',
      google_client_id: 'google-client-id.apps.googleusercontent.com',
    }), { status: 200, headers: { 'Content-Type': 'application/json' } }));
    const initialize = vi.fn((config: GoogleInitializeConfig) => {
      callback = config.callback;
    });
    const renderButton = vi.fn((parent: GoogleRenderParent) => {
      const button = document.createElement('button');
      button.type = 'button';
      button.textContent = 'Sign in with Google';
      parent.append(button);
    });
    const googleId: GoogleIdApi = {
      disableAutoSelect: vi.fn(),
      initialize,
      renderButton,
    };
    window.google = {
      accounts: {
        id: googleId,
      },
    };

    renderSignIn(onSignedIn);

    expect(await screen.findByText('Sign in with Google to continue.')).toBeInTheDocument();
    expect(await screen.findByRole('button', { name: 'Sign in with Google' })).toBeInTheDocument();
    expect(googleId.initialize).toHaveBeenCalledWith(expect.objectContaining({
      client_id: 'google-client-id.apps.googleusercontent.com',
      auto_select: false,
      essential_claims: 'auth_time, amr',
    }));

    await waitFor(() => {
      expect(callback).not.toBeNull();
    });
    const credentialCallback = callback as unknown as (response: { credential?: string }) => void;
    await act(async () => {
      credentialCallback({ credential });
      await Promise.resolve();
    });

    await waitFor(() => {
      expect(onSignedIn).toHaveBeenCalledTimes(1);
    });
    vi.resetModules();
    const reloadedSession = await import('./staffAuthSession');
    expect(reloadedSession.bearerHeaders(undefined).get('Authorization')).toBe(`Bearer ${credential}`);
    reloadedSession.clearStaffIdToken();
  });

  it('shows and clears a stored Google staff browser session', async () => {
    const disableAutoSelect = vi.fn();
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(JSON.stringify({
      auth_mode: 'staff_oidc',
      provider: 'google',
      google_client_id: 'google-client-id.apps.googleusercontent.com',
    }), { status: 200, headers: { 'Content-Type': 'application/json' } }));
    setStaffIdToken('stored-token', Date.now() + 60_000);
    window.google = {
      accounts: {
        id: {
          disableAutoSelect,
          initialize: vi.fn(),
          renderButton: vi.fn(),
        },
      },
    };

    renderSignIn();

    expect(await screen.findByText('Google sign-in token is ready for this browser session.')).toBeInTheDocument();
    const clearSession = screen.getByRole('button', { name: 'Clear Golden Rose session' });
    expect(clearSession).toBeInTheDocument();

    fireEvent.click(clearSession);

    await waitFor(() => {
      expect(disableAutoSelect).toHaveBeenCalledTimes(1);
    });
  });

  it('shows recoverable states for unsupported and unavailable config', async () => {
    const fetchSpy = vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(new Response(JSON.stringify({
      auth_mode: 'staff_oidc',
      provider: 'unsupported',
      google_client_id: null,
    }), { status: 200, headers: { 'Content-Type': 'application/json' } }));

    const view = renderSignIn();

    expect(await screen.findByRole('alert')).toHaveTextContent('not supported by this browser sign-in panel');

    view.unmount();
    fetchSpy.mockResolvedValueOnce(new Response('Service unavailable', { status: 503 }));
    renderSignIn();

    expect(await screen.findByRole('alert')).toHaveTextContent('Staff sign-in configuration is unavailable.');
  });

  it('does not keep a Google session when the credential callback is empty', async () => {
    let callback: ((response: { credential?: string }) => void) | null = null;
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(JSON.stringify({
      auth_mode: 'staff_oidc',
      provider: 'google',
      google_client_id: 'google-client-id.apps.googleusercontent.com',
    }), { status: 200, headers: { 'Content-Type': 'application/json' } }));
    window.google = {
      accounts: {
        id: {
          disableAutoSelect: vi.fn(),
          initialize: vi.fn((config: GoogleInitializeConfig) => {
            callback = config.callback;
          }),
          renderButton: vi.fn(),
        },
      },
    };

    renderSignIn();

    expect(await screen.findByText('Sign in with Google to continue.')).toBeInTheDocument();
    await waitFor(() => {
      expect(callback).not.toBeNull();
    });
    const credentialCallback = callback as unknown as (response: { credential?: string }) => void;
    await act(async () => {
      credentialCallback({});
      await Promise.resolve();
    });

    expect(await screen.findByRole('alert')).toHaveTextContent('Google sign-in could not start.');
    expect(screen.queryByRole('button', { name: 'Clear Golden Rose session' })).not.toBeInTheDocument();
  });

  it('stays quiet for synthetic auth mode', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(JSON.stringify({
      auth_mode: 'synthetic',
      provider: 'synthetic',
      google_client_id: null,
    }), { status: 200, headers: { 'Content-Type': 'application/json' } }));

    const view = renderSignIn();

    await waitFor(() => {
      expect(view.container).toBeEmptyDOMElement();
    });
  });
});
