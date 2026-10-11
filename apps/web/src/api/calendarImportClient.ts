import { staffApiFetch } from '../auth/staffAuthSession';

export type CalendarImportFailureKind =
  | 'forbidden'
  | 'validation'
  | 'not_found'
  | 'stale'
  | 'unavailable'
  | 'unexpected';

export type CalendarImportResult<T> =
  | { ok: true; value: T }
  | { ok: false; failure: { kind: CalendarImportFailureKind } };

export type StaffCalendarConnection = {
  connectionId: string;
  staffId: string;
  providerName: 'google_calendar';
  calendarAlias: string;
  grantedScopes: string[];
  connectionStatus: 'authorization_required' | 'connected' | 'disconnected' | 'unavailable';
  connectedAt: string | null;
  disconnectedAt: string | null;
  lastSyncStatus: 'never_synced' | 'ready' | 'failed' | 'configuration_required';
  lastSyncError: string | null;
  updatedAt: string;
  version: number;
};

export type ExternalCalendarImport = {
  importId: string;
  connectionId: string;
  providerEventUpdatedAt: string;
  eventTitle: string;
  startsAt: string;
  endsAt: string;
  timeZone: string;
  locationReview: string | null;
  importStatus:
    | 'candidate'
    | 'ignored'
    | 'marked_existing'
    | 'linked'
    | 'draft_started'
    | 'superseded'
    | 'unavailable';
  linkedEntityType: string | null;
  linkedEntityId: string | null;
  updatedAt: string;
  version: number;
};

export type CalendarImportSummary = {
  connection: StaffCalendarConnection | null;
  candidates: ExternalCalendarImport[];
  oauthConfigurationRequired: boolean;
  oauthConnectAvailable: boolean;
};

export type GoogleCalendarOAuthStart = {
  authorizationUrl: string;
};

export type CalendarImportCommandResponse = {
  candidate: ExternalCalendarImport;
  eventType:
    | 'external_calendar.candidate_imported'
    | 'external_calendar.candidate_deduplicated'
    | 'external_calendar.candidate_ignored'
    | 'external_calendar.candidate_marked_existing';
  resultVersion: number;
  replayed: boolean;
};

export type CalendarImportDisposition = 'ignored' | 'marked_existing';

const uuid = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
const connectionStatuses = new Set<StaffCalendarConnection['connectionStatus']>([
  'authorization_required',
  'connected',
  'disconnected',
  'unavailable',
]);
const syncStatuses = new Set<StaffCalendarConnection['lastSyncStatus']>([
  'never_synced',
  'ready',
  'failed',
  'configuration_required',
]);
const importStatuses = new Set<ExternalCalendarImport['importStatus']>([
  'candidate',
  'ignored',
  'marked_existing',
  'linked',
  'draft_started',
  'superseded',
  'unavailable',
]);
const commandEvents = new Set<CalendarImportCommandResponse['eventType']>([
  'external_calendar.candidate_imported',
  'external_calendar.candidate_deduplicated',
  'external_calendar.candidate_ignored',
  'external_calendar.candidate_marked_existing',
]);

