export type ShiftNeedFailureKind =
  | 'validation'
  | 'forbidden'
  | 'not_found'
  | 'stale'
  | 'unavailable'
  | 'unknown_outcome'
  | 'unexpected';

export type ShiftNeedResult<T> = { ok: true; value: T } | { ok: false; failure: { kind: ShiftNeedFailureKind } };

export type ShiftNeed = {
  shiftNeedId: string;
  employerId: string;
  staffingRequestId: string;
  requestVersionAtCreation: number;
  shiftStatus: 'draft' | 'pending_review';
  roleTitle: string;
  workerCount: number;
  startsAt: string;
  endsAt: string;
  timeZone: string;
  notes: string | null;
  version: number;
  createdAt: string;
  updatedAt: string;
};

export type ShiftNeedCommandResult = {
  commandId: string;
  resultRecordVersion: number;
  eventType: 'shift_need.created' | 'shift_need.submitted_for_review';
  current: ShiftNeed;
};

export type StaffingRequestDetail = {
  staffingRequestId: string;
  employerId: string;
  version: number;
  requestStatus: 'draft' | 'pending_review';
};

export type StaffingRequestCommandResult = {
  commandId: string;
  resultRecordVersion: number;
  eventType: 'staffing_request.submitted_for_review';
  current: StaffingRequestDetail;
};

export type CreateShiftNeedInput = {
  employerId: string;
  requestId: string;
  expectedRequestVersion: number;
  roleTitle: string;
  workerCount: number;
  startsAt: string;
  endsAt: string;
  timeZone: string;
  reasonText: string;
  notes: string | null;
  commandId: string;
};

export type SubmitForReviewInput = {
  employerId: string;
  requestId: string;
  expectedVersion: number;
  reasonText: string;
  commandId: string;
};

export type SubmitShiftNeedForReviewInput = SubmitForReviewInput & {
  shiftNeedId: string;
};

