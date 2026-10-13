import { fireEvent, render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router';
import { afterEach, beforeEach, expect, it, vi } from 'vitest';

import {
  activateStaffAccount,
  correctStaffAccount,
  createStaffAccount,
  grantStaffDelegation,
  listStaffAccounts,
  listStaffAccountEvents,
  listStaffDelegations,
  recordRecoveryEvidence,
  recordSessionRevocationEvidence,
  revokeStaffDelegation,
  suspendStaffAccount,
  updateStaffAccountGoogleEmail,
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
  correctStaffAccount: vi.fn(),
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
  updateStaffAccountGoogleEmail: vi.fn(),
}));

vi.mock('../auth/GoogleStaffSignIn', () => ({
  GoogleStaffSignIn: ({ onSignedIn }: { onSignedIn?: () => void }) => (
    <button type="button" onClick={onSignedIn}>Mock Google sign-in</button>
  ),
}));

const suspended: StaffAccount = {
  staffId: '22222222-2222-4222-8222-222222222222',
  providerSubject: 'oidc:staff:123',
  providerEmail: 'mariela.torres@example.test',
  displayName: 'Mariela Torres',
  roleName: 'operations_staff',
  lifecycleStatus: 'suspended',
  mfaEnrolled: false,
  permissionNames: ['staff_account:read'],
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

const createdLifecycleEvent: StaffAccountLifecycleEvent = {
  ...lifecycleEvent,
  eventId: '66666666-6666-4666-8666-666666666666',
  eventType: 'staff_account.created',
  previousStatus: null,
  newStatus: 'suspended',
  previousVersion: null,
  newVersion: 1,
  reasonText: 'Initial onboarding recorded',
};

const activatedLifecycleEvent: StaffAccountLifecycleEvent = {
  ...lifecycleEvent,
  eventId: '77777777-7777-4777-8777-777777777777',
  eventType: 'staff_account.activated',
  previousStatus: 'suspended',
  newStatus: 'active',
  previousVersion: 1,
  newVersion: 2,
  reasonText: 'MFA evidence confirmed before activation',
};

beforeEach(() => {
  vi.mocked(listStaffAccounts).mockResolvedValue({ ok: true, value: [suspended] });
  vi.mocked(createStaffAccount).mockReset();
  vi.mocked(correctStaffAccount).mockReset();
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
  const created = {
    ...suspended,
    staffId: '33333333-3333-4333-8333-333333333333',
    displayName: 'Sofia Diaz',
    providerSubject: 'pending-google-email:abc123',
    providerEmail: 'sofia.diaz@example.test',
  };
  vi.mocked(createStaffAccount).mockResolvedValue({ ok: true, value: { account: created, eventType: 'staff_account.created', resultVersion: 1 } });

  render(<LanguageProvider><StaffAccountAdmin /></LanguageProvider>);
  await screen.findByText('Mariela Torres');
  expect(screen.getByText('Google sign-in binding recorded')).toBeInTheDocument();
  expect(screen.queryByText('oidc:staff:123')).not.toBeInTheDocument();
  expect(screen.getByText('1 named permissions')).toBeInTheDocument();
  expect(screen.getByText('Residential intake: missing')).toBeInTheDocument();
  expect(screen.getAllByText('Staff Accounts: Read').length).toBeGreaterThan(0);

  await user.click(screen.getByRole('button', { name: 'Create staff account' }));
  expect(screen.getByText('Display name is required.')).toBeInTheDocument();
  expect(screen.getByText('Google email or provider subject is required.')).toBeInTheDocument();

  const createPanel = screen.getByRole('heading', { name: /Onboard staff account/ }).closest('section');
  expect(createPanel).not.toBeNull();
  const createForm = within(createPanel as HTMLElement);
  const createFormElement = createPanel?.querySelector('form');
  expect(createFormElement).not.toBeNull();
  await user.type(createForm.getByRole('textbox', { name: /Display name/ }), 'Sofia Diaz');
  const googleEmailInput = createForm.getAllByRole('textbox', { name: /Google email/ })[0];
  expect(googleEmailInput).toBeDefined();
  fireEvent.change(googleEmailInput as HTMLElement, { target: { value: 'not-an-email' } });
  fireEvent.submit(createFormElement as HTMLFormElement);
  expect(createForm.getByText('Enter a valid Google email address.')).toBeInTheDocument();
  await user.clear(googleEmailInput as HTMLElement);
  await user.type(googleEmailInput as HTMLElement, 'sofia.diaz@example.test');
  await user.selectOptions(createForm.getByRole('combobox', { name: /Role/ }), 'delegated_manager');
  await user.click(createForm.getByLabelText('MFA already enrolled'));
  await user.type(createForm.getByRole('textbox', { name: /Reason/ }), 'Initial onboarding approved');
  await user.click(createForm.getByLabelText('Staff Accounts: Create'));
  await user.click(createForm.getByLabelText('Staff Accounts: Read'));
  await user.click(createForm.getByLabelText('Staff Accounts: Read'));
  await user.click(createForm.getByRole('button', { name: 'Create staff account' }));

  const createCall = vi.mocked(createStaffAccount).mock.calls[0]?.[0];
  expect(createCall?.displayName).toBe('Sofia Diaz');
  expect(createCall?.providerEmail).toBe('sofia.diaz@example.test');
  expect(createCall?.providerSubject).toBe('');
  expect(createCall?.roleName).toBe('delegated_manager');
  expect(createCall?.mfaEnrolled).toBe(true);
  expect(createCall?.permissionNames).toEqual(expect.arrayContaining(['staff_account:read', 'staff_account:create']));
  expect(createCall?.reasonText).toBe('Initial onboarding approved');
  expect(await screen.findByText('Staff account created in suspended onboarding state.')).toBeInTheDocument();
  expect(screen.getByText('Sofia Diaz')).toBeInTheDocument();
});

it('applies durable role presets and provisioning add-ons during onboarding', async () => {
  const user = userEvent.setup();
  const created = {
    ...suspended,
    staffId: '33333333-3333-4333-8333-333333333333',
    displayName: 'Residential Staff',
    providerSubject: 'pending-google-email:abc123',
    providerEmail: 'residential.staff@example.test',
    permissionNames: ['intake:read', 'worker:read', 'calendar_import:manage'],
  };
  vi.mocked(createStaffAccount).mockResolvedValue({ ok: true, value: { account: created, eventType: 'staff_account.created', resultVersion: 1 } });

  render(<LanguageProvider><StaffAccountAdmin /></LanguageProvider>);
  await screen.findByText('Mariela Torres');

  const createPanel = screen.getByRole('heading', { name: /Onboard staff account/ }).closest('section');
  expect(createPanel).not.toBeNull();
  const createForm = within(createPanel as HTMLElement);
  await user.type(createForm.getByRole('textbox', { name: /Display name/ }), 'Residential Staff');
  const googleEmailInput = createForm.getAllByRole('textbox', { name: /Google email/ })[0];
  expect(googleEmailInput).toBeDefined();
  await user.type(googleEmailInput as HTMLElement, 'residential.staff@example.test');
  await user.click(createForm.getByRole('button', { name: /Residential intake operator/ }));
  await user.click(createForm.getByRole('button', { name: /Add Google Calendar import/ }));
  await user.type(createForm.getByRole('textbox', { name: /Reason/ }), 'Residential worker and employer coverage');
  await user.click(createForm.getByRole('button', { name: 'Create staff account' }));

  const createCall = vi.mocked(createStaffAccount).mock.calls[0]?.[0];
  expect(createCall?.roleName).toBe('operations_staff');
  expect(createCall?.permissionNames).toEqual(expect.arrayContaining([
    'intake:read',
    'worker:read',
    'worker_residence:write',
    'employer_contact:details:read',
    'party_address:write',
    'calendar_import:manage',
  ]));
  expect(createCall?.permissionNames).not.toContain('worksite_address:write');
  expect(createCall?.permissionNames).not.toContain('staff_account:create');
});

it('requires staff sign-in before showing account administration controls', async () => {
  const user = userEvent.setup();
  vi.mocked(listStaffAccounts)
    .mockResolvedValueOnce({ ok: false, failure: { kind: 'sign_in_required' } })
    .mockResolvedValueOnce({ ok: true, value: [suspended] });

  render(<LanguageProvider><StaffAccountAdmin /></LanguageProvider>);

  expect(await screen.findByText('Sign in with a staff session before managing accounts.')).toBeInTheDocument();
  expect(screen.getByRole('button', { name: 'Mock Google sign-in' })).toBeInTheDocument();
  expect(screen.queryByRole('button', { name: 'Create staff account' })).not.toBeInTheDocument();
  expect(screen.queryByRole('table', { name: 'Staff account lifecycle table' })).not.toBeInTheDocument();

  await user.click(screen.getByRole('button', { name: 'Mock Google sign-in' }));

  expect(await screen.findByText('Mariela Torres')).toBeInTheDocument();
  expect(screen.getByRole('button', { name: 'Create staff account' })).toBeInTheDocument();
  expect(screen.getByRole('table', { name: 'Staff account lifecycle table' })).toBeInTheDocument();
});

it('surfaces recoverable account reload failures after an initial successful load', async () => {
  const user = userEvent.setup();
  vi.mocked(listStaffAccounts)
    .mockResolvedValueOnce({ ok: true, value: [suspended] })
    .mockResolvedValueOnce({ ok: false, failure: { kind: 'unavailable' } });

  render(<LanguageProvider><StaffAccountAdmin /></LanguageProvider>);
  await screen.findByText('Mariela Torres');

  await user.click(screen.getByRole('button', { name: 'Reload accounts' }));

  expect(await screen.findByText('The account service is unavailable. Try again after the connection recovers.')).toBeInTheDocument();
  expect(screen.queryByRole('table', { name: 'Staff account lifecycle table' })).not.toBeInTheDocument();
});

it('corrects suspended onboarding details without deleting the account', async () => {
  const user = userEvent.setup();
  const corrected = {
    ...suspended,
    displayName: 'Mariela Rivera',
    providerSubject: 'oidc:staff:corrected',
    mfaEnrolled: true,
    version: 2,
  };
  vi.mocked(correctStaffAccount).mockResolvedValue({
    ok: true,
    value: { account: corrected, eventType: 'staff_account.corrected', resultVersion: 2 },
  });

  render(<LanguageProvider><StaffAccountAdmin /></LanguageProvider>);
  await screen.findByText('Mariela Torres');

  await user.click(screen.getByRole('button', { name: 'Manage access' }));
  const correctionPanel = screen.getByRole('heading', { name: 'Correct onboarding: Mariela Torres' }).closest('section');
  expect(correctionPanel).not.toBeNull();
  const correction = within(correctionPanel as HTMLElement);
  expect(correction.getByText(/permanent role and permission changes/)).toBeInTheDocument();
  await user.clear(correction.getByRole('textbox', { name: /Display name/ }));
  await user.type(correction.getByRole('textbox', { name: /Display name/ }), 'Mariela Rivera');
  await user.clear(correction.getByRole('textbox', { name: /Provider subject/ }));
  await user.type(correction.getByRole('textbox', { name: /Provider subject/ }), 'oidc:staff:corrected');
  await user.selectOptions(correction.getByRole('combobox', { name: /Role/ }), 'delegated_manager');
  await user.click(correction.getByLabelText('MFA already enrolled'));
  await user.click(correction.getByLabelText('Intakes: Read'));
  await user.type(correction.getByLabelText('Reason'), 'Corrected provider subject before activation');
  await user.click(correction.getByRole('button', { name: 'Save correction' }));

  expect(correctStaffAccount).toHaveBeenCalledTimes(1);
  const correctionInput = vi.mocked(correctStaffAccount).mock.calls[0]?.[0];
  expect(correctionInput).toMatchObject({
    staffId: suspended.staffId,
    expectedVersion: 1,
    displayName: 'Mariela Rivera',
    providerSubject: 'oidc:staff:corrected',
    roleName: 'delegated_manager',
    mfaEnrolled: true,
    reasonText: 'Corrected provider subject before activation',
  });
  expect(correctionInput?.permissionNames).toEqual(expect.arrayContaining(['staff_account:read', 'intake:read']));
  expect(await screen.findByText('Staff account onboarding details corrected.')).toBeInTheDocument();
  expect(screen.getByText('Mariela Rivera')).toBeInTheDocument();
  expect(screen.queryByRole('heading', { name: /Correct onboarding/ })).not.toBeInTheDocument();
});

it('manages durable role and permission changes for active accounts', async () => {
  const user = userEvent.setup();
  const updated = {
    ...active,
    permissionNames: ['employer:read', 'worksite:read', 'worksite_address:read', 'worksite_address:write', 'staffing_request:read', 'shift_need:read'],
    version: 3,
  };
  vi.mocked(listStaffAccounts).mockResolvedValue({ ok: true, value: [active] });
  vi.mocked(correctStaffAccount).mockResolvedValue({
    ok: true,
    value: { account: updated, eventType: 'staff_account.corrected', resultVersion: 3 },
  });

  render(<LanguageProvider><StaffAccountAdmin /></LanguageProvider>);
  await screen.findByText('Mariela Torres');

  await user.click(screen.getByRole('button', { name: 'Manage access' }));
  const accessPanel = screen.getByRole('heading', { name: 'Manage access: Mariela Torres' }).closest('section');
  expect(accessPanel).not.toBeNull();
  const access = within(accessPanel as HTMLElement);
  await user.click(access.getByRole('button', { name: /Jobsite and request coordinator/ }));
  await user.type(access.getByRole('textbox', { name: /Reason/ }), 'Move account to jobsite coordination');
  await user.click(access.getByRole('button', { name: 'Save correction' }));

  const correctionInput = vi.mocked(correctStaffAccount).mock.calls[0]?.[0];
  expect(correctionInput).toMatchObject({
    staffId: active.staffId,
    expectedVersion: active.version,
    roleName: 'operations_staff',
    reasonText: 'Move account to jobsite coordination',
  });
  expect(correctionInput?.permissionNames).toEqual(expect.arrayContaining([
    'worksite:read',
    'worksite_address:write',
    'staffing_request:read',
    'shift_need:submit_review',
  ]));
  expect(correctionInput?.permissionNames).not.toContain('worker_residence:read');
  expect(await screen.findByText('Staff account access updated.')).toBeInTheDocument();
});

it('updates Google email for an existing account', async () => {
  const user = userEvent.setup();
  const updated = {
    ...active,
    providerEmail: 'new.email@example.test',
    lifecycleStatus: 'suspended' as const,
    mfaEnrolled: false,
    providerSubject: 'pending-google-email:def456',
    version: 3,
  };
  vi.mocked(listStaffAccounts).mockResolvedValue({ ok: true, value: [active] });
  vi.mocked(updateStaffAccountGoogleEmail).mockResolvedValue({
    ok: true,
    value: { account: updated, eventType: 'staff_account.signin_email_updated', resultVersion: 3 },
  });

  render(<LanguageProvider><StaffAccountAdmin /></LanguageProvider>);
  await screen.findByText('Mariela Torres');

  await user.click(screen.getByRole('button', { name: 'Google email' }));
  const emailPanel = screen.getByRole('heading', { name: 'Manage Google email: Mariela Torres' }).closest('section');
  expect(emailPanel).not.toBeNull();
  const emailForm = within(emailPanel as HTMLElement);
  expect(emailForm.getByText(/Replacing an existing email resets/)).toBeInTheDocument();
  await user.clear(emailForm.getByRole('textbox', { name: /Google email/ }));
  await user.type(emailForm.getByRole('textbox', { name: /Google email/ }), 'new.email@example.test');
  await user.type(emailForm.getByRole('textbox', { name: /Reason/ }), 'Correct the staff Google email');
  await user.click(emailForm.getByRole('button', { name: 'Save Google email' }));

  expect(updateStaffAccountGoogleEmail).toHaveBeenCalledWith(expect.objectContaining({
    staffId: active.staffId,
    expectedVersion: active.version,
    providerEmail: 'new.email@example.test',
    reasonText: 'Correct the staff Google email',
  }));
  expect(await screen.findByText('Staff account Google email updated.')).toBeInTheDocument();
  expect(screen.getByText('new.email@example.test')).toBeInTheDocument();
  expect(screen.getByText('Waiting for verified Google sign-in')).toBeInTheDocument();
});

it('validates and preserves the Google email form after recoverable errors', async () => {
  const user = userEvent.setup();
  vi.mocked(listStaffAccounts).mockResolvedValue({ ok: true, value: [active] });
  vi.mocked(updateStaffAccountGoogleEmail).mockResolvedValue({ ok: false, failure: { kind: 'stale' } });

  render(<LanguageProvider><StaffAccountAdmin /></LanguageProvider>);
  await screen.findByText('Mariela Torres');

  await user.click(screen.getByRole('button', { name: 'Google email' }));
  const firstPanel = screen.getByRole('heading', { name: 'Manage Google email: Mariela Torres' }).closest('section');
  expect(firstPanel).not.toBeNull();
  const firstForm = within(firstPanel as HTMLElement);
  const firstFormElement = firstPanel?.querySelector('form');
  expect(firstFormElement).not.toBeNull();
  await user.clear(firstForm.getByRole('textbox', { name: /Google email/ }));
  fireEvent.change(firstForm.getByRole('textbox', { name: /Google email/ }), { target: { value: 'not-an-email' } });
  fireEvent.submit(firstFormElement as HTMLFormElement);

  expect(firstForm.getByText('Enter a valid Google email address.')).toBeInTheDocument();
  expect(firstForm.getByText('Reason is required.')).toBeInTheDocument();
  expect(updateStaffAccountGoogleEmail).not.toHaveBeenCalled();

  await user.clear(firstForm.getByRole('textbox', { name: /Google email/ }));
  await user.type(firstForm.getByRole('textbox', { name: /Google email/ }), 'missing.reason@example.test');
  await user.click(firstForm.getByRole('button', { name: 'Save Google email' }));

  expect(firstForm.getByText('Reason is required.')).toBeInTheDocument();
  expect(updateStaffAccountGoogleEmail).not.toHaveBeenCalled();

  await user.click(firstForm.getByRole('button', { name: 'Close' }));
  expect(screen.queryByRole('heading', { name: 'Manage Google email: Mariela Torres' })).not.toBeInTheDocument();

  await user.click(screen.getByRole('button', { name: 'Google email' }));
  const secondPanel = screen.getByRole('heading', { name: 'Manage Google email: Mariela Torres' }).closest('section');
  expect(secondPanel).not.toBeNull();
  const secondForm = within(secondPanel as HTMLElement);
  await user.clear(secondForm.getByRole('textbox', { name: /Google email/ }));
  await user.type(secondForm.getByRole('textbox', { name: /Google email/ }), 'corrected@example.test');
  await user.type(secondForm.getByRole('textbox', { name: /Reason/ }), 'Version changed during email correction');
  await user.click(secondForm.getByRole('button', { name: 'Save Google email' }));

  expect(updateStaffAccountGoogleEmail).toHaveBeenCalledWith(expect.objectContaining({
    staffId: active.staffId,
    expectedVersion: active.version,
    providerEmail: 'corrected@example.test',
    reasonText: 'Version changed during email correction',
  }));
  expect(await screen.findByText('The account changed in another session. Reload before trying again.')).toBeInTheDocument();
  expect(screen.getByRole('heading', { name: 'Manage Google email: Mariela Torres' })).toBeInTheDocument();
});

it('shows correction validation and recoverable command errors', async () => {
  const user = userEvent.setup();
  vi.mocked(correctStaffAccount).mockResolvedValue({ ok: false, failure: { kind: 'stale' } });

  render(<LanguageProvider><StaffAccountAdmin /></LanguageProvider>);
  await screen.findByText('Mariela Torres');

  await user.click(screen.getByRole('button', { name: 'Manage access' }));
  const firstPanel = screen.getByRole('heading', { name: 'Correct onboarding: Mariela Torres' }).closest('section');
  expect(firstPanel).not.toBeNull();
  const firstCorrection = within(firstPanel as HTMLElement);
  await user.clear(firstCorrection.getByRole('textbox', { name: /Display name/ }));
  await user.clear(firstCorrection.getByRole('textbox', { name: /Google email/ }));
  await user.clear(firstCorrection.getByRole('textbox', { name: /Provider subject/ }));
  await user.click(firstCorrection.getByLabelText('Staff Accounts: Read'));
  await user.click(firstCorrection.getByRole('button', { name: 'Save correction' }));

  expect(firstCorrection.getByText('Display name is required.')).toBeInTheDocument();
  expect(firstCorrection.getByText('Google email or provider subject is required.')).toBeInTheDocument();
  expect(firstCorrection.getByText('Select at least one permission.')).toBeInTheDocument();
  expect(firstCorrection.getByText('Reason is required.')).toBeInTheDocument();
  expect(correctStaffAccount).not.toHaveBeenCalled();

  await user.click(firstCorrection.getByRole('button', { name: 'Close' }));
  await user.click(screen.getByRole('button', { name: 'Manage access' }));
  const secondPanel = screen.getByRole('heading', { name: 'Correct onboarding: Mariela Torres' }).closest('section');
  expect(secondPanel).not.toBeNull();
  const secondCorrection = within(secondPanel as HTMLElement);
  await user.type(secondCorrection.getByLabelText('Reason'), 'Version changed during onboarding correction');
  await user.click(secondCorrection.getByRole('button', { name: 'Save correction' }));

  expect(correctStaffAccount).toHaveBeenCalledTimes(1);
  expect(await screen.findByText('The account changed in another session. Reload before trying again.')).toBeInTheDocument();
  expect(screen.getByRole('heading', { name: 'Correct onboarding: Mariela Torres' })).toBeInTheDocument();
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
  vi.mocked(listStaffAccountEvents).mockResolvedValue({
    ok: true,
    value: [createdLifecycleEvent, activatedLifecycleEvent, lifecycleEvent],
  });

  render(<LanguageProvider><StaffAccountAdmin /></LanguageProvider>);
  await screen.findByText('Mariela Torres');

  await user.click(screen.getByRole('button', { name: 'History' }));

  expect(await screen.findByRole('heading', { name: 'Account history: Mariela Torres' })).toBeInTheDocument();
  expect(listStaffAccountEvents).toHaveBeenCalledWith(suspended.staffId);
  expect(screen.getByText('Account created')).toBeInTheDocument();
  expect(screen.getByText(/Suspended, version 1/)).toBeInTheDocument();
  expect(screen.getByText('Account activated')).toBeInTheDocument();
  expect(screen.getByText(/Suspended to Active, version 2/)).toBeInTheDocument();
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
  await user.click(lastElement(screen.getAllByLabelText('MFA enrollment confirmed')));
  await user.click(lastElement(screen.getAllByLabelText('MFA enrollment confirmed')));
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
  await user.type(screen.getByRole('textbox', { name: /Provider subject/ }), 'oidc:staff:789');
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
  vi.mocked(revokeStaffDelegation)
    .mockResolvedValueOnce({ ok: false, failure: { kind: 'stale' } })
    .mockResolvedValueOnce({ ok: true, value: { delegation: revoked, eventType: 'staff_delegation.revoked', resultVersion: 1 } });

  render(<LanguageProvider><StaffAccountAdmin /></LanguageProvider>);
  await screen.findByText('Mariela Torres');

  await user.click(screen.getByRole('button', { name: 'Delegations' }));
  expect(await screen.findByRole('heading', { name: 'Delegations: Mariela Torres' })).toBeInTheDocument();
  expect(screen.getAllByText('Intakes: Read').length).toBeGreaterThan(0);
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

  await user.click(screen.getByRole('button', { name: 'Revoke' }));
  expect(screen.getByText('Revocation reason is required.')).toBeInTheDocument();
  await user.type(screen.getByLabelText('Revocation reason'), 'Coverage ended');
  await user.click(screen.getByRole('button', { name: 'Revoke' }));
  expect(await screen.findByText('The account changed in another session. Reload before trying again.')).toBeInTheDocument();
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
  vi.mocked(grantStaffDelegation).mockResolvedValue({ ok: false, failure: { kind: 'delegation_permission_unavailable' } });

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
  expect(await screen.findByText('This session cannot delegate a permission it does not currently have. Add the named permission through account correction or ask an authorized owner.')).toBeInTheDocument();
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