function object(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

function uuidText(value: unknown): value is string {
  return typeof value === 'string' && uuid.test(value.trim());
}

function text(value: unknown, max = 512): value is string {
  return typeof value === 'string' && value.trim().length > 0 && Array.from(value).length <= max;
}

function nullableText(value: unknown, max = 512): value is string | null {
  return value === null || text(value, max);
}

function timestamp(value: unknown): value is string {
  return typeof value === 'string' && !Number.isNaN(Date.parse(value));
}

function positive(value: unknown): value is number {
  return Number.isSafeInteger(value) && Number(value) > 0;
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

function failure(status: number, type: string | null): CalendarImportResult<never> {
  if (type === 'https://golden-rose.local/problems/forbidden' || status === 403) {
    return { ok: false, failure: { kind: 'forbidden' } };
  }
  if (type === 'https://golden-rose.local/problems/calendar-import-not-found' || status === 404) {
    return { ok: false, failure: { kind: 'not_found' } };
  }
  if (type === 'https://golden-rose.local/problems/calendar-import-version-conflict' || status === 412) {
    return { ok: false, failure: { kind: 'stale' } };
  }
  if (type === 'https://golden-rose.local/problems/calendar-import-invalid' || status === 422) {
    return { ok: false, failure: { kind: 'validation' } };
  }
  if (type === 'https://golden-rose.local/problems/service-unavailable' || status >= 500) {
    return { ok: false, failure: { kind: 'unavailable' } };
  }
  return { ok: false, failure: { kind: 'unexpected' } };
}

function parseConnection(value: unknown): StaffCalendarConnection | null {
  if (!object(value)) return null;
  if (!uuidText(value.connection_id) || !uuidText(value.staff_id)) return null;
  if (value.provider_name !== 'google_calendar') return null;
  if (!text(value.calendar_alias, 160)) return null;
  if (!Array.isArray(value.granted_scopes) || !value.granted_scopes.every((scope) => text(scope, 200))) return null;
  if (!connectionStatuses.has(value.connection_status as StaffCalendarConnection['connectionStatus'])) return null;
  if (value.connected_at !== null && !timestamp(value.connected_at)) return null;
  if (value.disconnected_at !== null && !timestamp(value.disconnected_at)) return null;
  if (!syncStatuses.has(value.last_sync_status as StaffCalendarConnection['lastSyncStatus'])) return null;
  if (!nullableText(value.last_sync_error, 80) || !timestamp(value.updated_at) || !positive(value.version)) return null;
  return {
    connectionId: value.connection_id.trim(),
    staffId: value.staff_id.trim(),
    providerName: 'google_calendar',
    calendarAlias: value.calendar_alias,
    grantedScopes: value.granted_scopes.map((scope) => scope.trim()),
    connectionStatus: value.connection_status as StaffCalendarConnection['connectionStatus'],
    connectedAt: value.connected_at,
    disconnectedAt: value.disconnected_at,
    lastSyncStatus: value.last_sync_status as StaffCalendarConnection['lastSyncStatus'],
    lastSyncError: value.last_sync_error,
    updatedAt: value.updated_at,
    version: value.version,
  };
}

function parseImport(value: unknown): ExternalCalendarImport | null {
  if (!object(value)) return null;
  if (!uuidText(value.import_id) || !uuidText(value.connection_id)) return null;
  if (!timestamp(value.provider_event_updated_at)) return null;
  if (!text(value.event_title, 200)) return null;
  if (!timestamp(value.starts_at) || !timestamp(value.ends_at)) return null;
  if (Date.parse(value.starts_at) >= Date.parse(value.ends_at)) return null;
  if (!text(value.time_zone, 64) || !nullableText(value.location_review, 200)) return null;
  if (!importStatuses.has(value.import_status as ExternalCalendarImport['importStatus'])) return null;
  if (!nullableText(value.linked_entity_type, 40)) return null;
  if (value.linked_entity_id !== null && !uuidText(value.linked_entity_id)) return null;
  if (!timestamp(value.updated_at) || !positive(value.version)) return null;
  return {
    importId: value.import_id.trim(),
    connectionId: value.connection_id.trim(),
    providerEventUpdatedAt: value.provider_event_updated_at,
    eventTitle: value.event_title,
    startsAt: value.starts_at,
    endsAt: value.ends_at,
    timeZone: value.time_zone,
    locationReview: value.location_review,
    importStatus: value.import_status as ExternalCalendarImport['importStatus'],
    linkedEntityType: value.linked_entity_type,
    linkedEntityId: value.linked_entity_id === null ? null : value.linked_entity_id.trim(),
    updatedAt: value.updated_at,
    version: value.version,
  };
}

function parseSummary(value: unknown): CalendarImportSummary | null {
  if (!object(value)) return null;
  const connection = value.connection === null ? null : parseConnection(value.connection);
  if (value.connection !== null && connection === null) return null;
  if (!Array.isArray(value.candidates)) return null;
  const candidates = value.candidates.map(parseImport);
  if (candidates.some((candidate) => candidate === null)) return null;
  if (typeof value.oauth_configuration_required !== 'boolean') return null;
  if (typeof value.oauth_connect_available !== 'boolean') return null;
  return {
    connection,
    candidates: candidates.filter((candidate): candidate is ExternalCalendarImport => candidate !== null),
    oauthConfigurationRequired: value.oauth_configuration_required,
    oauthConnectAvailable: value.oauth_connect_available,
  };
}

function parseOAuthStart(value: unknown): GoogleCalendarOAuthStart | null {
  if (!object(value)) return null;
  if (typeof value.authorization_url !== 'string') return null;
  let parsed: URL;
  try {
    parsed = new URL(value.authorization_url);
  } catch {
    return null;
  }
  if (parsed.protocol !== 'https:' || parsed.hostname !== 'accounts.google.com') return null;
  return { authorizationUrl: parsed.toString() };
}

function parseCommand(value: unknown): CalendarImportCommandResponse | null {
  if (!object(value)) return null;
  const candidate = parseImport(value.candidate);
  if (candidate === null) return null;
  if (!commandEvents.has(value.event_type as CalendarImportCommandResponse['eventType'])) return null;
  if (!positive(value.result_version) || typeof value.replayed !== 'boolean') return null;
  return {
    candidate,
    eventType: value.event_type as CalendarImportCommandResponse['eventType'],
    resultVersion: value.result_version,
    replayed: value.replayed,
  };
}

async function readCalendarImportResponse<T>(
  response: Response,
  parser: (value: unknown) => T | null,
): Promise<CalendarImportResult<T>> {
  if (response.status !== 200) {
    if (!isJson(response)) {
      await cancelBody(response);
      return failure(response.status, null);
    }
    try {
      return failure(response.status, parseProblemType(await response.json()));
    } catch {
      return failure(response.status, null);
    }
  }
  if (!isJson(response)) {
    await cancelBody(response);
    return { ok: false, failure: { kind: 'unexpected' } };
  }
  try {
    const parsed = parser(await response.json());
    return parsed === null ? { ok: false, failure: { kind: 'unexpected' } } : { ok: true, value: parsed };
  } catch {
    return { ok: false, failure: { kind: 'unexpected' } };
  }
}

export async function getCalendarImportSummary(): Promise<CalendarImportResult<CalendarImportSummary>> {
  let response: Response;
  try {
    response = await staffApiFetch('/api/staff/v1/calendar-imports', {
      method: 'GET',
      headers: { Accept: 'application/json' },
      cache: 'no-store',
      credentials: 'same-origin',
      mode: 'same-origin',
      redirect: 'error',
      referrerPolicy: 'no-referrer',
    });
  } catch {
    return { ok: false, failure: { kind: 'unavailable' } };
  }
  return readCalendarImportResponse(response, parseSummary);
}

export async function startGoogleCalendarOAuth(): Promise<CalendarImportResult<GoogleCalendarOAuthStart>> {
  let response: Response;
  try {
    response = await staffApiFetch('/api/staff/v1/calendar-imports/oauth/start', {
      method: 'POST',
      headers: { Accept: 'application/json' },
      cache: 'no-store',
      credentials: 'same-origin',
      mode: 'same-origin',
      redirect: 'error',
      referrerPolicy: 'no-referrer',
    });
  } catch {
    return { ok: false, failure: { kind: 'unavailable' } };
  }
  return readCalendarImportResponse(response, parseOAuthStart);
}

export async function disposeExternalCalendarCandidate(
  importId: string,
  expectedVersion: number,
  disposition: CalendarImportDisposition,
  reasonText: string,
  commandId: string,
): Promise<CalendarImportResult<CalendarImportCommandResponse>> {
  const action = disposition === 'ignored' ? 'ignore' : 'mark-existing';
  let response: Response;
  try {
    response = await staffApiFetch(`/api/staff/v1/calendar-imports/candidates/${importId}/${action}`, {
      method: 'POST',
      headers: {
        Accept: 'application/json',
        'Content-Type': 'application/json',
        'Idempotency-Key': commandId,
      },
      cache: 'no-store',
      credentials: 'same-origin',
      mode: 'same-origin',
      redirect: 'error',
      referrerPolicy: 'no-referrer',
      body: JSON.stringify({
        expected_version: expectedVersion,
        reason_text: reasonText,
      }),
    });
  } catch {
    return { ok: false, failure: { kind: 'unavailable' } };
  }
  return readCalendarImportResponse(response, parseCommand);
}
