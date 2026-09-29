import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router';
import { afterEach, beforeEach, expect, it, vi } from 'vitest';

import {
  activateStaffAccount,
  createStaffAccount,
  grantStaffDelegation,
  listStaffAccounts,
  listStaffAccountEvents,
  listStaffDelegations,
  recordRecoveryEvidence,
  recordSessionRevocationEvidence,
  revokeStaffDelegation,
  suspendStaffAccount,
} from '../api/staffAccountClient';
import type { StaffAccount, StaffAccountLifecycleEvent, StaffDelegation } from '../api/staffAccountClient';
import { LanguageProvider } from '../i18n/LanguageProvider';
import { runAxe } from '../test/axe';
import { AppRoutes } from '../app/App';
import { StaffAccountAdmin } from './StaffAccountAdmin';

vi.mock('../api/intakeClient', () => ({
  queryIntakes: vi.fn().mockResolvedValue({ ok: true, value: { items: [], next_cursor: null } }),
}));

vi.mock('../api/staffAccountClient', () => ({
  activateStaffAccount: vi.fn(),
  createStaffAccount: vi.fn(),
  deprovisionStaffAccount: vi.fn(),
  grantStaffDelegation: vi.fn(),
  listStaffAccountEvents: vi.fn(),
  listStaffAccounts: vi.fn(),
  listStaffDelegations: vi.fn(),
  recordRecoveryEvidence: vi.fn(),
  recordSessionRevocationEvidence: vi.fn(),
  revokeStaffDelegation: vi.fn(),
  suspendStaffAccount: vi.fn(),
}));

const suspended: StaffAccount = {
  staffId: '22222222-2222-4222-8222-222222222222',
  providerSubject: 'oidc:staff:123',
  displayName: 'Mariela Torres',
  roleName: 'operations_staff',
  lifecycleStatus: 'suspended',
  mfaEnrolled: false,
  createdAt: '2026-09-28T12:00:00Z',
  createdBy: '11111111-1111-4111-8111-111111111111',
  updatedAt: '2026-09-28T12:00:00Z',
  updatedBy: '11111111-1111-4111-8111-111111111111',
  version: 1,
};

const active: StaffAccount = {
  ...suspended,
  lifecycleStatus: 'active',
  mfaEnrolled: true,
  updatedAt: '2026-09-28T12:15:00Z',
  version: 2,
};

const delegation: StaffDelegation = {
  delegationId: '44444444-4444-4444-8444-444444444444',
  grantorStaffId: '11111111-1111-4111-8111-111111111111',
  granteeStaffId: suspended.staffId,
  permissionName: 'intake:read',
  scopeKind: 'global',
  scopeId: null,
  reasonText: 'Temporary coverage',
  startsAt: '2026-09-28T12:00:00Z',
  expiresAt: '2026-09-29T12:00:00Z',
  revokedAt: null,
  revokedBy: null,
  revocationReason: null,
};

const lifecycleEvent: StaffAccountLifecycleEvent = {
  eventId: '55555555-5555-4555-8555-555555555555',
  commandId: 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa',
  staffId: suspended.staffId,
  actorId: '11111111-1111-4111-8111-111111111111',
  eventType: 'staff_account.recovery_recorded',
  previousStatus: 'active',
  newStatus: 'active',
  previousVersion: 2,
  newVersion: 2,
  occurredAt: '2026-09-28T12:30:00Z',
  reasonText: 'Provider ticket reviewed; evidence recorded only',
};

beforeEach(() => {
  vi.mocked(listStaffAccounts).mockResolvedValue({ ok: true, value: [suspended] });
  vi.mocked(createStaffAccount).mockReset();
  vi.mocked(activateStaffAccount).mockReset();
  vi.mocked(recordRecoveryEvidence).mockReset();
  vi.mocked(recordSessionRevocationEvidence).mockReset();
  vi.mocked(listStaffAccountEvents).mockResolvedValue({ ok: true, value: [lifecycleEvent] });
  vi.mocked(listStaffDelegations).mockResolvedValue({ ok: true, value: [delegation] });
  vi.mocked(grantStaffDelegation).mockReset();
  vi.mocked(revokeStaffDelegation).mockReset();
  vi.mocked(suspendStaffAccount).mockReset();
  vi.spyOn(globalThis.crypto, 'randomUUID').mockReturnValue('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa');
});

