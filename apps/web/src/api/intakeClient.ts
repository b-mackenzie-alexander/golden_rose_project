import type {
  AddressDetail,
  AddressSection,
  DraftObject,
  IntakeCommandResult,
  IntakeDetail,
  IntakeKind,
  IntakeSummary,
  Result,
} from './intakeContracts';
import type { Command } from '../intakes/saveState';
const uuid = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
const object = (v: unknown): v is Record<string, unknown> =>
  !!v && typeof v === 'object' && !Array.isArray(v);
const positive = (v: unknown): v is number => Number.isSafeInteger(v) && Number(v) > 0;
// Reject unknown nested values before they can become a later full-section replacement.
function sectionObject(value: unknown, fields: readonly string[]): value is DraftObject {
  return (
    object(value) &&
    Object.entries(value).every(
      ([key, item]) =>
        fields.includes(key) && (item === null || ['string', 'number', 'boolean'].includes(typeof item)),
    )
  );
}
function content(value: unknown, kind: IntakeKind): value is DraftObject {
  if (!object(value)) return false;
  const basic =
    kind === 'worker'
      ? ['full_name', 'phone']
      : [
          'employer_type',
          'display_name',
          'representative_name',
          'phone',
          'role_title',
          'duties_summary',
          'worker_count',
        ];
  return Object.entries(value).every(([key, item]) => {
    if (basic.includes(key))
      return item === null || typeof item === 'string' || (key === 'worker_count' && positive(item));
    if (
      item === null &&
      (kind === 'worker' ? ['interests', 'availability'] : ['offer', 'schedule']).includes(key)
    )
      return true;
    if (kind === 'worker' && key === 'interests') return sectionObject(item, ['other_description']);
    if (kind === 'worker' && key === 'availability' && object(item)) {
      return Object.entries(item).every(([field, entry]) =>
        field === 'ranges'
          ? Array.isArray(entry) &&
            entry.length <= 28 &&
            entry.every((range) =>
              sectionObject(range, ['weekday', 'start_local', 'end_local', 'end_day_offset']),
            )
          : ['mode', 'time_zone', 'exception_note'].includes(field) &&
            (entry === null || typeof entry === 'string'),
      );
    }
    if (kind === 'employer' && key === 'schedule')
      return sectionObject(item, [
        'mode',
        'requested_start_date',
        'starts_at',
        'ends_at',
        'time_zone',
        'note',
      ]);
    if (kind === 'employer' && key === 'offer')
      return sectionObject(item, [
        'minimum',
        'maximum',
        'currency',
        'basis',
        'per_worker',
        'negotiable',
        'terms',
      ]);
    return false;
  });
}
function summary(v: unknown): v is IntakeSummary {
  return (
    object(v) &&
    typeof v.intake_id === 'string' &&
    uuid.test(v.intake_id) &&
    (v.kind === 'worker' || v.kind === 'employer') &&
    positive(v.version) &&
    v.lifecycle === 'draft' &&
    typeof v.complete === 'boolean' &&
    Array.isArray(v.missing_fields) &&
    v.missing_fields.every((x) => typeof x === 'string') &&
    v.review_status === 'unreviewed' &&
    typeof v.updated_at === 'string' &&
    (v.display_name === undefined || v.display_name === null || typeof v.display_name === 'string')
  );
}
function detail(v: unknown): v is IntakeDetail {
  return (
    object(v) &&
    summary(v.summary) &&
    positive(v.content_version) &&
    content(v.candidate, v.summary.kind) &&
    object(v.resolved) &&
    object(v.links) &&
    typeof v.dependency_stale === 'boolean'
  );
}
async function request<T>(
  path: string,
  body: DraftObject | undefined,
  validate: (value: unknown) => value is T,
  key?: string,
): Promise<Result<T>> {
  try {
    const response = await fetch(`/api/staff/v1${path}`, {
      method: body ? 'POST' : 'GET',
      headers: {
        Accept: 'application/json',
        ...(body ? { 'Content-Type': 'application/json' } : {}),
        ...(key ? { 'Idempotency-Key': key } : {}),
      },
      ...(body ? { body: JSON.stringify(body) } : {}),
      cache: 'no-store',
      credentials: 'same-origin',
      mode: 'same-origin',
      redirect: 'error',
      referrerPolicy: 'no-referrer',
    });
    if (response.status !== 200 && response.status !== 201) {
      await response.body?.cancel();
      return {
        ok: false,
        failure:
          response.status === 403
            ? 'forbidden'
            : response.status === 409
              ? 'conflict'
              : [400, 404, 413, 422].includes(response.status)
                ? 'failed'
                : key
                  ? 'unknown'
                  : 'failed',
      };
    }
    if (!/^application\/json(?:\s*;.*)?$/i.test(response.headers.get('Content-Type') ?? ''))
      return { ok: false, failure: key ? 'unknown' : 'failed' };
    const value: unknown = await response.json();
    if (!validate(value)) return { ok: false, failure: key ? 'unknown' : 'failed' };
    if (key) {
      const candidate = value as IntakeCommandResult;
      const replayed = response.headers.get('Idempotency-Replayed');
      const version = response.headers.get('Idempotency-Result-Version');
      if (
        !['true', 'false'].includes(replayed ?? '') ||
        version !== String(candidate.result_record_version) ||
        candidate.command_id !== key ||
        candidate.current.summary.version < candidate.result_record_version
      )
        return { ok: false, failure: 'unknown' };
    }
    return { ok: true, value };
  } catch {
    return { ok: false, failure: key ? 'unknown' : 'failed' };
  }
}
export const queryIntakes = (kind: IntakeKind, filter: DraftObject = {}) =>
  request(
    '/intakes/query',
    { kind, lifecycle: 'draft', page_size: 25, ...filter },
    (v): v is { items: IntakeSummary[]; next_cursor: string | null } =>
      object(v) &&
      Array.isArray(v.items) &&
      v.items.length <= 25 &&
      v.items.every(summary) &&
      (v.next_cursor === null || typeof v.next_cursor === 'string'),
  );
export const getIntake = (id: string) =>
  uuid.test(id)
    ? request(`/intakes/${id}`, undefined, (v): v is IntakeDetail => detail(v) && v.summary.intake_id === id)
    : Promise.resolve<Result<IntakeDetail>>({ ok: false, failure: 'failed' });
export const getIntakeAddress = (id: string, section: AddressSection) =>
  request(
    `/intakes/${id}/addresses/${section}`,
    undefined,
    (v): v is AddressDetail =>
      object(v) &&
      v.intake_id === id &&
      positive(v.version) &&
      v.section === section &&
      (v.candidate === null ||
        sectionObject(v.candidate, ['line1', 'line2', 'locality', 'region', 'postal_code', 'country'])) &&
      (v.resolved === null ||
        sectionObject(v.resolved, ['line1', 'line2', 'locality', 'region', 'postal_code', 'country'])),
  );
export const saveIntake = (command: Command) =>
  request(
    command.path,
    command.body,
    (v): v is IntakeCommandResult =>
      object(v) && typeof v.command_id === 'string' && positive(v.result_record_version) && detail(v.current),
    command.key,
  );
