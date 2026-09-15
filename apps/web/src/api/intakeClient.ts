import type {
  WorkInterest,
  HistoryItem,
  Page,
  RestrictedHistory,
  StaffChoice,
  CatalogResult,
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
import {
  canonicalId, canonicalReference, canonicalVersion, finalizeBody, finalizationOutputs,
  intakeLinks, linkBody, sameOutputs,
} from './intakeCanonicalContracts';
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
    if (kind === 'worker' && key === 'interests')
      return (
        object(item) &&
        Object.entries(item).every(([field, entry]) =>
          field === 'other_description'
            ? entry === null || typeof entry === 'string'
            : field === 'selections' &&
              Array.isArray(entry) &&
              entry.length <= 20 &&
              entry.every(
                (selection) =>
                  object(selection) &&
                  typeof selection.interest_id === 'string' &&
                  uuid.test(selection.interest_id) &&
                  positive(selection.catalog_version) &&
                  Object.keys(selection).every((k) => ['interest_id', 'catalog_version'].includes(k)),
              ),
        )
      );
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
function summary(v: unknown, allowFinalized = false): v is IntakeSummary {
  return (
    object(v) &&
    typeof v.intake_id === 'string' &&
    uuid.test(v.intake_id) &&
    (v.kind === 'worker' || v.kind === 'employer') &&
    canonicalVersion(v.version) &&
    (v.lifecycle === 'draft' || (allowFinalized && v.lifecycle === 'finalized')) &&
    (typeof v.complete === 'boolean' || (v.complete === null && v.display_name === undefined &&
      Array.isArray(v.missing_fields) && v.missing_fields.length === 0)) &&
    Array.isArray(v.missing_fields) &&
    v.missing_fields.every((x) => typeof x === 'string') &&
    ['unreviewed', 'needs_follow_up', 'current', 'stale'].includes(String(v.review_status)) &&
    (v.follow_up === undefined ||
      (object(v.follow_up) &&
        typeof v.follow_up.owner_staff_id === 'string' &&
        uuid.test(v.follow_up.owner_staff_id) &&
        typeof v.follow_up.next_follow_up_at === 'string' &&
        typeof v.follow_up.overdue === 'boolean')) &&
    typeof v.updated_at === 'string' &&
    (v.display_name === undefined || v.display_name === null || typeof v.display_name === 'string')
  );
}
function detail(v: unknown, allowFinalized = false): v is IntakeDetail {
  return (
    object(v) &&
    Object.keys(v).every((key) => ['summary', 'content_version', 'candidate', 'resolved', 'links',
      'dependency_stale', 'latest_review', 'finalization'].includes(key)) &&
    summary(v.summary, allowFinalized) && v.summary.complete !== null &&
    canonicalVersion(v.content_version) &&
    v.content_version <= v.summary.version &&
    content(v.candidate, v.summary.kind) &&
    content(v.resolved, v.summary.kind) &&
    (v.summary.kind !== 'employer' || Object.keys(v.resolved).every((key) =>
      ['employer_type', 'display_name', 'representative_name', 'phone'].includes(key))) &&
    intakeLinks(v.links, v.summary.kind) &&
    typeof v.dependency_stale === 'boolean' &&
    (Object.keys(v.links).length > 0 ||
      (Object.keys(v.resolved).length === 0 && !v.dependency_stale)) &&
    (v.summary.lifecycle === 'finalized'
      ? finalizationOutputs(v.finalization, v.summary.kind)
      : v.finalization === undefined) &&
    (v.latest_review === undefined ||
      (object(v.latest_review) &&
        typeof v.latest_review.review_id === 'string' &&
        uuid.test(v.latest_review.review_id) &&
        positive(v.latest_review.reviewed_record_version) &&
        positive(v.latest_review.reviewed_content_version) &&
        ['intake_reviewed', 'needs_follow_up'].includes(String(v.latest_review.outcome)) &&
        typeof v.latest_review.actor_id === 'string' &&
        uuid.test(v.latest_review.actor_id) &&
        typeof v.latest_review.actor_display_name === 'string' &&
        typeof v.latest_review.occurred_at === 'string'))
  );
}
async function request<T>(
  path: string,
  body: DraftObject | undefined,
  validate: (value: unknown) => value is T,
  key?: string,
  commandKind?: 'link' | 'finalize',
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
      if (commandKind === 'link' && response.status === 409 &&
        /^application\/problem\+json(?:\s*;.*)?$/i.test(response.headers.get('Content-Type') ?? '')) {
        try {
          const problem: unknown = await response.json();
          if (object(problem) && problem.status === 409 && problem.code === 'no_change' &&
            problem.type === 'urn:golden-rose:intake:no_change')
            return { ok: false, failure: 'failed' };
        } catch { /* An unreadable conflict remains a conflict. */ }
        return { ok: false, failure: 'conflict' };
      }
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
        (object(candidate.current) && object(candidate.current.summary)
          ? candidate.current.summary.version
          : (candidate.current as unknown as WorkInterest).version) < candidate.result_record_version
      )
        return { ok: false, failure: 'unknown' };
      if (commandKind && response.status !==
        (commandKind === 'finalize' && replayed === 'false' ? 201 : 200))
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
      v.items.every((item) => summary(item)) &&
      (v.next_cursor === null || typeof v.next_cursor === 'string'),
  );