afterEach(() => {
  vi.restoreAllMocks();
});

function lastElement<T>(items: T[]): T {
  const item = items.at(-1);
  if (item === undefined) {
    throw new Error('Expected at least one element.');
  }
  return item;
}

it('creates a suspended onboarding account and shows field-local validation', async () => {
  const user = userEvent.setup();
  const created = { ...suspended, staffId: '33333333-3333-4333-8333-333333333333', displayName: 'Sofia Diaz', providerSubject: 'oidc:staff:456' };
  vi.mocked(createStaffAccount).mockResolvedValue({ ok: true, value: { account: created, eventType: 'staff_account.created', resultVersion: 1 } });

  render(<LanguageProvider><StaffAccountAdmin /></LanguageProvider>);
  await screen.findByText('Mariela Torres');

  await user.click(screen.getByRole('button', { name: 'Create staff account' }));
  expect(screen.getByText('Display name is required.')).toBeInTheDocument();
  expect(screen.getByText('Provider subject is required.')).toBeInTheDocument();

  await user.type(screen.getByRole('textbox', { name: /Display name/ }), 'Sofia Diaz');
  await user.type(screen.getByRole('textbox', { name: /Provider subject/ }), 'oidc:staff:456');
  await user.type(screen.getByRole('textbox', { name: /Reason/ }), 'Initial onboarding approved');
  await user.click(screen.getByLabelText('staff_account:create'));
  await user.click(screen.getByRole('button', { name: 'Create staff account' }));

  const createCall = vi.mocked(createStaffAccount).mock.calls[0]?.[0];
  expect(createCall?.displayName).toBe('Sofia Diaz');
  expect(createCall?.providerSubject).toBe('oidc:staff:456');
  expect(createCall?.permissionNames).toEqual(expect.arrayContaining(['staff_account:read', 'staff_account:create']));
  expect(createCall?.reasonText).toBe('Initial onboarding approved');
  expect(await screen.findByText('Staff account created in suspended onboarding state.')).toBeInTheDocument();
  expect(screen.getByText('Sofia Diaz')).toBeInTheDocument();
});

it('filters staff accounts by lifecycle, MFA readiness, and search text', async () => {
  const user = userEvent.setup();
  const activeStaff: StaffAccount = {
    ...active,
    staffId: '33333333-3333-4333-8333-333333333333',
    displayName: 'Sofia Diaz',
    providerSubject: 'oidc:staff:456',
  };
  const deprovisioned: StaffAccount = {
    ...suspended,
    staffId: '55555555-5555-4555-8555-555555555555',
    displayName: 'Elena Ruiz',
    providerSubject: 'oidc:staff:789',
    lifecycleStatus: 'deprovisioned',
    version: 3,
  };
  vi.mocked(listStaffAccounts).mockResolvedValue({ ok: true, value: [suspended, activeStaff, deprovisioned] });

  render(<LanguageProvider><StaffAccountAdmin /></LanguageProvider>);
  await screen.findByText('Mariela Torres');
  expect(screen.getByText('Sofia Diaz')).toBeInTheDocument();
  expect(screen.getByText('Elena Ruiz')).toBeInTheDocument();

  await user.selectOptions(screen.getByLabelText('Lifecycle filter'), 'active');
  expect(screen.queryByText('Mariela Torres')).not.toBeInTheDocument();
  expect(screen.getByText('Sofia Diaz')).toBeInTheDocument();

  await user.selectOptions(screen.getByLabelText('Lifecycle filter'), 'mfa_pending');
  expect(screen.getByText('Mariela Torres')).toBeInTheDocument();
  expect(screen.queryByText('Sofia Diaz')).not.toBeInTheDocument();
  expect(screen.queryByText('Elena Ruiz')).not.toBeInTheDocument();

  await user.type(screen.getByRole('textbox', { name: 'Find account' }), 'missing');
  expect(screen.getByText('No accounts match this filter.')).toBeInTheDocument();
});

