import { afterEach, expect, it, vi } from 'vitest';

import {
  activateStaffAccount,
  createStaffAccount,
  deprovisionStaffAccount,
  getStaffSession,
  grantStaffDelegation,
  listStaffAccountEvents,
  listStaffAccounts,
  listStaffDelegations,
  recordRecoveryEvidence,
  recordSessionRevocationEvidence,
  revokeStaffDelegation,
  suspendStaffAccount,
} from './staffAccountClient';

const account = {
  staff_id: '22222222-2222-4222-8222-222222222222',
  provider_subject: 'oidc:staff:123',
  display_name: 'Mariela Torres',
  role_name: 'operations_staff',
  lifecycle_status: 'suspended',
  mfa_enrolled: false,
  created_at: '2026-09-28T12:00:00Z',
  created_by: '11111111-1111-4111-8111-111111111111',
  updated_at: '2026-09-28T12:00:00Z',
  updated_by: '11111111-1111-4111-8111-111111111111',
  version: 1,
};

const delegation = {
  delegation_id: '44444444-4444-4444-8444-444444444444',
  grantor_staff_id: '11111111-1111-4111-8111-111111111111',
  grantee_staff_id: account.staff_id,
  permission_name: 'intake:read',
  scope_kind: 'global',
  scope_id: null,
  reason_text: 'Temporary coverage',
  starts_at: '2026-09-28T12:00:00Z',
  expires_at: '2026-09-29T12:00:00Z',
  revoked_at: null,
  revoked_by: null,
  revocation_reason: null,
};

const lifecycleEvent = {
  event_id: '55555555-5555-4555-8555-555555555555',
  command_id: 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa',
  staff_id: account.staff_id,
  actor_id: '11111111-1111-4111-8111-111111111111',
  event_type: 'staff_account.recovery_recorded',
  previous_status: 'active',
  new_status: 'active',
  previous_version: 2,
  new_version: 2,
  occurred_at: '2026-09-28T12:30:00Z',
  reason_text: 'Recovery evidence recorded in provider ticket',
};

afterEach(() => {
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});

it('lists staff accounts with no-store fetch options and strict response parsing', async () => {
  const fetchMock = vi.fn<typeof fetch>().mockResolvedValue(
    new Response(JSON.stringify({ items: [account] }), {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
    }),
  );
  vi.stubGlobal('fetch', fetchMock);

  const result = await listStaffAccounts();

  expect(fetchMock).toHaveBeenCalledWith('/api/staff/v1/staff-accounts', {
    method: 'GET',
    headers: { Accept: 'application/json' },
    cache: 'no-store',
    credentials: 'same-origin',
    mode: 'same-origin',
    redirect: 'error',
    referrerPolicy: 'no-referrer',
  });
  expect(result).toEqual({
    ok: true,
    value: [{
      staffId: account.staff_id,
      providerSubject: account.provider_subject,
      displayName: account.display_name,
      roleName: account.role_name,
      lifecycleStatus: account.lifecycle_status,
      mfaEnrolled: account.mfa_enrolled,
      createdAt: account.created_at,
      createdBy: account.created_by,
      updatedAt: account.updated_at,
      updatedBy: account.updated_by,
      version: account.version,
    }],
  });
});

it('reads the current staff session with account and delegation context', async () => {
  const fetchMock = vi.fn<typeof fetch>().mockResolvedValue(
    new Response(JSON.stringify({
      actor_id: account.staff_id,
      role_name: 'operations_staff',
      permission_names: ['intake:read', 'worker:read'],
      auth_context: 'staff_oidc',
      account,
      delegations: [delegation],
    }), {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
    }),
  );
  vi.stubGlobal('fetch', fetchMock);

  const result = await getStaffSession();

  expect(fetchMock).toHaveBeenCalledWith('/api/staff/v1/session', {
    method: 'GET',
    headers: { Accept: 'application/json' },
    cache: 'no-store',
    credentials: 'same-origin',
    mode: 'same-origin',
    redirect: 'error',
    referrerPolicy: 'no-referrer',
  });
  expect(result).toEqual({
    ok: true,
    value: {
      actorId: account.staff_id,
      roleName: 'operations_staff',
      permissionNames: ['intake:read', 'worker:read'],
      authContext: 'staff_oidc',
      account: {
        staffId: account.staff_id,
        providerSubject: account.provider_subject,
        displayName: account.display_name,
        roleName: account.role_name,
        lifecycleStatus: account.lifecycle_status,
        mfaEnrolled: account.mfa_enrolled,
        createdAt: account.created_at,
        createdBy: account.created_by,
        updatedAt: account.updated_at,
        updatedBy: account.updated_by,
        version: account.version,
      },
      delegations: [{
        delegationId: delegation.delegation_id,
        grantorStaffId: delegation.grantor_staff_id,
        granteeStaffId: delegation.grantee_staff_id,
        permissionName: delegation.permission_name,
        scopeKind: 'global',
        scopeId: null,
        reasonText: delegation.reason_text,
        startsAt: delegation.starts_at,
        expiresAt: delegation.expires_at,
        revokedAt: null,
        revokedBy: null,
        revocationReason: null,
      }],
    },
  });
});