export const getIntake = (id: string) =>
  uuid.test(id)
    ? request(
        `/intakes/${id}`,
        undefined,
        (v): v is IntakeDetail => detail(v) && v.summary.intake_id === id,
      )
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
        sectionObject(v.candidate, [
          'line1',
          'line2',
          'locality',
          'region',
          'postal_code',
          'country',
        ])) &&
      (v.resolved === null ||
        sectionObject(v.resolved, ['line1', 'line2', 'locality', 'region', 'postal_code', 'country'])) &&
      (v.source_ref === undefined || canonicalReference(v.source_ref)),
  );

// Canonical detail admits finalized records for the read-only intake view.
export const getCanonicalIntake = (id: string) =>
  canonicalId(id)
    ? request(`/intakes/${id}`, undefined,
      (v): v is IntakeDetail => detail(v, true) && v.summary.intake_id === id)
    : Promise.resolve<Result<IntakeDetail>>({ ok: false, failure: 'failed' });

export const saveCanonicalIntake = (command: Command): Promise<Result<IntakeCommandResult>> => {
  const match = /^\/intakes\/([^/]+)\/(links|finalizations)$/.exec(command.path);
  if (!match || !canonicalId(match[1]) || !canonicalId(command.key) ||
    !(match[2] === 'links' ? linkBody(command.body) : finalizeBody(command.body)))
    return Promise.resolve({ ok: false, failure: 'failed' });
  const target = match[1], finalize = match[2] === 'finalizations';
  return request(command.path, command.body, (v): v is IntakeCommandResult =>
    object(v) && canonicalId(v.command_id) && canonicalVersion(v.result_record_version) &&
    Object.keys(v).every((key) => ['command_id', 'result_record_version', 'current', 'finalization'].includes(key)) &&
    v.result_record_version === Number(command.body.expected_version) + 1 &&
    detail(v.current, true) && v.current.summary.intake_id === target &&
    (!finalize || (v.current.summary.lifecycle === 'finalized' &&
      finalizationOutputs(v.finalization, v.current.summary.kind) &&
      v.current.finalization !== undefined && sameOutputs(v.finalization, v.current.finalization))) &&
    (finalize || v.finalization === undefined), command.key, finalize ? 'finalize' : 'link');
};
export const saveIntake = (command: Command) =>
  request(
    command.path,
    command.body,
    (v): v is IntakeCommandResult =>
      object(v) &&
      typeof v.command_id === 'string' &&
      positive(v.result_record_version) &&
      detail(v.current, true),
    command.key,
  );

const page = <T>(value: unknown, item: (v: unknown) => v is T): value is Page<T> =>
  object(value) &&
  Array.isArray(value.items) &&
  value.items.length <= 25 &&
  value.items.every(item) &&
  (value.next_cursor === null || typeof value.next_cursor === 'string');