it('opens lifecycle evidence history without claiming provider-side execution', async () => {
  const user = userEvent.setup();

  render(<LanguageProvider><StaffAccountAdmin /></LanguageProvider>);
  await screen.findByText('Mariela Torres');

  await user.click(screen.getByRole('button', { name: 'History' }));

  expect(await screen.findByRole('heading', { name: 'Account history: Mariela Torres' })).toBeInTheDocument();
  expect(listStaffAccountEvents).toHaveBeenCalledWith(suspended.staffId);
  expect(screen.getByText('Recovery evidence recorded')).toBeInTheDocument();
  expect(screen.getByText('Provider ticket reviewed; evidence recorded only')).toBeInTheDocument();
  expect(screen.getByText(/Recovery and session entries do not confirm provider-side reset or revocation/)).toBeInTheDocument();
});

it('shows recoverable history errors and empty lifecycle evidence', async () => {
  const user = userEvent.setup();
  vi.mocked(listStaffAccountEvents)
    .mockResolvedValueOnce({ ok: false, failure: { kind: 'not_found' } })
    .mockResolvedValueOnce({ ok: true, value: [] });

  render(<LanguageProvider><StaffAccountAdmin /></LanguageProvider>);
  await screen.findByText('Mariela Torres');

  await user.click(screen.getByRole('button', { name: 'History' }));
  expect(await screen.findByText('The account is no longer available. Reload the list.')).toBeInTheDocument();
  await user.click(screen.getByRole('button', { name: 'Close' }));
  await user.click(screen.getByRole('button', { name: 'History' }));

  expect(await screen.findByText('No lifecycle evidence has been recorded for this account.')).toBeInTheDocument();
});

it('activates with MFA evidence and records recovery evidence without provider-side claims', async () => {
  const user = userEvent.setup();
  vi.mocked(activateStaffAccount).mockResolvedValue({ ok: true, value: { account: active, eventType: 'staff_account.activated', resultVersion: 2 } });
  vi.mocked(recordRecoveryEvidence).mockResolvedValue({ ok: true, value: { account: active, eventType: 'staff_account.recovery_recorded', resultVersion: 2 } });

  render(<LanguageProvider><StaffAccountAdmin /></LanguageProvider>);
  await screen.findByText('Mariela Torres');

  await user.click(screen.getByRole('button', { name: 'Activate' }));
  expect(screen.getByText('Activation requires confirmed MFA enrollment.')).toBeInTheDocument();
  await user.type(lastElement(screen.getAllByLabelText('Reason')), 'MFA confirmed in provider console');
  await user.click(lastElement(screen.getAllByRole('button', { name: 'Activate' })));

  expect(activateStaffAccount).toHaveBeenCalledWith(expect.objectContaining({
    expectedVersion: 1,
    mfaEnrolled: true,
    staffId: suspended.staffId,
  }));
  expect((await screen.findAllByText('Active')).length).toBeGreaterThan(0);

  await user.click(screen.getByRole('button', { name: 'Recovery evidence' }));
  expect(screen.getByText('Evidence only. Identity-provider factor reset stays outside this application.')).toBeInTheDocument();
  await user.type(lastElement(screen.getAllByLabelText('Reason')), 'Recovery call completed');
  await user.click(screen.getByRole('button', { name: 'Record recovery evidence' }));

  expect(recordRecoveryEvidence).toHaveBeenCalledWith(expect.objectContaining({
    expectedVersion: 2,
    reasonText: 'Recovery call completed',
    staffId: suspended.staffId,
  }));
});

