import type {
  ApiResult,
  CreateEmployerInput,
  EmployerDetail,
  EmployerSearchResult,
  EmployerSummary,
  SearchEmployersInput,
} from './employerContracts';

const JSON_HEADERS = {
  Accept: 'application/json',
  'Content-Type': 'application/json',
} as const;

const UUID_PATTERN = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

function hasControlCharacters(value: string) {
  return /[\p{Cc}\p{Cf}\p{Cs}\p{Co}\p{Cn}]/u.test(value);
}

function isValidDisplayName(value: unknown): value is string {
  if (typeof value !== 'string') {
    return false;
  }
  const normalized = value.normalize('NFC');
  return normalized === value && value.trim().length > 0 && Array.from(value).length <= 200 && !hasControlCharacters(value);
}

function isValidUuid(value: unknown): value is string {
  return typeof value === 'string' && UUID_PATTERN.test(value);
}

function isValidTimestamp(value: unknown): value is string {
  if (typeof value !== 'string') {
    return false;
  }
  const match = value.match(
    /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(?:\.(\d+))?(Z|[+-]\d{2}:\d{2})$/,
  );
  if (!match) {
    return false;
  }
  const [, year, month, day, hour, minute, second] = match;
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return false;
  }
  const isoLike = parsed.toISOString();
  return (
    isoLike.slice(0, 4) === year &&
    isoLike.slice(5, 7) === month &&
    isoLike.slice(8, 10) === day &&
    isoLike.slice(11, 13) === hour &&
    isoLike.slice(14, 16) === minute &&
    isoLike.slice(17, 19) === second
  );
}

function isJsonResponse(response: Response) {
  const contentType = response.headers.get('Content-Type');
  return contentType !== null && /^application\/json(?:\s*;.*)?$/i.test(contentType);
}

function isAbortError(error: unknown) {
  return (
    (typeof DOMException !== 'undefined' && error instanceof DOMException && error.name === 'AbortError') ||
    (error instanceof Error && error.name === 'AbortError')
  );
}

async function cancelUnreadBody(response: { body?: { cancel?: () => Promise<void> | void } | null }) {
  try {
    await response.body?.cancel?.();
  } catch {
    // swallow cancellation failures into bounded classifications
  }
}

function unexpected() {
  return { ok: false as const, failure: { kind: 'unexpected' as const } };
}

function unavailable() {
  return { ok: false as const, failure: { kind: 'unavailable' as const } };
}

function validation() {
  return { ok: false as const, failure: { kind: 'validation' as const } };
}

function forbidden() {
  return { ok: false as const, failure: { kind: 'forbidden' as const } };
}

function conflict() {
  return { ok: false as const, failure: { kind: 'conflict' as const } };
}

function unknownOutcome() {
  return { ok: false as const, failure: { kind: 'unknown_outcome' as const } };
}

function parseEmployerSummary(value: unknown): EmployerSummary | null {
  if (typeof value !== 'object' || value === null) {
    return null;
  }
  const candidate = value as Record<string, unknown>;
  if (!isValidUuid(candidate.employer_id)) return null;
  if (candidate.employer_type !== 'household' && candidate.employer_type !== 'business') return null;
  if (!isValidDisplayName(candidate.display_name)) return null;
  if (candidate.lifecycle_status !== 'draft') return null;
  if (!Number.isSafeInteger(candidate.version) || (candidate.version as number) <= 0) return null;
  if (!isValidTimestamp(candidate.received_at)) return null;
  return {
    employerId: candidate.employer_id,
    employerType: candidate.employer_type,
    displayName: candidate.display_name,
    lifecycleStatus: candidate.lifecycle_status,
  };
}

function parseSearchResult(value: unknown): EmployerSearchResult | null {
  if (typeof value !== 'object' || value === null) {
    return null;
  }
  const candidate = value as Record<string, unknown>;
  if (!Array.isArray(candidate.items) || candidate.items.length > 25) {
    return null;
  }
  const items = candidate.items.map(parseEmployerSummary);
  if (items.some((item) => item === null)) {
    return null;
  }
  const nextCursor = candidate.next_cursor;
  if (!(nextCursor === null || (typeof nextCursor === 'string' && nextCursor.length > 0 && nextCursor.length <= 512))) {
    return null;
  }
  return { items: items as EmployerSummary[], nextCursor };
}

