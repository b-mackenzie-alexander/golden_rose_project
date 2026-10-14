import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router';
import { afterEach, vi } from 'vitest';

import { AppShell } from './AppShell';
import * as staffAccountApi from '../api/staffAccountClient';
import { bearerHeaders, clearStaffIdToken, setStaffIdToken } from '../auth/staffAuthSession';
import { LanguageProvider } from '../i18n/LanguageProvider';

vi.mock('../api/staffAccountClient');

afterEach(() => {
  clearStaffIdToken();
  vi.restoreAllMocks();
  window.google = undefined;
});

describe('AppShell', () => {
  beforeEach(() => {
    window.localStorage.clear();
    document.documentElement.removeAttribute('data-theme');
    clearStaffIdToken();
    vi.mocked(staffAccountApi.getStaffSession).mockResolvedValue({
      ok: false,
      failure: { kind: 'sign_in_required' },
    });
  });

  it('renders the dashboard shell navigation and language action', () => {
    render(
      <LanguageProvider>
        <MemoryRouter initialEntries={['/employers']}>
          <AppShell />
        </MemoryRouter>
      </LanguageProvider>,
    );

    const banner = screen.getByRole('banner');
    expect(banner).toHaveClass('app-header');
    expect(within(banner).getByRole('button', { name: 'Cambiar a español' })).toHaveClass('language-action');
    expect(screen.getByRole('heading', { name: 'Nuestro Corazón Dorado' })).toHaveClass('app-brand');
    expect(screen.getByRole('navigation', { name: 'Primary' })).toHaveClass('primary-navigation');
    expect(screen.getByRole('link', { name: 'Employers' })).toHaveClass('nav-link');
    const accountGroup = document.querySelector('.nav-account-group');
    expect(accountGroup).toContainElement(screen.getByRole('link', { name: 'My account' }));
    expect(accountGroup).toContainElement(screen.getByRole('link', { name: 'Staff accounts' }));
    expect(accountGroup).not.toContainElement(screen.getByRole('link', { name: 'Map' }));
    expect(screen.getByRole('main')).toHaveClass('app-main');
  });

  it('renders the staff workspace landmarks', () => {
    render(
      <MemoryRouter initialEntries={['/employers']}>
        <AppShell />
      </MemoryRouter>,
    );

    expect(screen.getByRole('banner')).toBeInTheDocument();
    expect(screen.getByRole('navigation', { name: 'Primary' })).toBeInTheDocument();
    expect(screen.getByRole('main')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Employers' })).toHaveAttribute('aria-current', 'page');
  });

  it('does not hardcode a named staff identity before session verification', () => {
    render(
      <LanguageProvider>
        <MemoryRouter initialEntries={['/employers']}>
          <AppShell />
        </MemoryRouter>
      </LanguageProvider>,
    );

    const accountButton = screen.getByRole('button', { name: 'Open my staff account' });
    expect(accountButton).toHaveTextContent('Staff account');
    expect(accountButton).toHaveTextContent('Verify session');
    expect(accountButton).not.toHaveTextContent('Mariela Torres');
    expect(accountButton).not.toHaveTextContent('Operations team');
    expect(screen.queryByRole('button', { name: 'Sign out of Golden Rose session' })).not.toBeInTheDocument();
  });

  it('shows the signed-in staff account name after session verification', async () => {
    setStaffIdToken('stored-token', Date.now() + 60_000);
    vi.mocked(staffAccountApi.getStaffSession).mockResolvedValue({
      ok: true,
      value: {
        actorId: 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa',
        roleName: 'owner',
        permissionNames: ['staff_account:read'],
        authContext: 'staff_oidc',
        account: {
          staffId: 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa',
          providerSubject: 'oidc:staff:owner',
          providerEmail: 'owner@example.test',
          displayName: 'Beatrice Santos',
          roleName: 'owner',
          lifecycleStatus: 'active',
          mfaEnrolled: true,
          permissionNames: ['staff_account:read'],
          createdAt: '2026-10-06T12:00:00Z',
          createdBy: 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa',
          updatedAt: '2026-10-06T12:00:00Z',
          updatedBy: 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa',
          version: 1,
        },
        delegations: [],
      },
    });

    render(
      <LanguageProvider>
        <MemoryRouter initialEntries={['/employers']}>
          <AppShell />
        </MemoryRouter>
      </LanguageProvider>,
    );

    const accountButton = screen.getByRole('button', { name: 'Open my staff account' });
    await waitFor(() => {
      expect(accountButton).toHaveTextContent('Beatrice Santos');
    });
    expect(accountButton).toHaveTextContent('Signed in');
    expect(accountButton).not.toHaveTextContent('Staff account');
  });

  it('clears the Golden Rose staff browser session from the header', async () => {
    const user = userEvent.setup();
    const disableAutoSelect = vi.fn();
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

    render(
      <LanguageProvider>
        <MemoryRouter initialEntries={['/staff/map']}>
          <AppShell />
        </MemoryRouter>
      </LanguageProvider>,
    );

    expect(bearerHeaders(undefined).get('Authorization')).toBe('Bearer stored-token');

    await user.click(screen.getByRole('button', { name: 'Sign out of Golden Rose session' }));

    await waitFor(() => {
      expect(disableAutoSelect).toHaveBeenCalledTimes(1);
      expect(screen.queryByRole('button', { name: 'Sign out of Golden Rose session' })).not.toBeInTheDocument();
      expect(bearerHeaders(undefined).has('Authorization')).toBe(false);
    });
  });

  it('clears the staff browser session with Spanish labels when Google auto-select is unavailable', async () => {
    const user = userEvent.setup();
    setStaffIdToken('stored-token', Date.now() + 60_000);

    render(
      <LanguageProvider>
        <MemoryRouter initialEntries={['/staff/account']}>
          <AppShell />
        </MemoryRouter>
      </LanguageProvider>,
    );

    await user.click(screen.getByRole('button', { name: 'Cambiar a español' }));

    const signOut = screen.getByRole('button', { name: 'Cerrar sesion de Golden Rose' });
    expect(signOut).toHaveTextContent('Cerrar sesion');
    expect(signOut).toHaveAttribute(
      'title',
      'Borra esta sesion de Golden Rose en el navegador. Google puede seguir activo.',
    );
    expect(bearerHeaders(undefined).get('Authorization')).toBe('Bearer stored-token');

    await user.click(signOut);

    await waitFor(() => {
      expect(screen.queryByRole('button', { name: 'Cerrar sesion de Golden Rose' })).not.toBeInTheDocument();
      expect(bearerHeaders(undefined).has('Authorization')).toBe(false);
    });
  });

  it('persists light and dark mode from the utility toggle', async () => {
    const user = userEvent.setup();
    render(
      <LanguageProvider>
        <MemoryRouter initialEntries={['/employers']}>
          <AppShell />
        </MemoryRouter>
      </LanguageProvider>,
    );

    await user.click(screen.getByRole('button', { name: 'Switch to dark mode' }));

    expect(document.documentElement.dataset.theme).toBe('dark');
    expect(window.localStorage.getItem('golden-rose-theme')).toBe('dark');
    expect(screen.getByRole('button', { name: 'Switch to light mode' })).toHaveAttribute('aria-pressed', 'true');

    await user.click(screen.getByRole('button', { name: 'Switch to light mode' }));

    expect(document.documentElement.dataset.theme).toBe('light');
    expect(window.localStorage.getItem('golden-rose-theme')).toBe('light');
  });
});