it('shows recoverable list, create, and action errors', async () => {
  const user = userEvent.setup();
  vi.mocked(listStaffAccounts).mockResolvedValueOnce({ ok: false, failure: { kind: 'forbidden' } }).mockResolvedValue({ ok: true, value: [active] });
  vi.mocked(createStaffAccount).mockResolvedValue({ ok: false, failure: { kind: 'forbidden' } });
  vi.mocked(suspendStaffAccount).mockResolvedValue({ ok: false, failure: { kind: 'stale' } });
  vi.mocked(recordSessionRevocationEvidence).mockResolvedValue({ ok: false, failure: { kind: 'unknown_outcome' } });

  render(<LanguageProvider><StaffAccountAdmin /></LanguageProvider>);

  expect(await screen.findByText('This staff session does not have permission for that account action.')).toBeInTheDocument();
  await user.click(screen.getByRole('button', { name: 'Reload accounts' }));
  expect((await screen.findAllByText('Active')).length).toBeGreaterThan(0);

  await user.type(screen.getByRole('textbox', { name: 'Display name' }), 'Denied Staff');
  await user.type(screen.getByRole('textbox', { name: 'Provider subject' }), 'oidc:staff:789');
  await user.type(screen.getByRole('textbox', { name: 'Reason' }), 'Try denied create');
  await user.click(screen.getByRole('button', { name: 'Create staff account' }));
  expect(await screen.findByText('This staff session does not have permission for that account action.')).toBeInTheDocument();

  await user.click(screen.getByRole('button', { name: 'Suspend' }));
  await user.click(lastElement(screen.getAllByRole('button', { name: 'Suspend' })));
  expect(screen.getByText('Reason is required.')).toBeInTheDocument();
  await user.type(lastElement(screen.getAllByLabelText('Reason')), 'Access review changed elsewhere');
  await user.click(lastElement(screen.getAllByRole('button', { name: 'Suspend' })));
  expect(await screen.findByText('The account changed in another session. Reload before trying again.')).toBeInTheDocument();

  await user.click(screen.getByRole('button', { name: 'Close' }));
  await user.click(screen.getByRole('button', { name: 'Session evidence' }));
  expect(screen.getByText('Evidence only. This does not confirm provider-side session revocation.')).toBeInTheDocument();
  await user.type(lastElement(screen.getAllByLabelText('Reason')), 'Provider console review pending');
  await user.click(screen.getByRole('button', { name: 'Record session revocation evidence' }));
  expect(await screen.findByText('The outcome is unknown. Retry the original account request before changing the form.')).toBeInTheDocument();
});

it('opens a deprovision action for active accounts', async () => {
  const user = userEvent.setup();
  render(<LanguageProvider><StaffAccountAdmin /></LanguageProvider>);
  await screen.findByText('Mariela Torres');

  await user.click(screen.getByRole('button', { name: 'Deprovision' }));

  expect(screen.getByRole('heading', { name: 'Deprovision: Mariela Torres' })).toBeInTheDocument();
});

it('lists, grants, and revokes account delegations', async () => {
  const user = userEvent.setup();
  const revoked = {
    ...delegation,
    revokedAt: '2026-09-28T13:00:00Z',
    revokedBy: delegation.grantorStaffId,
    revocationReason: 'Coverage ended',
  };
  vi.mocked(grantStaffDelegation).mockResolvedValue({ ok: true, value: { delegation, eventType: 'staff_delegation.granted', resultVersion: 1 } });
  vi.mocked(revokeStaffDelegation).mockResolvedValue({ ok: true, value: { delegation: revoked, eventType: 'staff_delegation.revoked', resultVersion: 1 } });

  render(<LanguageProvider><StaffAccountAdmin /></LanguageProvider>);
  await screen.findByText('Mariela Torres');

  await user.click(screen.getByRole('button', { name: 'Delegations' }));
  expect(await screen.findByRole('heading', { name: 'Delegations: Mariela Torres' })).toBeInTheDocument();
  expect(screen.getAllByText('intake:read').length).toBeGreaterThan(0);
  await user.selectOptions(screen.getByLabelText('Permission'), 'worker:read');
  await user.clear(lastElement(screen.getAllByLabelText('Reason')));
  await user.type(lastElement(screen.getAllByLabelText('Reason')), 'Temporary worker coverage');
  await user.click(screen.getByRole('button', { name: 'Grant delegation' }));

  expect(grantStaffDelegation).toHaveBeenCalledWith(expect.objectContaining({
    staffId: suspended.staffId,
    permissionName: 'worker:read',
    reasonText: 'Temporary worker coverage',
  }));
  expect(await screen.findByText('Delegation recorded.')).toBeInTheDocument();

  await user.type(screen.getByLabelText('Revocation reason'), 'Coverage ended');
  await user.click(screen.getByRole('button', { name: 'Revoke' }));

  expect(revokeStaffDelegation).toHaveBeenCalledWith(expect.objectContaining({
    staffId: suspended.staffId,
    delegationId: delegation.delegationId,
    reasonText: 'Coverage ended',
  }));
  expect(await screen.findByText('Delegation revoked.')).toBeInTheDocument();
  expect(screen.getByText('Coverage ended')).toBeInTheDocument();
});