export async function searchEmployers(input: SearchEmployersInput): Promise<ApiResult<EmployerSearchResult> | null> {
  let response: Response;
  try {
    response = await fetch('/api/staff/v1/employers/search', {
      method: 'POST',
      headers: JSON_HEADERS,
      body: JSON.stringify({
        display_name_query: input.displayNameQuery,
        ...(input.employerType ? { employer_type: input.employerType } : {}),
        page_size: 25,
        cursor: input.cursor ?? null,
      }),
      cache: 'no-store',
      credentials: 'same-origin',
      mode: 'same-origin',
      redirect: 'error',
      referrerPolicy: 'no-referrer',
      signal: input.signal,
    });
  } catch (error) {
    if (isAbortError(error)) {
      return null;
    }
    return unavailable();
  }

  if (response.status !== 200) {
    await cancelUnreadBody(response);
    if (response.status === 400 || response.status === 422) return validation();
    if (response.status === 403) return forbidden();
    if (response.status === 409) return conflict();
    if (response.status === 503) return unavailable();
    return unexpected();
  }
  if (!isJsonResponse(response)) {
    await cancelUnreadBody(response);
    return unexpected();
  }

  try {
    const payload: unknown = await response.json();
    const parsed = parseSearchResult(payload);
    return parsed ? { ok: true, value: parsed } : unexpected();
  } catch {
    return unexpected();
  }
}

function parseEmployerDetail(value: unknown, requestedId: string): EmployerDetail | null {
  const summary = parseEmployerSummary(value);
  if (summary === null || summary.employerId !== requestedId) {
    return null;
  }
  const candidate = value as Record<string, unknown>;
  if (candidate.source_channel !== 'staff_entry') return null;
  if (!isValidTimestamp(candidate.created_at)) return null;
  return {
    ...summary,
    sourceChannel: candidate.source_channel,
  };
}

export async function getEmployer(
  employerId: string,
  options?: {
    signal?: AbortSignal;
  },
): Promise<ApiResult<EmployerDetail> | null> {
  if (!isValidUuid(employerId)) {
    return validation();
  }

  let response: Response;
  try {
    response = await fetch(`/api/staff/v1/employers/${employerId}`, {
      method: 'GET',
      headers: {
        Accept: 'application/json',
      },
      cache: 'no-store',
      credentials: 'same-origin',
      mode: 'same-origin',
      redirect: 'error',
      referrerPolicy: 'no-referrer',
      signal: options?.signal,
    });
  } catch (error) {
    if (isAbortError(error)) {
      return null;
    }
    return unavailable();
  }

  if (response.status !== 200) {
    await cancelUnreadBody(response);
    if (response.status === 400 || response.status === 422) return validation();
    if (response.status === 403) return forbidden();
    if (response.status === 404) return { ok: false, failure: { kind: 'not_found' } };
    if (response.status === 409) return conflict();
    if (response.status === 503) return unavailable();
    return unexpected();
  }
  if (!isJsonResponse(response)) {
    await cancelUnreadBody(response);
    return unexpected();
  }

  try {
    const payload: unknown = await response.json();
    const parsed = parseEmployerDetail(payload, employerId);
    return parsed ? { ok: true, value: parsed } : unexpected();
  } catch {
    return unexpected();
  }
}

export async function createEmployer(_input: CreateEmployerInput): Promise<ApiResult<EmployerDetail>> {
  let response: Response;
  try {
    response = await fetch('/api/staff/v1/employers', {
      method: 'POST',
      headers: {
        Accept: 'application/json',
        'Content-Type': 'application/json',
        'Idempotency-Key': _input.commandId,
      },
      body: JSON.stringify({
        employer_type: _input.employerType,
        display_name: _input.displayName,
      }),
      cache: 'no-store',
      credentials: 'same-origin',
      mode: 'same-origin',
      redirect: 'error',
      referrerPolicy: 'no-referrer',
    });
  } catch {
    return unknownOutcome();
  }

  if (response.status !== 201) {
    await cancelUnreadBody(response);
    if (response.status === 400 || response.status === 422) return validation();
    if (response.status === 403) return forbidden();
    if (response.status === 409) return conflict();
    return unknownOutcome();
  }
  if (!isJsonResponse(response)) {
    await cancelUnreadBody(response);
    return unknownOutcome();
  }

  try {
    const payload: unknown = await response.json();
    if (typeof payload !== 'object' || payload === null) {
      return unknownOutcome();
    }
    const candidate = payload as Record<string, unknown>;
    const requestedId = typeof candidate.employer_id === 'string' ? candidate.employer_id : '';
    const detail = parseEmployerDetail(payload, requestedId);
    return detail ? { ok: true, value: detail } : unknownOutcome();
  } catch {
    return unknownOutcome();
  }
}