const interest = (v: unknown): v is WorkInterest =>
  object(v) &&
  typeof v.interest_id === 'string' &&
  uuid.test(v.interest_id) &&
  positive(v.version) &&
  typeof v.code === 'string' &&
  typeof v.label_en === 'string' &&
  typeof v.label_es === 'string' &&
  typeof v.active === 'boolean';
export const queryWorkInterests = (cursor?: string, includeRetired = false) =>
  request(
    '/work-interests/query',
    { page_size: 25, include_retired: includeRetired, ...(cursor ? { cursor } : {}) },
    (v): v is Page<WorkInterest> => page(v, interest),
  );
export const saveWorkInterest = (command: Command) =>
  request(
    command.path,
    command.body,
    (v): v is CatalogResult =>
      object(v) &&
      typeof v.command_id === 'string' &&
      positive(v.result_record_version) &&
      interest(v.current),
    command.key,
  );
export const queryFollowUpOwners = (id: string, cursor?: string) =>
  request(
    `/intakes/${id}/follow-up-owners/query`,
    { page_size: 25, ...(cursor ? { cursor } : {}) },
    (v): v is Page<StaffChoice> =>
      page(
        v,
        (x): x is StaffChoice =>
          object(x) &&
          typeof x.staff_id === 'string' &&
          uuid.test(x.staff_id) &&
          typeof x.display_name === 'string',
      ),
  );
export const queryIntakeHistory = (id: string, cursor?: string) =>
  request(
    `/intakes/${id}/history/query`,
    { page_size: 25, ...(cursor ? { cursor } : {}) },
    (v): v is Page<HistoryItem> =>
      page(
        v,
        (x): x is HistoryItem =>
          object(x) &&
          typeof x.event_id === 'string' &&
          uuid.test(x.event_id) &&
          positive(x.version) &&
          positive(x.content_version) &&
          typeof x.event_type === 'string' &&
          typeof x.actor_id === 'string' &&
          uuid.test(x.actor_id) &&
          typeof x.actor_display_name === 'string' &&
          typeof x.occurred_at === 'string' &&
          ['review_id', 'outcome', 'owner_staff_id', 'next_follow_up_at'].every(
            (key) => x[key] === undefined || typeof x[key] === 'string',
          ),
      ),
  );
export const getRestrictedHistory = (id: string, eventId: string) =>
  request(
    `/intakes/${id}/history/${eventId}/restricted`,
    undefined,
    (v): v is RestrictedHistory =>
      object(v) &&
      v.event_id === eventId &&
      (v.note === undefined || typeof v.note === 'string') &&
      (v.reviewed_content === undefined || object(v.reviewed_content)) &&
      (v.follow_up === undefined ||
        (object(v.follow_up) &&
          Object.keys(v.follow_up).every((key) =>
            ['action', 'reason_code', 'reason_text', 'method', 'outcome', 'time_zone'].includes(key),
          ) &&
          ['needs_follow_up', 'reschedule', 'reassign', 'attempt'].includes(
            typeof v.follow_up.action === 'string' ? v.follow_up.action : '',
          ) &&
          typeof v.follow_up.reason_text === 'string' &&
          typeof v.follow_up.time_zone === 'string' &&
          (v.follow_up.reason_code === undefined ||
            ['missing_information', 'clarification', 'other'].includes(
              typeof v.follow_up.reason_code === 'string' ? v.follow_up.reason_code : '',
            )) &&
          (v.follow_up.method === undefined ||
            ['phone', 'email', 'in_person', 'other'].includes(
              typeof v.follow_up.method === 'string' ? v.follow_up.method : '',
            )) &&
          (v.follow_up.outcome === undefined ||
            [
              'no_answer',
              'voicemail_left',
              'callback_requested',
              'contact_reached_information_pending',
              'invalid_contact_information',
              'information_received',
              'other',
            ].includes(typeof v.follow_up.outcome === 'string' ? v.follow_up.outcome : '')))),
  );