it('shows recoverable delegation list and form errors', async () => {
  const user = userEvent.setup();
  vi.mocked(listStaffDelegations)
    .mockResolvedValueOnce({ ok: false, failure: { kind: 'forbidden' } })
    .mockResolvedValueOnce({ ok: true, value: [] });
  vi.mocked(grantStaffDelegation).mockResolvedValue({ ok: false, failure: { kind: 'validation' } });

  render(<LanguageProvider><StaffAccountAdmin /></LanguageProvider>);
  await screen.findByText('Mariela Torres');

  await user.click(screen.getByRole('button', { name: 'Delegations' }));
  expect(await screen.findByText('This staff session does not have permission for that account action.')).toBeInTheDocument();
  await user.click(screen.getByRole('button', { name: 'Close' }));
  await user.click(screen.getByRole('button', { name: 'Delegations' }));
  expect(await screen.findByText('No delegations recorded for this account.')).toBeInTheDocument();

  await user.click(screen.getByRole('button', { name: 'Grant delegation' }));
  expect(screen.getByText('Permission, expiration and reason are required.')).toBeInTheDocument();

  await user.type(lastElement(screen.getAllByLabelText('Reason')), 'Temporary coverage');
  await user.click(screen.getByRole('button', { name: 'Grant delegation' }));
  expect(await screen.findByText('Check the highlighted account fields and try again.')).toBeInTheDocument();
});

it('blocks expired delegation grants before submitting to the API', async () => {
  const user = userEvent.setup();

  render(<LanguageProvider><StaffAccountAdmin /></LanguageProvider>);
  await screen.findByText('Mariela Torres');

  await user.click(screen.getByRole('button', { name: 'Delegations' }));
  await screen.findByRole('heading', { name: 'Delegations: Mariela Torres' });
  await user.clear(screen.getByLabelText('Expires'));
  await user.type(screen.getByLabelText('Expires'), '2000-01-01T00:00');
  await user.type(lastElement(screen.getAllByLabelText('Reason')), 'Temporary coverage');
  await user.click(screen.getByRole('button', { name: 'Grant delegation' }));

  expect(screen.getByText('Expiration must be a future date and time.')).toBeInTheDocument();
  expect(grantStaffDelegation).not.toHaveBeenCalled();
});

it('renders Spanish account administration and has no automated axe violations', async () => {
  const user = userEvent.setup();
  const view = render(
    <LanguageProvider>
      <MemoryRouter initialEntries={['/staff/admin/accounts']}>
        <AppRoutes />
      </MemoryRouter>
    </LanguageProvider>,
  );
  await screen.findByText('Mariela Torres');

  expect(await runAxe(view.container)).toEqual([]);

  await user.click(screen.getByRole('button', { name: 'Cambiar a español' }));

  expect(screen.getByRole('heading', { name: 'Cuentas del personal' })).toBeInTheDocument();
  expect(screen.getByRole('button', { name: 'Crear cuenta' })).toBeInTheDocument();
  expect(await runAxe(view.container)).toEqual([]);
});
