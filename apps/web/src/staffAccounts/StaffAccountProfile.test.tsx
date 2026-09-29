import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router';
import { afterEach, vi } from 'vitest';

import { getStaffSession } from '../api/staffAccountClient';
import { LanguageProvider } from '../i18n/LanguageProvider';
import { useLanguage } from '../i18n/LanguageProvider';
import { runAxe } from '../test/axe';
import { StaffAccountProfile } from './StaffAccountProfile';

vi.mock('../api/staffAccountClient', () => ({
  getStaffSession: vi.fn(),
}));

afterEach(() => {
  vi.clearAllMocks();
});

const account = {
  staffId: '22222222-2222-4222-8222-222222222222',
  providerSubject: 'oidc:staff:123',
  displayName: 'Mariela Torres',
  roleName: 'operations_staff' as const,
  lifecycleStatus: 'active' as const,
  mfaEnrolled: true,
  createdAt: '2026-09-28T12:00:00Z',
  createdBy: '11111111-1111-4111-8111-111111111111',
  updatedAt: '2026-09-28T12:30:00Z',
  updatedBy: '11111111-1111-4111-8111-111111111111',
  version: 2,
};

const delegation = {
  delegationId: '44444444-4444-4444-8444-444444444444',
  grantorStaffId: '11111111-1111-4111-8111-111111111111',
  granteeStaffId: account.staffId,
  permissionName: 'worker:read',
  scopeKind: 'global' as const,
  scopeId: null,
  reasonText: 'Temporary coverage',
  startsAt: '2026-09-28T12:00:00Z',
  expiresAt: '2026-10-28T12:00:00Z',
  revokedAt: null,
  revokedBy: null,
  revocationReason: null,
};

function renderProfile() {
  function Harness() {
    const { messages, toggleLanguage } = useLanguage();
    return (
      <>
        <button type="button" onClick={toggleLanguage}>{messages.switchLanguage}</button>
        <StaffAccountProfile />
      </>
    );
  }
  return render(
    <LanguageProvider>
      <MemoryRouter>
        <Harness />
      </MemoryRouter>
    </LanguageProvider>,
  );
}

it('shows the current staff account, MFA evidence, permissions, and active delegations', async () => {
  vi.mocked(getStaffSession).mockResolvedValue({
    ok: true,
    value: {
      actorId: account.staffId,
      roleName: 'operations_staff',
      permissionNames: ['intake:read', 'worker:read'],
      authContext: 'staff_oidc',
      account,
      delegations: [delegation],
    },
  });

  const view = renderProfile();

  expect(await screen.findByRole('heading', { name: 'Mariela Torres' })).toBeInTheDocument();
  expect(screen.getByText('Staff identity provider session')).toBeInTheDocument();
  expect(screen.getByText('Active')).toBeInTheDocument();
  expect(screen.getByText('MFA')).toBeInTheDocument();
  expect(screen.getByText('intake:read')).toBeInTheDocument();
  expect(screen.getAllByText('worker:read')).toHaveLength(2);
  expect(screen.getByText('This page reflects Golden Rose account evidence and permissions. Provider-side factor resets and session revocation remain outside this application.')).toBeInTheDocument();
  expect(screen.getByRole('link', { name: 'Open account administration' })).toHaveAttribute('href', '/staff/admin/accounts');
  expect(await runAxe(view.container)).toEqual([]);
});

it('shows a truthful local synthetic session without inventing a durable account', async () => {
  const user = userEvent.setup();
  vi.mocked(getStaffSession).mockResolvedValue({
    ok: true,
    value: {
      actorId: '11111111-1111-4111-8111-111111111111',
      roleName: 'synthetic_staff',
      permissionNames: ['intake:read'],
      authContext: 'synthetic',
      account: null,
      delegations: [],
    },
  });

  renderProfile();

  expect(await screen.findByText('Local synthetic session')).toBeInTheDocument();
  expect(screen.getByText('No durable account in this environment')).toBeInTheDocument();
  expect(screen.getByText('This local session is synthetic for development and testing. It is not a production personal account.')).toBeInTheDocument();

  await user.click(screen.getByRole('button', { name: 'Cambiar a español' }));

  expect(screen.getByRole('heading', { name: 'Mi cuenta del personal' })).toBeInTheDocument();
  expect(screen.getByText('Sesion sintetica local')).toBeInTheDocument();
  expect(screen.getByText('Sin cuenta durable en este entorno')).toBeInTheDocument();
});

it('surfaces recoverable staff sign-in and unavailable-account states', async () => {
  const user = userEvent.setup();
  vi.mocked(getStaffSession)
    .mockResolvedValueOnce({ ok: false, failure: { kind: 'sign_in_required' } })
    .mockResolvedValueOnce({ ok: false, failure: { kind: 'account_unavailable' } });

  renderProfile();

  expect(await screen.findByRole('alert')).toHaveTextContent('Sign in with the configured staff identity provider to continue.');

  await user.click(screen.getByRole('button', { name: 'Reload status' }));

  expect(await screen.findByRole('alert')).toHaveTextContent('Your staff account is suspended, deprovisioned, or otherwise unavailable.');
  expect(getStaffSession).toHaveBeenCalledTimes(2);
});
