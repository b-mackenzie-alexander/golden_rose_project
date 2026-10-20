import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, useLocation } from 'react-router';
import { afterEach, vi } from 'vitest';

import { AppShell } from './AppShell';
import * as intakeApi from '../api/intakeClient';
import * as operationsApi from '../api/operationsProjectionClient';
import * as staffAccountApi from '../api/staffAccountClient';
import { bearerHeaders, clearStaffIdToken, setStaffIdToken } from '../auth/staffAuthSession';
import { LanguageProvider } from '../i18n/LanguageProvider';

vi.mock('../api/staffAccountClient');
vi.mock('../api/intakeClient');
vi.mock('../api/operationsProjectionClient');

function successfulOperationsProjection(highPriorityCount = 0) {
  return {
    ok: true as const,
    value: {
      requestItems: [], shiftItems: [], areaSummary: [],
      reportSummary: { requestCount: 0, shiftCount: 0, workerSlots: 0, pendingReviewCount: 0, activeAreaCount: 0, unmappedRequestCount: 0 },
      calendarSummary: { projectedShiftCount: 0, workerSlots: 0, pendingReviewShiftCount: 0, coverageDayCount: 0, firstShiftStartsAt: null, lastShiftEndsAt: null },
      queueSummary: { openItemCount: highPriorityCount, draftCount: highPriorityCount, pendingReviewCount: 0, highPriorityCount, oldestItemUpdatedAt: null, newestItemUpdatedAt: null },
    },
  };
}

