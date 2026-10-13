import { staffApiFetch } from '../auth/staffAuthSession';

export type StaffAccountRole = 'owner' | 'delegated_manager' | 'operations_staff' | 'platform_administrator';
export type StaffAccountStatus = 'active' | 'suspended' | 'deprovisioned';
export type StaffAccountEvent =
  | 'staff_account.created'
  | 'staff_account.activated'
  | 'staff_account.suspended'
  | 'staff_account.deprovisioned'
  | 'staff_account.corrected'
  | 'staff_account.signin_email_updated'
  | 'staff_account.recovery_recorded'
  | 'staff_account.sessions_revoked';
export type StaffDelegationEvent = 'staff_delegation.granted' | 'staff_delegation.revoked';
export type StaffAuthContext = 'synthetic' | 'staff_oidc';
export type StaffIdentityBoundary =
  | 'synthetic_local_or_test'
  | 'synthetic_private_develop'
  | 'production_oidc_configured';
export type StaffIdentityReadinessAction =
  | 'use_only_for_local_or_test'
  | 'configure_staff_oidc_for_production'
  | 'replace_synthetic_staff_auth_before_production'
  | 'configure_staff_oidc_issuer_audience_and_jwks'
  | 'create_staff_accounts_before_live_use'
  | 'confirm_mfa_claim_mapping'
  | 'record_recovery_and_session_revocation_provider_runbook';

export type StaffIdentityReadiness = {
  environment: 'local' | 'test' | 'develop' | 'production';
  authMode: StaffAuthContext;
  staffIdentityBoundary: StaffIdentityBoundary;
  productionStaffAuthReady: boolean;
  syntheticStaffRuntimeAllowed: boolean;
  recoveryAndSessionRevocationEvidenceOnly: boolean;
  requiredOperatorActions: StaffIdentityReadinessAction[];
};

export type StaffAccount = {
  staffId: string;
  providerSubject: string;
  providerEmail: string | null;
  displayName: string;
  roleName: StaffAccountRole;
  lifecycleStatus: StaffAccountStatus;
  mfaEnrolled: boolean;
  permissionNames: string[];
  createdAt: string;
  createdBy: string;
  updatedAt: string;
  updatedBy: string;
  version: number;
};

export type StaffAccountLifecycleResult = {
  account: StaffAccount;
  eventType: StaffAccountEvent;
  resultVersion: number;
};

export type StaffAccountLifecycleEvent = {
  eventId: string;
  commandId: string;
  staffId: string;
  actorId: string;
  eventType: StaffAccountEvent;
  previousStatus: StaffAccountStatus | null;
  newStatus: StaffAccountStatus;
  previousVersion: number | null;
  newVersion: number;
  occurredAt: string;
  reasonText: string;
};

export type StaffDelegation = {
  delegationId: string;
  grantorStaffId: string;
  granteeStaffId: string;
  permissionName: string;
  scopeKind: 'global';
  scopeId: string | null;
  reasonText: string;
  startsAt: string;
  expiresAt: string;
  revokedAt: string | null;
  revokedBy: string | null;
  revocationReason: string | null;
};

export type StaffDelegationResult = {
  delegation: StaffDelegation;
  eventType: StaffDelegationEvent;
  resultVersion: number;
};

export type StaffSession = {
  actorId: string;
  roleName: string;
  permissionNames: string[];
  authContext: StaffAuthContext;
  account: StaffAccount | null;
  delegations: StaffDelegation[];
};

export type StaffAccountFailureKind =
  | 'sign_in_required'
  | 'authentication_failed'
  | 'account_unavailable'
  | 'identity_provider_unavailable'
  | 'validation'
  | 'forbidden'
  | 'not_found'
  | 'stale'
  | 'unavailable'
  | 'unknown_outcome'
  | 'unexpected'
  | 'delegation_self_grant'
  | 'delegation_permission_unavailable'
  | 'delegation_target_unavailable'
  | 'delegation_expiration_invalid';