it('lists staff account lifecycle events with no-store options and strict parsing', async () => {
  const fetchMock = vi.fn<typeof fetch>().mockResolvedValue(
    new Response(JSON.stringify({ items: [lifecycleEvent] }), {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
    }),
  );
  vi.stubGlobal('fetch', fetchMock);

  const result = await listStaffAccountEvents(account.staff_id);

  expect(fetchMock).toHaveBeenCalledWith(`/api/staff/v1/staff-accounts/${account.staff_id}/events`, {
    method: 'GET',
    headers: { Accept: 'application/json' },
    cache: 'no-store',
    credentials: 'same-origin',
    mode: 'same-origin',
    redirect: 'error',
    referrerPolicy: 'no-referrer',
  });
  expect(result).toEqual({
    ok: true,
    value: [{
      eventId: lifecycleEvent.event_id,
      commandId: lifecycleEvent.command_id,
      staffId: lifecycleEvent.staff_id,
      actorId: lifecycleEvent.actor_id,
      eventType: lifecycleEvent.event_type,
      previousStatus: lifecycleEvent.previous_status,
      newStatus: lifecycleEvent.new_status,
      previousVersion: lifecycleEvent.previous_version,
      newVersion: lifecycleEvent.new_version,
      occurredAt: lifecycleEvent.occurred_at,
      reasonText: lifecycleEvent.reason_text,
    }],
  });
});

it('rejects non-json lifecycle event responses as unusable reads', async () => {
  vi.stubGlobal('fetch', vi.fn<typeof fetch>().mockResolvedValue(
    new Response('not json', { status: 200, headers: { 'Content-Type': 'text/plain' } }),
  ));

  expect(await listStaffAccountEvents(account.staff_id)).toEqual({ ok: false, failure: { kind: 'unexpected' } });
});

it('maps staff authentication and account-state problem responses', async () => {
  const problem = (type: string, status: number) => new Response(JSON.stringify({ type }), {
    status,
    headers: { 'Content-Type': 'application/problem+json' },
  });
  const fetchMock = vi.fn<typeof fetch>()
    .mockResolvedValueOnce(problem('https://golden-rose.local/problems/staff-authentication-required', 401))
    .mockResolvedValueOnce(problem('https://golden-rose.local/problems/staff-authentication-failed', 401))
    .mockResolvedValueOnce(problem('https://golden-rose.local/problems/staff-account-unavailable', 403))
    .mockResolvedValueOnce(problem('https://golden-rose.local/problems/staff-identity-provider-unavailable', 503));
  vi.stubGlobal('fetch', fetchMock);

  expect(await getStaffSession()).toEqual({ ok: false, failure: { kind: 'sign_in_required' } });
  expect(await getStaffSession()).toEqual({ ok: false, failure: { kind: 'authentication_failed' } });
  expect(await getStaffSession()).toEqual({ ok: false, failure: { kind: 'account_unavailable' } });
  expect(await getStaffSession()).toEqual({ ok: false, failure: { kind: 'identity_provider_unavailable' } });
});