const uuid = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
function object(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}
function text(value: unknown, max = 1000): value is string {
  return typeof value === 'string' && value.trim().length > 0 && Array.from(value).length <= max;
}
function positive(value: unknown, max = 2147483647): value is number {
  return Number.isSafeInteger(value) && Number(value) >= 1 && Number(value) <= max;
}
function timestamp(value: unknown): value is string {
  return typeof value === 'string' && !Number.isNaN(Date.parse(value));
}
function isJson(response: Response) {
  return /^application\/(?:json|problem\+json)(?:\s*;.*)?$/i.test(response.headers.get('Content-Type') ?? '');
}
async function cancelBody(response: Response) {
  try { await response.body?.cancel(); } catch { /* best effort */ }
}
function failure(status: number, command = false): ShiftNeedResult<never> {
  if (status === 400 || status === 422) return { ok: false, failure: { kind: 'validation' } };
  if (status === 403) return { ok: false, failure: { kind: 'forbidden' } };
  if (status === 404) return { ok: false, failure: { kind: 'not_found' } };
  if (status === 412) return { ok: false, failure: { kind: 'stale' } };
  if (status === 503) return { ok: false, failure: { kind: 'unavailable' } };
  return { ok: false, failure: { kind: command ? 'unknown_outcome' : 'unexpected' } };
}
function parseShiftNeed(value: unknown): ShiftNeed | null {
  if (!object(value)) return null;
  const keys = new Set([
    'shift_need_id',
    'employer_id',
    'staffing_request_id',
    'request_version_at_creation',
    'shift_status',
    'role_title',
    'worker_count',
    'starts_at',
    'ends_at',
    'time_zone',
    'notes',
    'version',
    'created_at',
    'updated_at',
  ]);
  if (Object.keys(value).some((key) => !keys.has(key))) return null;
  if (typeof value.shift_need_id !== 'string' || !uuid.test(value.shift_need_id)) return null;
  if (typeof value.employer_id !== 'string' || !uuid.test(value.employer_id)) return null;
  if (typeof value.staffing_request_id !== 'string' || !uuid.test(value.staffing_request_id)) return null;
  if (!positive(value.request_version_at_creation) || !['draft', 'pending_review'].includes(String(value.shift_status))) return null;
  if (!text(value.role_title, 200) || !positive(value.worker_count, 1000)) return null;
  if (!timestamp(value.starts_at) || !timestamp(value.ends_at) || Date.parse(value.starts_at) >= Date.parse(value.ends_at)) return null;
  if (!text(value.time_zone, 100)) return null;
  if (value.notes !== null && (typeof value.notes !== 'string' || Array.from(value.notes).length > 1000)) return null;
  if (!positive(value.version) || !timestamp(value.created_at) || !timestamp(value.updated_at)) return null;
  return {
    shiftNeedId: value.shift_need_id,
    employerId: value.employer_id,
    staffingRequestId: value.staffing_request_id,
    requestVersionAtCreation: value.request_version_at_creation,
    shiftStatus: value.shift_status as ShiftNeed['shiftStatus'],
    roleTitle: value.role_title,
    workerCount: value.worker_count,
    startsAt: value.starts_at,
    endsAt: value.ends_at,
    timeZone: value.time_zone,
    notes: value.notes,
    version: value.version,
    createdAt: value.created_at,
    updatedAt: value.updated_at,
  };
}
function parseCommand(value: unknown): ShiftNeedCommandResult | null {
  if (!object(value)) return null;
  const current = parseShiftNeed(value.current);
  if (typeof value.command_id !== 'string' || !uuid.test(value.command_id) || current === null) return null;
  if (!['shift_need.created', 'shift_need.submitted_for_review'].includes(String(value.event_type)) || value.result_record_version !== current.version) return null;
  return {
    commandId: value.command_id,
    resultRecordVersion: value.result_record_version,
    eventType: value.event_type as ShiftNeedCommandResult['eventType'],
    current,
  };
}
function parseRequestCommand(value: unknown): StaffingRequestCommandResult | null {
  if (!object(value) || !object(value.current)) return null;
  const current = value.current;
  if (typeof value.command_id !== 'string' || !uuid.test(value.command_id)) return null;
  if (value.event_type !== 'staffing_request.submitted_for_review') return null;
  if (typeof current.staffing_request_id !== 'string' || !uuid.test(current.staffing_request_id)) return null;
  if (typeof current.employer_id !== 'string' || !uuid.test(current.employer_id)) return null;
  if (!positive(current.version) || !['draft', 'pending_review'].includes(String(current.request_status))) return null;
  if (value.result_record_version !== current.version) return null;
  return {
    commandId: value.command_id,
    resultRecordVersion: value.result_record_version,
    eventType: 'staffing_request.submitted_for_review',
    current: {
      staffingRequestId: current.staffing_request_id,
      employerId: current.employer_id,
      version: current.version,
      requestStatus: current.request_status as StaffingRequestDetail['requestStatus'],
    },
  };
}
async function request<T>(path: string, init: RequestInit, validate: (value: unknown) => T | null, command = false): Promise<ShiftNeedResult<T>> {
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
    if (!isJson(response)) await cancelBody(response);
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
    if (command && object(payload) && response.headers.get('Idempotency-Result-Version') !== String(payload.result_record_version)) {
      return { ok: false, failure: { kind: 'unknown_outcome' } };
    }
    return { ok: true, value: parsed };
  } catch {
    return { ok: false, failure: { kind: command ? 'unknown_outcome' : 'unexpected' } };
  }
}
export async function listShiftNeeds(employerId: string, requestId: string): Promise<ShiftNeedResult<ShiftNeed[]>> {
  return request(`/employers/${employerId}/requests/${requestId}/shift-needs/query`, {
    method: 'POST',
    headers: { Accept: 'application/json', 'Content-Type': 'application/json' },
    body: JSON.stringify({ page_size: 50 }),
  }, (value) => {
    if (!object(value) || !Array.isArray(value.items) || value.items.length > 50) return null;
    const items = value.items.map(parseShiftNeed);
    if (items.some((item) => item === null)) return null;
    return items as ShiftNeed[];
  });
}
export async function createShiftNeed(input: CreateShiftNeedInput): Promise<ShiftNeedResult<ShiftNeedCommandResult>> {
  return request(`/employers/${input.employerId}/requests/${input.requestId}/shift-needs`, {
    method: 'POST',
    headers: { Accept: 'application/json', 'Content-Type': 'application/json', 'Idempotency-Key': input.commandId },
    body: JSON.stringify({
      expected_request_version: input.expectedRequestVersion,
      role_title: input.roleTitle,
      worker_count: input.workerCount,
      starts_at: input.startsAt,
      ends_at: input.endsAt,
      time_zone: input.timeZone,
      reason_text: input.reasonText,
      notes: input.notes,
    }),
  }, parseCommand, true);
}

export async function submitShiftNeedForReview(input: SubmitShiftNeedForReviewInput): Promise<ShiftNeedResult<ShiftNeedCommandResult>> {
  return request(`/employers/${input.employerId}/requests/${input.requestId}/shift-needs/${input.shiftNeedId}/submit-review`, {
    method: 'POST',
    headers: { Accept: 'application/json', 'Content-Type': 'application/json', 'Idempotency-Key': input.commandId },
    body: JSON.stringify({
      expected_version: input.expectedVersion,
      reason_text: input.reasonText,
    }),
  }, parseCommand, true);
}

export async function submitStaffingRequestForReview(input: SubmitForReviewInput): Promise<ShiftNeedResult<StaffingRequestCommandResult>> {
  return request(`/employers/${input.employerId}/requests/${input.requestId}/submit-review`, {
    method: 'POST',
    headers: { Accept: 'application/json', 'Content-Type': 'application/json', 'Idempotency-Key': input.commandId },
    body: JSON.stringify({
      expected_version: input.expectedVersion,
      reason_text: input.reasonText,
    }),
  }, parseRequestCommand, true);
}