function LocationObserver() {
  const location = useLocation();
  return <output data-testid="location-observer">{`${location.pathname}${location.search}`}</output>;
}

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
    vi.mocked(intakeApi.queryIntakes).mockResolvedValue({ ok: true, value: { items: [], next_cursor: null } });
    vi.mocked(operationsApi.getOperationsProjection).mockResolvedValue({
      ok: false,
      failure: { kind: 'unavailable' },
    });
  });

  it('shows the authorized urgent-work count and opens the urgent queue', async () => {
    const user = userEvent.setup();
    setStaffIdToken('stored-token', Date.now() + 60_000);
    vi.mocked(operationsApi.getOperationsProjection).mockResolvedValue(successfulOperationsProjection(0));
    vi.mocked(intakeApi.queryIntakes).mockImplementation((kind) => Promise.resolve({
      ok: true,
      value: {
        items: kind === 'worker'
          ? [{
              intake_id: 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa',
              kind: 'worker',
              version: 1,
              lifecycle: 'draft',
              display_name: 'Urgent worker',
              complete: false,
              missing_fields: ['worker_residence'],
              review_status: 'unreviewed',
              updated_at: '2026-10-20T12:00:00Z',
            }]
          : [],
        next_cursor: null,
      },
    }));
    render(
      <LanguageProvider>
        <MemoryRouter initialEntries={['/']}>
          <AppShell />
          <LocationObserver />
        </MemoryRouter>
      </LanguageProvider>,
    );

    const urgentButton = await screen.findByRole('button', { name: 'Open urgent work queue: 1 urgent item' });
    expect(urgentButton).toHaveTextContent('1');
    await user.click(urgentButton);
    expect(screen.getByTestId('location-observer')).toHaveTextContent('/staff/queues?filter=urgent');
  });

  it('counts urgent drafts across intake pages', async () => {
    setStaffIdToken('stored-token', Date.now() + 60_000);
    vi.mocked(operationsApi.getOperationsProjection).mockResolvedValue(successfulOperationsProjection(0));
    vi.mocked(intakeApi.queryIntakes).mockImplementation((kind, filter) => Promise.resolve({
      ok: true,
      value: {
        items: kind === 'worker'
          ? filter?.cursor === 'second-worker-page'
            ? [{
                intake_id: 'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb', kind: 'worker', version: 1, lifecycle: 'draft',
                display_name: 'Overdue worker', complete: true, missing_fields: [], review_status: 'unreviewed',
                follow_up: { owner_staff_id: 'cccccccc-cccc-4ccc-8ccc-cccccccccccc', next_follow_up_at: '2026-10-19T12:00:00Z', overdue: true }, updated_at: '2026-10-20T12:00:00Z',
              }]
            : [{
                intake_id: 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa', kind: 'worker', version: 1, lifecycle: 'draft',
                display_name: 'Incomplete worker', complete: false, missing_fields: ['worker_residence'], review_status: 'unreviewed',
                updated_at: '2026-10-20T12:00:00Z',
              }]
          : [],
        next_cursor: kind === 'worker' && filter?.cursor === undefined ? 'second-worker-page' : null,
      },
    }));
    render(
      <LanguageProvider>
        <MemoryRouter initialEntries={['/']}><AppShell /></MemoryRouter>
      </LanguageProvider>,
    );

    expect(await screen.findByRole('button', { name: 'Open urgent work queue: 2 urgent items' })).toHaveTextContent('2');
    expect(intakeApi.queryIntakes).toHaveBeenCalledWith('worker', { page_size: 50, cursor: 'second-worker-page' });
  });

  it('does not show a zero count when an urgent-work source is unavailable', async () => {
    setStaffIdToken('stored-token', Date.now() + 60_000);
    vi.mocked(operationsApi.getOperationsProjection).mockResolvedValue(successfulOperationsProjection(0));
    vi.mocked(intakeApi.queryIntakes).mockResolvedValue({ ok: false, failure: 'failed' });
    render(
      <LanguageProvider>
        <MemoryRouter initialEntries={['/']}><AppShell /></MemoryRouter>
      </LanguageProvider>,
    );

    await waitFor(() => {
      expect(intakeApi.queryIntakes).toHaveBeenCalledTimes(2);
    });
    expect(screen.getByRole('button', { name: 'Open urgent work queue' })).not.toHaveTextContent('0');
  });

  it('keeps the count unavailable when intake pagination repeats a cursor', async () => {
    setStaffIdToken('stored-token', Date.now() + 60_000);
    vi.mocked(operationsApi.getOperationsProjection).mockResolvedValue(successfulOperationsProjection(0));
    vi.mocked(intakeApi.queryIntakes).mockImplementation(() => Promise.resolve({
      ok: true,
      value: { items: [], next_cursor: 'repeated-cursor' },
    }));
    render(
      <LanguageProvider>
        <MemoryRouter initialEntries={['/']}><AppShell /></MemoryRouter>
      </LanguageProvider>,
    );

    await waitFor(() => {
      expect(intakeApi.queryIntakes).toHaveBeenCalledWith('worker', { page_size: 50, cursor: 'repeated-cursor' });
    });
    expect(screen.getByRole('button', { name: 'Open urgent work queue' })).not.toHaveTextContent('0');
  });

  it('keeps the count unavailable when the projection is unavailable', async () => {
    setStaffIdToken('stored-token', Date.now() + 60_000);
    vi.mocked(operationsApi.getOperationsProjection).mockResolvedValue({ ok: false, failure: { kind: 'unavailable' } });
    render(
      <LanguageProvider>
        <MemoryRouter initialEntries={['/']}><AppShell /></MemoryRouter>
      </LanguageProvider>,
    );

    await waitFor(() => {
      expect(intakeApi.queryIntakes).toHaveBeenCalledTimes(2);
    });
    expect(screen.getByRole('button', { name: 'Open urgent work queue' })).not.toHaveTextContent('0');
  });

  it('keeps the count unavailable when an urgent-work request rejects', async () => {
    setStaffIdToken('stored-token', Date.now() + 60_000);
    vi.mocked(operationsApi.getOperationsProjection).mockResolvedValue(successfulOperationsProjection(0));
    vi.mocked(intakeApi.queryIntakes).mockRejectedValue(new Error('network unavailable'));
    render(
      <LanguageProvider>
        <MemoryRouter initialEntries={['/']}><AppShell /></MemoryRouter>
      </LanguageProvider>,
    );

    await waitFor(() => {
      expect(intakeApi.queryIntakes).toHaveBeenCalledTimes(2);
    });
    expect(screen.getByRole('button', { name: 'Open urgent work queue' })).not.toHaveTextContent('0');
  });

  it('refreshes urgent work after the staff workspace regains focus', async () => {
    setStaffIdToken('stored-token', Date.now() + 60_000);
    vi.mocked(operationsApi.getOperationsProjection).mockResolvedValue(successfulOperationsProjection(0));
    render(
      <LanguageProvider>
        <MemoryRouter initialEntries={['/']}><AppShell /></MemoryRouter>
      </LanguageProvider>,
    );

    await waitFor(() => {
      expect(intakeApi.queryIntakes).toHaveBeenCalledTimes(2);
    });
    window.dispatchEvent(new Event('focus'));
    await waitFor(() => {
      expect(intakeApi.queryIntakes).toHaveBeenCalledTimes(4);
    });
  });

  it('does not refresh urgent work while the staff workspace is hidden', async () => {
    const visibilityDescriptor = Object.getOwnPropertyDescriptor(document, 'visibilityState');
    Object.defineProperty(document, 'visibilityState', { configurable: true, value: 'hidden' });
    try {
      setStaffIdToken('stored-token', Date.now() + 60_000);
      vi.mocked(operationsApi.getOperationsProjection).mockResolvedValue(successfulOperationsProjection(0));
      render(
        <LanguageProvider>
          <MemoryRouter initialEntries={['/']}><AppShell /></MemoryRouter>
        </LanguageProvider>,
      );

      await waitFor(() => {
        expect(intakeApi.queryIntakes).toHaveBeenCalledTimes(2);
      });
      window.dispatchEvent(new Event('focus'));
      expect(intakeApi.queryIntakes).toHaveBeenCalledTimes(2);
    } finally {
      if (visibilityDescriptor) {
        Object.defineProperty(document, 'visibilityState', visibilityDescriptor);
      }
    }
  });

  it('localizes large urgent-work counts without changing the displayed cap', async () => {
    const user = userEvent.setup();
    setStaffIdToken('stored-token', Date.now() + 60_000);
    vi.mocked(operationsApi.getOperationsProjection).mockResolvedValue(successfulOperationsProjection(100));
    render(
      <LanguageProvider>
        <MemoryRouter initialEntries={['/']}><AppShell /></MemoryRouter>
      </LanguageProvider>,
    );

    expect(await screen.findByRole('button', { name: 'Open urgent work queue: 100 urgent items' })).toHaveTextContent('99+');
    await user.click(screen.getByRole('button', { name: 'Cambiar a español' }));
    expect(await screen.findByRole('button', { name: 'Abrir cola de trabajo urgente: 100 elementos urgentes' })).toHaveTextContent('99+');
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

  it('keeps the generic account label when server session verification is denied', async () => {
    setStaffIdToken('stored-token', Date.now() + 60_000);
    vi.mocked(staffAccountApi.getStaffSession).mockResolvedValue({
      ok: false,
      failure: { kind: 'sign_in_required' },
    });

    render(
      <LanguageProvider>
        <MemoryRouter initialEntries={['/employers']}>
          <AppShell />
        </MemoryRouter>
      </LanguageProvider>,
    );

    await waitFor(() => {
      expect(staffAccountApi.getStaffSession).toHaveBeenCalledTimes(1);
    });
    expect(screen.getByRole('button', { name: 'Open my staff account' })).toHaveTextContent('Staff account');
    expect(screen.getByRole('button', { name: 'Open my staff account' })).toHaveTextContent('Verify session');
  });

  it('keeps the generic account label when session verification is unavailable', async () => {
    setStaffIdToken('stored-token', Date.now() + 60_000);
    vi.mocked(staffAccountApi.getStaffSession).mockRejectedValue(new Error('Network unavailable'));

    render(
      <LanguageProvider>
        <MemoryRouter initialEntries={['/employers']}>
          <AppShell />
        </MemoryRouter>
      </LanguageProvider>,
    );

    await waitFor(() => {
      expect(staffAccountApi.getStaffSession).toHaveBeenCalledTimes(1);
    });
    expect(screen.getByRole('button', { name: 'Open my staff account' })).toHaveTextContent('Staff account');
    expect(screen.getByRole('button', { name: 'Open my staff account' })).toHaveTextContent('Verify session');
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