it('creates and activates accounts with idempotency headers and version validation', async () => {
  const activeAccount = { ...account, lifecycle_status: 'active', mfa_enrolled: true, version: 2 };
  const fetchMock = vi.fn<typeof fetch>()
    .mockResolvedValueOnce(
      new Response(JSON.stringify({ account, event_type: 'staff_account.created', result_version: 1 }), {
        status: 201,
        headers: { 'Content-Type': 'application/json', 'Idempotency-Result-Version': '1' },
      }),
    )
    .mockResolvedValueOnce(
      new Response(JSON.stringify({ account: activeAccount, event_type: 'staff_account.activated', result_version: 2 }), {
        status: 200,
        headers: { 'Content-Type': 'application/json', 'Idempotency-Result-Version': '2' },
      }),
    );
  vi.stubGlobal('fetch', fetchMock);

  const created = await createStaffAccount({
    commandId: 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa',
    displayName: 'Mariela Torres',
    mfaEnrolled: false,
    permissionNames: ['staff_account:read'],
    providerSubject: 'oidc:staff:123',
    reasonText: 'Initial onboarding',
    roleName: 'operations_staff',
  });
  const activated = await activateStaffAccount({
    commandId: 'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb',
    expectedVersion: 1,
    mfaEnrolled: true,
    reasonText: 'MFA confirmed',
    staffId: account.staff_id,
  });

  expect(created.ok).toBe(true);
  expect(activated.ok).toBe(true);
  const firstCall = fetchMock.mock.calls[0];
  expect(firstCall?.[0]).toBe('/api/staff/v1/staff-accounts');
  expect(firstCall?.[1]).toMatchObject({
    method: 'POST',
    headers: { 'Idempotency-Key': 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa' },
  });
  expect(fetchMock).toHaveBeenNthCalledWith(2, `/api/staff/v1/staff-accounts/${account.staff_id}/activate`, expect.objectContaining({
    method: 'POST',
    body: JSON.stringify({ expected_version: 1, reason_text: 'MFA confirmed', mfa_enrolled: true }),
  }));
});

it('lists, grants, and revokes staff delegations with strict command parsing', async () => {
  const revoked = {
    ...delegation,
    revoked_at: '2026-09-28T13:00:00Z',
    revoked_by: delegation.grantor_staff_id,
    revocation_reason: 'Coverage ended',
  };
  const fetchMock = vi.fn<typeof fetch>()
    .mockResolvedValueOnce(new Response(JSON.stringify({ items: [delegation] }), { status: 200, headers: { 'Content-Type': 'application/json' } }))
    .mockResolvedValueOnce(new Response(JSON.stringify({ delegation, event_type: 'staff_delegation.granted', result_version: 1 }), {
      status: 201,
      headers: { 'Content-Type': 'application/json', 'Idempotency-Result-Version': '1' },
    }))
    .mockResolvedValueOnce(new Response(JSON.stringify({ delegation: revoked, event_type: 'staff_delegation.revoked', result_version: 1 }), {
      status: 200,
      headers: { 'Content-Type': 'application/json', 'Idempotency-Result-Version': '1' },
    }));
  vi.stubGlobal('fetch', fetchMock);

  const listed = await listStaffDelegations(account.staff_id);
  const granted = await grantStaffDelegation({
    staffId: account.staff_id,
    permissionName: 'intake:read',
    expiresAt: delegation.expires_at,
    reasonText: 'Temporary coverage',
    commandId: delegation.delegation_id,
  });
  const revokedResult = await revokeStaffDelegation({
    staffId: account.staff_id,
    delegationId: delegation.delegation_id,
    reasonText: 'Coverage ended',
    commandId: 'eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee',
  });

  expect(listed.ok).toBe(true);
  expect(granted.ok).toBe(true);
  expect(revokedResult.ok).toBe(true);
  const grantInit = fetchMock.mock.calls[1]?.[1];
  expect(fetchMock).toHaveBeenNthCalledWith(1, `/api/staff/v1/staff-accounts/${account.staff_id}/delegations`, expect.objectContaining({ method: 'GET' }));
  expect(fetchMock).toHaveBeenNthCalledWith(2, `/api/staff/v1/staff-accounts/${account.staff_id}/delegations`, expect.objectContaining({
    method: 'POST',
    body: JSON.stringify({
      permission_name: 'intake:read',
      scope_kind: 'global',
      expires_at: delegation.expires_at,
      reason_text: 'Temporary coverage',
    }),
  }));
  expect(grantInit?.headers).toMatchObject({ 'Idempotency-Key': delegation.delegation_id });
  expect(fetchMock).toHaveBeenNthCalledWith(3, `/api/staff/v1/staff-accounts/${account.staff_id}/delegations/${delegation.delegation_id}/revoke`, expect.objectContaining({
    method: 'POST',
    body: JSON.stringify({ reason_text: 'Coverage ended' }),
  }));
});

it('rejects malformed delegation payloads and mismatched delegation command versions', async () => {
  const invalidDelegations = [
    { ...delegation, extra_field: 'private' },
    { ...delegation, delegation_id: 'not-a-uuid' },
    { ...delegation, grantor_staff_id: 'not-a-uuid' },
    { ...delegation, grantee_staff_id: 'not-a-uuid' },
    { ...delegation, permission_name: '' },
    { ...delegation, scope_kind: 'worker' },
    { ...delegation, scope_id: 'not-a-uuid' },
    { ...delegation, reason_text: '' },
    { ...delegation, starts_at: 'not-a-date' },
    { ...delegation, expires_at: 'not-a-date' },
    { ...delegation, revoked_at: 'not-a-date' },
    { ...delegation, revoked_by: 'not-a-uuid' },
    { ...delegation, revocation_reason: '' },
  ];

  for (const invalidDelegation of invalidDelegations) {
    vi.stubGlobal('fetch', vi.fn<typeof fetch>().mockResolvedValue(
      new Response(JSON.stringify({ items: [invalidDelegation] }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    ));

    expect(await listStaffDelegations(account.staff_id)).toEqual({ ok: false, failure: { kind: 'unexpected' } });
  }

  vi.stubGlobal('fetch', vi.fn<typeof fetch>().mockResolvedValue(
    new Response(JSON.stringify({ delegation, event_type: 'staff_delegation.granted', result_version: 2 }), {
      status: 201,
      headers: { 'Content-Type': 'application/json', 'Idempotency-Result-Version': '2' },
    }),
  ));

  expect(await grantStaffDelegation({
    staffId: account.staff_id,
    permissionName: 'intake:read',
    expiresAt: delegation.expires_at,
    reasonText: 'Temporary coverage',
    commandId: delegation.delegation_id,
  })).toEqual({ ok: false, failure: { kind: 'unknown_outcome' } });
});

it('rejects malformed lifecycle event payloads', async () => {
  const invalidEvents = [
    { ...lifecycleEvent, extra_field: 'private' },
    { ...lifecycleEvent, event_id: 'not-a-uuid' },
    { ...lifecycleEvent, command_id: 'not-a-uuid' },
    { ...lifecycleEvent, staff_id: 'not-a-uuid' },
    { ...lifecycleEvent, actor_id: 'not-a-uuid' },
    { ...lifecycleEvent, event_type: 'staff_account.provider_reset' },
    { ...lifecycleEvent, previous_status: 'pending' },
    { ...lifecycleEvent, new_status: 'pending' },
    { ...lifecycleEvent, previous_version: 0 },
    { ...lifecycleEvent, new_version: 0 },
    { ...lifecycleEvent, occurred_at: 'not-a-date' },
    { ...lifecycleEvent, reason_text: '' },
  ];

  for (const invalidEvent of invalidEvents) {
    vi.stubGlobal('fetch', vi.fn<typeof fetch>().mockResolvedValue(
      new Response(JSON.stringify({ items: [invalidEvent] }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    ));

    expect(await listStaffAccountEvents(account.staff_id)).toEqual({ ok: false, failure: { kind: 'unexpected' } });
  }
});

it('maps version conflicts and unknown command outcomes to recoverable failures', async () => {
  const fetchMock = vi.fn<typeof fetch>()
    .mockResolvedValueOnce(new Response(JSON.stringify({ type: 'stale' }), { status: 412, headers: { 'Content-Type': 'application/problem+json' } }))
    .mockResolvedValueOnce(
      new Response(JSON.stringify({ account, event_type: 'staff_account.sessions_revoked', result_version: 1 }), {
        status: 200,
        headers: { 'Content-Type': 'application/json', 'Idempotency-Result-Version': '999' },
      }),
    );
  vi.stubGlobal('fetch', fetchMock);

  const stale = await activateStaffAccount({
    commandId: 'cccccccc-cccc-4ccc-8ccc-cccccccccccc',
    expectedVersion: 1,
    mfaEnrolled: true,
    reasonText: 'MFA confirmed',
    staffId: account.staff_id,
  });
  const unknown = await recordSessionRevocationEvidence({
    commandId: 'dddddddd-dddd-4ddd-8ddd-dddddddddddd',
    expectedVersion: 1,
    reasonText: 'Provider console note',
    staffId: account.staff_id,
  });

  expect(stale).toEqual({ ok: false, failure: { kind: 'stale' } });
  expect(unknown).toEqual({ ok: false, failure: { kind: 'unknown_outcome' } });
});

it('maps list and lifecycle problem responses without reading private payloads', async () => {
  const fetchMock = vi.fn<typeof fetch>()
    .mockResolvedValueOnce(new Response(JSON.stringify({ detail: 'forbidden' }), { status: 403, headers: { 'Content-Type': 'application/problem+json' } }))
    .mockResolvedValueOnce(new Response(JSON.stringify({ detail: 'invalid' }), { status: 422, headers: { 'Content-Type': 'application/problem+json' } }))
    .mockResolvedValueOnce(new Response(JSON.stringify({ detail: 'missing' }), { status: 404, headers: { 'Content-Type': 'application/problem+json' } }))
    .mockResolvedValueOnce(new Response(JSON.stringify({ detail: 'unavailable' }), { status: 503, headers: { 'Content-Type': 'application/problem+json' } }))
    .mockResolvedValueOnce(new Response(JSON.stringify({ detail: 'bad request' }), { status: 400, headers: { 'Content-Type': 'application/problem+json' } }))
    .mockRejectedValueOnce(new Error('network down'));
  vi.stubGlobal('fetch', fetchMock);

  const listed = await listStaffAccounts();
  const created = await createStaffAccount({
    commandId: 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa',
    displayName: 'Mariela Torres',
    mfaEnrolled: false,
    permissionNames: ['staff_account:read'],
    providerSubject: 'oidc:staff:123',
    reasonText: 'Initial onboarding',
    roleName: 'operations_staff',
  });
  const activated = await activateStaffAccount({
    commandId: 'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb',
    expectedVersion: 1,
    mfaEnrolled: true,
    reasonText: 'MFA confirmed',
    staffId: account.staff_id,
  });
  const suspended = await suspendStaffAccount({
    commandId: 'cccccccc-cccc-4ccc-8ccc-cccccccccccc',
    expectedVersion: 2,
    reasonText: 'Access review',
    staffId: account.staff_id,
  });
  const deprovisioned = await deprovisionStaffAccount({
    commandId: 'dddddddd-dddd-4ddd-8ddd-dddddddddddd',
    expectedVersion: 3,
    reasonText: 'Offboarding',
    staffId: account.staff_id,
  });
  const recovery = await recordRecoveryEvidence({
    commandId: 'eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee',
    expectedVersion: 4,
    reasonText: 'Recovery record',
    staffId: account.staff_id,
  });

  expect(listed).toEqual({ ok: false, failure: { kind: 'forbidden' } });
  expect(created).toEqual({ ok: false, failure: { kind: 'validation' } });
  expect(activated).toEqual({ ok: false, failure: { kind: 'not_found' } });
  expect(suspended).toEqual({ ok: false, failure: { kind: 'unavailable' } });
  expect(deprovisioned).toEqual({ ok: false, failure: { kind: 'validation' } });
  expect(recovery).toEqual({ ok: false, failure: { kind: 'unknown_outcome' } });
});

it('rejects malformed account payloads for list and command reads', async () => {
  const invalidAccounts = [
    { ...account, extra_field: 'private' },
    { ...account, staff_id: 'not-a-uuid' },
    { ...account, provider_subject: '' },
    { ...account, role_name: 'superuser' },
    { ...account, lifecycle_status: 'pending' },
    { ...account, mfa_enrolled: 'yes' },
    { ...account, created_at: 'not-a-date' },
    { ...account, created_by: 'not-a-uuid' },
    { ...account, updated_by: 'not-a-uuid' },
    { ...account, version: 0 },
  ];

  for (const invalidAccount of invalidAccounts) {
    vi.stubGlobal('fetch', vi.fn<typeof fetch>().mockResolvedValue(
      new Response(JSON.stringify({ items: [invalidAccount] }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    ));

    expect(await listStaffAccounts()).toEqual({ ok: false, failure: { kind: 'unexpected' } });
  }

  vi.stubGlobal('fetch', vi.fn<typeof fetch>().mockResolvedValue(
    new Response(JSON.stringify({ account, event_type: 'staff_account.created', result_version: 2 }), {
      status: 201,
      headers: { 'Content-Type': 'application/json', 'Idempotency-Result-Version': '2' },
    }),
  ));

  expect(await createStaffAccount({
    commandId: 'ffffffff-ffff-4fff-8fff-ffffffffffff',
    displayName: 'Mariela Torres',
    mfaEnrolled: false,
    permissionNames: ['staff_account:read'],
    providerSubject: 'oidc:staff:123',
    reasonText: 'Initial onboarding',
    roleName: 'operations_staff',
  })).toEqual({ ok: false, failure: { kind: 'unknown_outcome' } });
});
