export type StaffAccountRole = 'owner' | 'delegated_manager' | 'operations_staff' | 'platform_administrator';
export type StaffAccountStatus = 'active' | 'suspended' | 'deprovisioned';
export type StaffAccountEvent =
  | 'staff_account.created'
  | 'staff_account.activated'
  | 'staff_account.suspended'
  | 'staff_account.deprovisioned'
  | 'staff_account.recovery_recorded'
  | 'staff_account.sessions_revoked';

export type StaffAccount = {
  staffId: string;
  providerSubject: string;
  displayName: string;
  roleName: StaffAccountRole;
  lifecycleStatus: StaffAccountStatus;
  mfaEnrolled: boolean;
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

export type StaffAccountFailureKind =
  | 'validation'
  | 'forbidden'
  | 'not_found'
  | 'stale'
  | 'unavailable'
  | 'unknown_outcome'
  | 'unexpected';

export type StaffAccountResult<T> = { ok: true; value: T } | { ok: false; failure: { kind: StaffAccountFailureKind } };

export type CreateStaffAccountInput = {
  providerSubject: string;
  displayName: string;
  roleName: StaffAccountRole;
  permissionNames: string[];
  mfaEnrolled: boolean;
  reasonText: string;
  commandId: string;
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

const uuid = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
const roles = new Set<StaffAccountRole>(['owner', 'delegated_manager', 'operations_staff', 'platform_administrator']);
const statuses = new Set<StaffAccountStatus>(['active', 'suspended', 'deprovisioned']);
const events = new Set<StaffAccountEvent>([
  'staff_account.created',
  'staff_account.activated',
  'staff_account.suspended',
  'staff_account.deprovisioned',
  'staff_account.recovery_recorded',
  'staff_account.sessions_revoked',
]);

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
  return /^application\/json(?:\s*;.*)?$/i.test(response.headers.get('Content-Type') ?? '');
}

async function cancelBody(response: Response) {
  try {
    await response.body?.cancel();
  } catch {
    // Best-effort cleanup only.
  }
}

function failure(status: number, command = false): StaffAccountResult<never> {
  if (status === 400 || status === 422) return { ok: false, failure: { kind: 'validation' } };
  if (status === 403) return { ok: false, failure: { kind: 'forbidden' } };
  if (status === 404) return { ok: false, failure: { kind: 'not_found' } };
  if (status === 412) return { ok: false, failure: { kind: 'stale' } };
  if (status === 503) return { ok: false, failure: { kind: 'unavailable' } };
  return { ok: false, failure: { kind: command ? 'unknown_outcome' : 'unexpected' } };
}

function parseAccount(value: unknown): StaffAccount | null {
  if (!object(value)) return null;
  const keys = new Set([
    'staff_id',
    'provider_subject',
    'display_name',
    'role_name',
    'lifecycle_status',
    'mfa_enrolled',
    'created_at',
    'created_by',
    'updated_at',
    'updated_by',
    'version',
  ]);
  if (Object.keys(value).some((key) => !keys.has(key))) return null;
  if (typeof value.staff_id !== 'string' || !uuid.test(value.staff_id)) return null;
  if (!text(value.provider_subject, 256) || !text(value.display_name, 160)) return null;
  if (typeof value.role_name !== 'string' || !roles.has(value.role_name as StaffAccountRole)) return null;
  if (typeof value.lifecycle_status !== 'string' || !statuses.has(value.lifecycle_status as StaffAccountStatus)) return null;
  if (typeof value.mfa_enrolled !== 'boolean') return null;
  if (!timestamp(value.created_at) || !timestamp(value.updated_at)) return null;
  if (typeof value.created_by !== 'string' || !uuid.test(value.created_by)) return null;
  if (typeof value.updated_by !== 'string' || !uuid.test(value.updated_by)) return null;
  if (!positive(value.version)) return null;
  return {
    staffId: value.staff_id,
    providerSubject: value.provider_subject,
    displayName: value.display_name,
    roleName: value.role_name as StaffAccountRole,
    lifecycleStatus: value.lifecycle_status as StaffAccountStatus,
    mfaEnrolled: value.mfa_enrolled,
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

async function request<T>(
  path: string,
  init: RequestInit,
  validate: (value: unknown) => T | null,
  command = false,
): Promise<StaffAccountResult<T>> {
  let response: Response;
  try {
    response = await fetch(`/api/staff/v1${path}`, {
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
    await cancelBody(response);
    return failure(response.status, command);
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

export async function listStaffAccounts(): Promise<StaffAccountResult<StaffAccount[]>> {
  return request('/staff-accounts', { method: 'GET', headers: { Accept: 'application/json' } }, (value) => {
    if (!object(value) || !Array.isArray(value.items) || value.items.length > 50) return null;
    const items = value.items.map(parseAccount);
    if (items.some((item) => item === null)) return null;
    return items as StaffAccount[];
  });
}

export async function createStaffAccount(input: CreateStaffAccountInput): Promise<StaffAccountResult<StaffAccountLifecycleResult>> {
  return request('/staff-accounts', {
    method: 'POST',
    headers: { Accept: 'application/json', 'Content-Type': 'application/json', 'Idempotency-Key': input.commandId },
    body: JSON.stringify({
      provider_subject: input.providerSubject,
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
export const suspendStaffAccount = (input: StaffAccountTransitionInput) =>
  transition(`/staff-accounts/${input.staffId}/suspend`, input);
export const deprovisionStaffAccount = (input: StaffAccountTransitionInput) =>
  transition(`/staff-accounts/${input.staffId}/deprovision`, input);
export const recordRecoveryEvidence = (input: StaffAccountTransitionInput) =>
  transition(`/staff-accounts/${input.staffId}/recovery-evidence`, input);
export const recordSessionRevocationEvidence = (input: StaffAccountTransitionInput) =>
  transition(`/staff-accounts/${input.staffId}/session-revocations`, input);
