import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router';
import { afterEach, vi } from 'vitest';

import { getStaffIdentityReadiness, getStaffSession } from '../api/staffAccountClient';
import type { StaffIdentityReadiness } from '../api/staffAccountClient';
import { LanguageProvider } from '../i18n/LanguageProvider';
import { useLanguage } from '../i18n/LanguageProvider';
import { runAxe } from '../test/axe';
import { StaffAccountProfile } from './StaffAccountProfile';

vi.mock('../api/staffAccountClient', () => ({
  getStaffIdentityReadiness: vi.fn(),
  getStaffSession: vi.fn(),
}));

vi.mock('../auth/GoogleStaffSignIn', () => ({
  GoogleStaffSignIn: ({ onSignedIn }: { onSignedIn?: () => void }) => (
    <button type="button" onClick={onSignedIn}>Mock Google sign-in</button>
  ),
}));

afterEach(() => {
  vi.clearAllMocks();
});

const account = {
  staffId: '22222222-2222-4222-8222-222222222222',
  providerSubject: 'oidc:staff:123',
  providerEmail: 'mariela.torres@example.test',
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

const productionReadiness: StaffIdentityReadiness = {
  environment: 'production' as const,
  authMode: 'staff_oidc' as const,
  staffIdentityBoundary: 'production_oidc_configured' as const,
  productionStaffAuthReady: true,
  syntheticStaffRuntimeAllowed: false,
  recoveryAndSessionRevocationEvidenceOnly: true,
  requiredOperatorActions: [
    'create_staff_accounts_before_live_use',
    'confirm_mfa_claim_mapping',
    'record_recovery_and_session_revocation_provider_runbook',
  ],
};

const syntheticReadiness: StaffIdentityReadiness = {
  environment: 'local' as const,
  authMode: 'synthetic' as const,
  staffIdentityBoundary: 'synthetic_local_or_test' as const,
  productionStaffAuthReady: false,
  syntheticStaffRuntimeAllowed: true,
  recoveryAndSessionRevocationEvidenceOnly: true,
  requiredOperatorActions: [
    'use_only_for_local_or_test',
    'configure_staff_oidc_for_production',
    'create_staff_accounts_before_live_use',
  ],
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
  vi.mocked(getStaffIdentityReadiness).mockResolvedValue({ ok: true, value: productionReadiness });

  const view = renderProfile();

  expect(await screen.findByRole('heading', { name: 'Mariela Torres' })).toBeInTheDocument();
  expect(screen.getByText('Staff identity provider session')).toBeInTheDocument();
  expect(screen.getByText('Active')).toBeInTheDocument();
  expect(screen.getByText('MFA')).toBeInTheDocument();
  expect(screen.getByText('intake:read')).toBeInTheDocument();
  expect(screen.getAllByText('worker:read')).toHaveLength(2);
  expect(screen.getByText('This page reflects Golden Rose account evidence and permissions. Provider-side factor resets and session revocation remain outside this application.')).toBeInTheDocument();
  expect(screen.getByText('Production staff OIDC configured')).toBeInTheDocument();
  expect(screen.getByText('Evidence recording only')).toBeInTheDocument();
  expect(screen.getByText('Confirm MFA claim mapping before admitting live staff sessions.')).toBeInTheDocument();
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
  vi.mocked(getStaffIdentityReadiness).mockResolvedValue({ ok: true, value: syntheticReadiness });

  renderProfile();

  expect(await screen.findByText('Local synthetic session')).toBeInTheDocument();
  expect(screen.getByText('No durable account in this environment')).toBeInTheDocument();
  expect(screen.getByText('This local session is synthetic for development and testing. It is not a production personal account.')).toBeInTheDocument();
  expect(screen.getByText('Local/test synthetic staff identity')).toBeInTheDocument();
  expect(screen.getByText('Use this identity mode only for local or test work.')).toBeInTheDocument();

  await user.click(screen.getByRole('button', { name: 'Cambiar a español' }));

  expect(screen.getByRole('heading', { name: 'Mi cuenta del personal' })).toBeInTheDocument();
  expect(screen.getByText('Sesion sintetica local')).toBeInTheDocument();
  expect(screen.getByText('Sin cuenta durable en este entorno')).toBeInTheDocument();
  expect(screen.getByText('Identidad sintetica local/de prueba')).toBeInTheDocument();
});

it('surfaces recoverable staff sign-in and unavailable-account states', async () => {
  const user = userEvent.setup();
  vi.mocked(getStaffSession)
    .mockResolvedValueOnce({ ok: false, failure: { kind: 'sign_in_required' } })
    .mockResolvedValueOnce({ ok: false, failure: { kind: 'account_unavailable' } });
  vi.mocked(getStaffIdentityReadiness)
    .mockResolvedValueOnce({ ok: false, failure: { kind: 'sign_in_required' } })
    .mockResolvedValueOnce({ ok: false, failure: { kind: 'account_unavailable' } });

  renderProfile();

  expect(await screen.findByRole('alert')).toHaveTextContent('Sign in with the configured staff identity provider to continue.');
  expect(screen.getByRole('button', { name: 'Mock Google sign-in' })).toBeInTheDocument();

  await user.click(screen.getByRole('button', { name: 'Reload status' }));

  expect(await screen.findByRole('alert')).toHaveTextContent('Your staff account is suspended, deprovisioned, or otherwise unavailable.');
  expect(getStaffSession).toHaveBeenCalledTimes(2);
  expect(getStaffIdentityReadiness).toHaveBeenCalledTimes(2);
});

it('surfaces recoverable operator readiness loading failures without hiding the account', async () => {
  const user = userEvent.setup();
  vi.mocked(getStaffSession).mockResolvedValue({
    ok: true,
    value: {
      actorId: account.staffId,
      roleName: 'operations_staff',
      permissionNames: ['intake:read'],
      authContext: 'staff_oidc',
      account,
      delegations: [],
    },
  });
  vi.mocked(getStaffIdentityReadiness)
    .mockResolvedValueOnce({ ok: false, failure: { kind: 'unavailable' } })
    .mockResolvedValueOnce({ ok: true, value: productionReadiness });

  renderProfile();

  expect(await screen.findByRole('heading', { name: 'Mariela Torres' })).toBeInTheDocument();
  expect(screen.getByRole('alert')).toHaveTextContent('Readiness could not be loaded: The account service is unavailable.');

  await user.click(screen.getByRole('button', { name: 'Reload status' }));

  expect(await screen.findByText('Production staff OIDC configured')).toBeInTheDocument();
  expect(screen.queryByText(/Readiness could not be loaded/)).not.toBeInTheDocument();
});