export type StaffAccountResult<T> = { ok: true; value: T } | { ok: false; failure: { kind: StaffAccountFailureKind } };

export type CreateStaffAccountInput = {
  providerSubject: string;
  providerEmail?: string;
  displayName: string;
  roleName: StaffAccountRole;
  permissionNames: string[];
  mfaEnrolled: boolean;
  reasonText: string;
  commandId: string;
};

export type CorrectStaffAccountInput = CreateStaffAccountInput & {
  staffId: string;
  expectedVersion: number;
};

export type StaffAccountTransitionInput = {
  staffId: string;
  expectedVersion: number;
  reasonText: string;
  commandId: string;
};

export type ActivateStaffAccountInput = StaffAccountTransitionInput & {
  mfaEnrolled: boolean;
};

export type UpdateStaffAccountGoogleEmailInput = StaffAccountTransitionInput & {
  providerEmail: string;
};

export type GrantStaffDelegationInput = {
  staffId: string;
  permissionName: string;
  expiresAt: string;
  reasonText: string;
  commandId: string;
};

export type RevokeStaffDelegationInput = {
  staffId: string;
  delegationId: string;
  reasonText: string;
  commandId: string;
};

const uuid = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
const roles = new Set<StaffAccountRole>(['owner', 'delegated_manager', 'operations_staff', 'platform_administrator']);
const statuses = new Set<StaffAccountStatus>(['active', 'suspended', 'deprovisioned']);
const authContexts = new Set<StaffAuthContext>(['synthetic', 'staff_oidc']);
const environments = new Set<StaffIdentityReadiness['environment']>(['local', 'test', 'develop', 'production']);
const identityBoundaries = new Set<StaffIdentityBoundary>([
  'synthetic_local_or_test',
  'synthetic_private_develop',
  'production_oidc_configured',
]);
const readinessActions = new Set<StaffIdentityReadinessAction>([
  'use_only_for_local_or_test',
  'configure_staff_oidc_for_production',
  'replace_synthetic_staff_auth_before_production',
  'configure_staff_oidc_issuer_audience_and_jwks',
  'create_staff_accounts_before_live_use',
  'confirm_mfa_claim_mapping',
  'record_recovery_and_session_revocation_provider_runbook',
]);
const events = new Set<StaffAccountEvent>([
  'staff_account.created',
  'staff_account.activated',
  'staff_account.suspended',
  'staff_account.deprovisioned',
  'staff_account.corrected',
  'staff_account.signin_email_updated',
  'staff_account.recovery_recorded',
  'staff_account.sessions_revoked',
]);
const delegationEvents = new Set<StaffDelegationEvent>(['staff_delegation.granted', 'staff_delegation.revoked']);

function object(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

function text(value: unknown, max = 512): value is string {
  return typeof value === 'string' && value.trim().length > 0 && Array.from(value).length <= max;
}

function positive(value: unknown): value is number {
  return Number.isSafeInteger(value) && Number(value) > 0;
}

function timestamp(value: unknown): value is string {
  return typeof value === 'string' && !Number.isNaN(Date.parse(value));
}

function isJson(response: Response) {
  return /^application\/(?:json|problem\+json)(?:\s*;.*)?$/i.test(response.headers.get('Content-Type') ?? '');
}

async function cancelBody(response: Response) {
  try {
    await response.body?.cancel();
  } catch {
    // Best-effort cleanup only.
  }
}

function parseProblemType(value: unknown): string | null {
  if (!object(value)) return null;
  return typeof value.type === 'string' ? value.type : null;
}

function failureFromProblem(status: number, type: string | null, command = false): StaffAccountResult<never> {
  if (type === 'https://golden-rose.local/problems/staff-authentication-required') {
    return { ok: false, failure: { kind: 'sign_in_required' } };
  }
  if (type === 'https://golden-rose.local/problems/staff-authentication-failed') {
    return { ok: false, failure: { kind: 'authentication_failed' } };
  }
  if (type === 'https://golden-rose.local/problems/staff-account-unavailable') {
    return { ok: false, failure: { kind: 'account_unavailable' } };
  }
  if (type === 'https://golden-rose.local/problems/staff-identity-provider-unavailable') {
    return { ok: false, failure: { kind: 'identity_provider_unavailable' } };
  }
  if (type === 'https://golden-rose.local/problems/staff-delegation-self-grant') {
    return { ok: false, failure: { kind: 'delegation_self_grant' } };
  }
  if (type === 'https://golden-rose.local/problems/staff-delegation-permission-unavailable') {
    return { ok: false, failure: { kind: 'delegation_permission_unavailable' } };
  }
  if (type === 'https://golden-rose.local/problems/staff-delegation-target-unavailable') {
    return { ok: false, failure: { kind: 'delegation_target_unavailable' } };
  }
  if (type === 'https://golden-rose.local/problems/staff-delegation-expiration-invalid') {
    return { ok: false, failure: { kind: 'delegation_expiration_invalid' } };
  }
  if (status === 400 || status === 422) return { ok: false, failure: { kind: 'validation' } };
  if (status === 403) return { ok: false, failure: { kind: 'forbidden' } };
  if (status === 404) return { ok: false, failure: { kind: 'not_found' } };
  if (status === 412) return { ok: false, failure: { kind: 'stale' } };
  if (status === 503) return { ok: false, failure: { kind: 'unavailable' } };
  return { ok: false, failure: { kind: command ? 'unknown_outcome' : 'unexpected' } };
}

async function responseFailure(response: Response, command = false): Promise<StaffAccountResult<never>> {
  let type: string | null = null;
  if (isJson(response)) {
    try {
      type = parseProblemType(await response.json());
    } catch {
      type = null;
    }
  } else {
    await cancelBody(response);
  }
  return failureFromProblem(response.status, type, command);
}

function parseAccount(value: unknown): StaffAccount | null {
  if (!object(value)) return null;
  const keys = new Set([
    'staff_id',
    'provider_subject',
    'provider_email',
    'display_name',
    'role_name',
    'lifecycle_status',
    'mfa_enrolled',
    'permission_names',
    'created_at',
    'created_by',
    'updated_at',
    'updated_by',
    'version',
  ]);
  if (Object.keys(value).some((key) => !keys.has(key))) return null;
  if (typeof value.staff_id !== 'string' || !uuid.test(value.staff_id)) return null;
  if (!text(value.provider_subject, 256) || !text(value.display_name, 160)) return null;
  if (value.provider_email !== null && !text(value.provider_email, 320)) return null;
  if (typeof value.role_name !== 'string' || !roles.has(value.role_name as StaffAccountRole)) return null;
  if (typeof value.lifecycle_status !== 'string' || !statuses.has(value.lifecycle_status as StaffAccountStatus)) return null;
  if (typeof value.mfa_enrolled !== 'boolean') return null;
  if (!Array.isArray(value.permission_names) || value.permission_names.length > 100) return null;
  if (value.permission_names.some((permission) => !text(permission, 120))) return null;
  if (!timestamp(value.created_at) || !timestamp(value.updated_at)) return null;
  if (typeof value.created_by !== 'string' || !uuid.test(value.created_by)) return null;
  if (typeof value.updated_by !== 'string' || !uuid.test(value.updated_by)) return null;
  if (!positive(value.version)) return null;
  return {
    staffId: value.staff_id,
    providerSubject: value.provider_subject,
    providerEmail: value.provider_email,
    displayName: value.display_name,
    roleName: value.role_name as StaffAccountRole,
    lifecycleStatus: value.lifecycle_status as StaffAccountStatus,
    mfaEnrolled: value.mfa_enrolled,
    permissionNames: value.permission_names as string[],
    createdAt: value.created_at,
    createdBy: value.created_by,
    updatedAt: value.updated_at,
    updatedBy: value.updated_by,
    version: value.version,
  };
}

function parseLifecycle(value: unknown): StaffAccountLifecycleResult | null {
  if (!object(value)) return null;
  const account = parseAccount(value.account);
  if (account === null || typeof value.event_type !== 'string' || !events.has(value.event_type as StaffAccountEvent)) return null;
  if (!positive(value.result_version) || value.result_version !== account.version) return null;
  return {
    account,
    eventType: value.event_type as StaffAccountEvent,
    resultVersion: value.result_version,
  };
}

function parseLifecycleEvent(value: unknown): StaffAccountLifecycleEvent | null {
  if (!object(value)) return null;
  const keys = new Set([
    'event_id',
    'command_id',
    'staff_id',
    'actor_id',
    'event_type',
    'previous_status',
    'new_status',
    'previous_version',
    'new_version',
    'occurred_at',
    'reason_text',
  ]);
  if (Object.keys(value).some((key) => !keys.has(key))) return null;
  if (typeof value.event_id !== 'string' || !uuid.test(value.event_id)) return null;
  if (typeof value.command_id !== 'string' || !uuid.test(value.command_id)) return null;
  if (typeof value.staff_id !== 'string' || !uuid.test(value.staff_id)) return null;
  if (typeof value.actor_id !== 'string' || !uuid.test(value.actor_id)) return null;
  if (typeof value.event_type !== 'string' || !events.has(value.event_type as StaffAccountEvent)) return null;
  if (value.previous_status !== null && (typeof value.previous_status !== 'string' || !statuses.has(value.previous_status as StaffAccountStatus))) return null;
  if (typeof value.new_status !== 'string' || !statuses.has(value.new_status as StaffAccountStatus)) return null;
  if (value.previous_version !== null && !positive(value.previous_version)) return null;
  if (!positive(value.new_version)) return null;
  if (!timestamp(value.occurred_at) || !text(value.reason_text, 512)) return null;
  return {
    eventId: value.event_id,
    commandId: value.command_id,
    staffId: value.staff_id,
    actorId: value.actor_id,
    eventType: value.event_type as StaffAccountEvent,
    previousStatus: value.previous_status as StaffAccountStatus | null,
    newStatus: value.new_status as StaffAccountStatus,
    previousVersion: value.previous_version,
    newVersion: value.new_version,
    occurredAt: value.occurred_at,
    reasonText: value.reason_text,
  };
}

function parseDelegation(value: unknown): StaffDelegation | null {
  if (!object(value)) return null;
  const keys = new Set([
    'delegation_id',
    'grantor_staff_id',
    'grantee_staff_id',
    'permission_name',
    'scope_kind',
    'scope_id',
    'reason_text',
    'starts_at',
    'expires_at',
    'revoked_at',
    'revoked_by',
    'revocation_reason',
  ]);
  if (Object.keys(value).some((key) => !keys.has(key))) return null;
  if (typeof value.delegation_id !== 'string' || !uuid.test(value.delegation_id)) return null;
  if (typeof value.grantor_staff_id !== 'string' || !uuid.test(value.grantor_staff_id)) return null;
  if (typeof value.grantee_staff_id !== 'string' || !uuid.test(value.grantee_staff_id)) return null;
  if (!text(value.permission_name, 120) || value.scope_kind !== 'global') return null;
  if (value.scope_id !== null && (typeof value.scope_id !== 'string' || !uuid.test(value.scope_id))) return null;
  if (!text(value.reason_text, 512)) return null;
  if (!timestamp(value.starts_at) || !timestamp(value.expires_at)) return null;
  if (value.revoked_at !== null && !timestamp(value.revoked_at)) return null;
  if (value.revoked_by !== null && (typeof value.revoked_by !== 'string' || !uuid.test(value.revoked_by))) return null;
  if (value.revocation_reason !== null && !text(value.revocation_reason, 512)) return null;
  return {
    delegationId: value.delegation_id,
    grantorStaffId: value.grantor_staff_id,
    granteeStaffId: value.grantee_staff_id,
    permissionName: value.permission_name,
    scopeKind: 'global',
    scopeId: value.scope_id,
    reasonText: value.reason_text,
    startsAt: value.starts_at,
    expiresAt: value.expires_at,
    revokedAt: value.revoked_at,
    revokedBy: value.revoked_by,
    revocationReason: value.revocation_reason,
  };
}

function parseDelegationCommand(value: unknown): StaffDelegationResult | null {
  if (!object(value)) return null;
  const delegation = parseDelegation(value.delegation);
  if (delegation === null || typeof value.event_type !== 'string' || !delegationEvents.has(value.event_type as StaffDelegationEvent)) return null;
  if (value.result_version !== 1) return null;
  return {
    delegation,
    eventType: value.event_type as StaffDelegationEvent,
    resultVersion: value.result_version,
  };
}

function parseSession(value: unknown): StaffSession | null {
  if (!object(value)) return null;
  const keys = new Set(['actor_id', 'role_name', 'permission_names', 'auth_context', 'account', 'delegations']);
  if (Object.keys(value).some((key) => !keys.has(key))) return null;
  if (typeof value.actor_id !== 'string' || !uuid.test(value.actor_id)) return null;
  if (!text(value.role_name, 120)) return null;
  const permissionNames = value.permission_names;
  if (!Array.isArray(permissionNames) || permissionNames.length > 100) return null;
  if (permissionNames.some((permission) => !text(permission, 120))) return null;
  if (typeof value.auth_context !== 'string' || !authContexts.has(value.auth_context as StaffAuthContext)) return null;
  if (value.account !== null && parseAccount(value.account) === null) return null;
  if (!Array.isArray(value.delegations) || value.delegations.length > 50) return null;
  const delegations = value.delegations.map(parseDelegation);
  if (delegations.some((delegation) => delegation === null)) return null;
  return {
    actorId: value.actor_id,
    roleName: value.role_name,
    permissionNames: permissionNames as string[],
    authContext: value.auth_context as StaffAuthContext,
    account: value.account === null ? null : parseAccount(value.account),
    delegations: delegations as StaffDelegation[],
  };
}

function parseIdentityReadiness(value: unknown): StaffIdentityReadiness | null {
  if (!object(value)) return null;
  const keys = new Set([
    'environment',
    'auth_mode',
    'staff_identity_boundary',
    'production_staff_auth_ready',
    'synthetic_staff_runtime_allowed',
    'recovery_and_session_revocation_evidence_only',
    'required_operator_actions',
  ]);
  if (Object.keys(value).some((key) => !keys.has(key))) return null;
  if (typeof value.environment !== 'string' || !environments.has(value.environment as StaffIdentityReadiness['environment'])) return null;
  if (typeof value.auth_mode !== 'string' || !authContexts.has(value.auth_mode as StaffAuthContext)) return null;
  if (typeof value.staff_identity_boundary !== 'string' || !identityBoundaries.has(value.staff_identity_boundary as StaffIdentityBoundary)) return null;
  if (typeof value.production_staff_auth_ready !== 'boolean') return null;
  if (typeof value.synthetic_staff_runtime_allowed !== 'boolean') return null;
  if (typeof value.recovery_and_session_revocation_evidence_only !== 'boolean') return null;
  if (!Array.isArray(value.required_operator_actions) || value.required_operator_actions.length > 20) return null;
  if (value.required_operator_actions.some((action) => typeof action !== 'string' || !readinessActions.has(action as StaffIdentityReadinessAction))) {
    return null;
  }
  return {
    environment: value.environment as StaffIdentityReadiness['environment'],
    authMode: value.auth_mode as StaffAuthContext,
    staffIdentityBoundary: value.staff_identity_boundary as StaffIdentityBoundary,
    productionStaffAuthReady: value.production_staff_auth_ready,
    syntheticStaffRuntimeAllowed: value.synthetic_staff_runtime_allowed,
    recoveryAndSessionRevocationEvidenceOnly: value.recovery_and_session_revocation_evidence_only,
    requiredOperatorActions: value.required_operator_actions as StaffIdentityReadinessAction[],
  };
}

async function request<T>(
  path: string,
  init: RequestInit,
  validate: (value: unknown) => T | null,
  command = false,
): Promise<StaffAccountResult<T>> {
  let response: Response;
  try {
    response = await staffApiFetch(`/api/staff/v1${path}`, {
      cache: 'no-store',
      credentials: 'same-origin',
      mode: 'same-origin',
      redirect: 'error',
      referrerPolicy: 'no-referrer',
      ...init,
    });
  } catch {
    return { ok: false, failure: { kind: command ? 'unknown_outcome' : 'unavailable' } };
  }
  if (response.status < 200 || response.status >= 300) {
    return responseFailure(response, command);
  }
  if (!isJson(response)) {
    await cancelBody(response);
    return { ok: false, failure: { kind: command ? 'unknown_outcome' : 'unexpected' } };
  }
  try {
    const payload: unknown = await response.json();
    const parsed = validate(payload);
    if (parsed === null) return { ok: false, failure: { kind: command ? 'unknown_outcome' : 'unexpected' } };
    if (command && object(payload)) {
      const headerVersion = response.headers.get('Idempotency-Result-Version');
      if (headerVersion !== String(payload.result_version)) {
        return { ok: false, failure: { kind: 'unknown_outcome' } };
      }
    }
    return { ok: true, value: parsed };
  } catch {
    return { ok: false, failure: { kind: command ? 'unknown_outcome' : 'unexpected' } };
  }
}

export async function getStaffSession(): Promise<StaffAccountResult<StaffSession>> {
  return request('/session', { method: 'GET', headers: { Accept: 'application/json' } }, parseSession);
}

export async function getStaffIdentityReadiness(): Promise<StaffAccountResult<StaffIdentityReadiness>> {
  return request('/staff-identity-readiness', { method: 'GET', headers: { Accept: 'application/json' } }, parseIdentityReadiness);
}

export async function listStaffAccounts(): Promise<StaffAccountResult<StaffAccount[]>> {
  return request('/staff-accounts', { method: 'GET', headers: { Accept: 'application/json' } }, (value) => {
    if (!object(value) || !Array.isArray(value.items) || value.items.length > 50) return null;
    const items = value.items.map(parseAccount);
    if (items.some((item) => item === null)) return null;
    return items as StaffAccount[];
  });
}

export async function listStaffAccountEvents(staffId: string): Promise<StaffAccountResult<StaffAccountLifecycleEvent[]>> {
  return request(`/staff-accounts/${staffId}/events`, { method: 'GET', headers: { Accept: 'application/json' } }, (value) => {
    if (!object(value) || !Array.isArray(value.items) || value.items.length > 50) return null;
    const items = value.items.map(parseLifecycleEvent);
    if (items.some((item) => item === null)) return null;
    return items as StaffAccountLifecycleEvent[];
  });
}

export async function createStaffAccount(input: CreateStaffAccountInput): Promise<StaffAccountResult<StaffAccountLifecycleResult>> {
  const providerEmail = input.providerEmail ?? '';
  return request('/staff-accounts', {
    method: 'POST',
    headers: { Accept: 'application/json', 'Content-Type': 'application/json', 'Idempotency-Key': input.commandId },
    body: JSON.stringify({
      provider_subject: input.providerSubject,
      provider_email: providerEmail.length > 0 ? providerEmail : null,
      display_name: input.displayName,
      role_name: input.roleName,
      permission_names: input.permissionNames,
      mfa_enrolled: input.mfaEnrolled,
      reason_text: input.reasonText,
    }),
  }, parseLifecycle, true);
}

export async function correctStaffAccount(input: CorrectStaffAccountInput): Promise<StaffAccountResult<StaffAccountLifecycleResult>> {
  const providerEmail = input.providerEmail ?? '';
  return request(`/staff-accounts/${input.staffId}/correct-onboarding`, {
    method: 'POST',
    headers: { Accept: 'application/json', 'Content-Type': 'application/json', 'Idempotency-Key': input.commandId },
    body: JSON.stringify({
      expected_version: input.expectedVersion,
      provider_subject: input.providerSubject,
      provider_email: providerEmail.length > 0 ? providerEmail : null,
      display_name: input.displayName,
      role_name: input.roleName,
      permission_names: input.permissionNames,
      mfa_enrolled: input.mfaEnrolled,
      reason_text: input.reasonText,
    }),
  }, parseLifecycle, true);
}

async function transition(
  path: string,
  input: StaffAccountTransitionInput | ActivateStaffAccountInput,
): Promise<StaffAccountResult<StaffAccountLifecycleResult>> {
  return request(path, {
    method: 'POST',
    headers: { Accept: 'application/json', 'Content-Type': 'application/json', 'Idempotency-Key': input.commandId },
    body: JSON.stringify({
      expected_version: input.expectedVersion,
      reason_text: input.reasonText,
      ...('mfaEnrolled' in input ? { mfa_enrolled: input.mfaEnrolled } : {}),
    }),
  }, parseLifecycle, true);
}

export const activateStaffAccount = (input: ActivateStaffAccountInput) =>
  transition(`/staff-accounts/${input.staffId}/activate`, input);
export const updateStaffAccountGoogleEmail = (input: UpdateStaffAccountGoogleEmailInput) =>
  request(`/staff-accounts/${input.staffId}/google-email`, {
    method: 'POST',
    headers: { Accept: 'application/json', 'Content-Type': 'application/json', 'Idempotency-Key': input.commandId },
    body: JSON.stringify({
      expected_version: input.expectedVersion,
      provider_email: input.providerEmail,
      reason_text: input.reasonText,
    }),
  }, parseLifecycle, true);
export const suspendStaffAccount = (input: StaffAccountTransitionInput) =>
  transition(`/staff-accounts/${input.staffId}/suspend`, input);
export const deprovisionStaffAccount = (input: StaffAccountTransitionInput) =>
  transition(`/staff-accounts/${input.staffId}/deprovision`, input);
export const recordRecoveryEvidence = (input: StaffAccountTransitionInput) =>
  transition(`/staff-accounts/${input.staffId}/recovery-evidence`, input);
export const recordSessionRevocationEvidence = (input: StaffAccountTransitionInput) =>
  transition(`/staff-accounts/${input.staffId}/session-revocations`, input);

export async function listStaffDelegations(staffId: string): Promise<StaffAccountResult<StaffDelegation[]>> {
  return request(`/staff-accounts/${staffId}/delegations`, { method: 'GET', headers: { Accept: 'application/json' } }, (value) => {
    if (!object(value) || !Array.isArray(value.items) || value.items.length > 50) return null;
    const items = value.items.map(parseDelegation);
    if (items.some((item) => item === null)) return null;
    return items as StaffDelegation[];
  });
}

export async function grantStaffDelegation(input: GrantStaffDelegationInput): Promise<StaffAccountResult<StaffDelegationResult>> {
  return request(`/staff-accounts/${input.staffId}/delegations`, {
    method: 'POST',
    headers: { Accept: 'application/json', 'Content-Type': 'application/json', 'Idempotency-Key': input.commandId },
    body: JSON.stringify({
      permission_name: input.permissionName,
      scope_kind: 'global',
      expires_at: input.expiresAt,
      reason_text: input.reasonText,
    }),
  }, parseDelegationCommand, true);
}

export async function revokeStaffDelegation(input: RevokeStaffDelegationInput): Promise<StaffAccountResult<StaffDelegationResult>> {
  return request(`/staff-accounts/${input.staffId}/delegations/${input.delegationId}/revoke`, {
    method: 'POST',
    headers: { Accept: 'application/json', 'Content-Type': 'application/json', 'Idempotency-Key': input.commandId },
    body: JSON.stringify({ reason_text: input.reasonText }),
  }, parseDelegationCommand, true);
}
