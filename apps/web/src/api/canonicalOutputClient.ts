import { canonicalId, canonicalVersion, finalizationOutputs } from './intakeCanonicalContracts';
import type { FinalizationOutputs, OutputReference } from './intakeCanonicalContracts';
import type { DraftObject, Result } from './intakeContracts';

type Validator = (value: unknown) => boolean;
const object = (value: unknown): value is Record<string, unknown> =>
  !!value && typeof value === 'object' && !Array.isArray(value);
const text: Validator = (v) => typeof v === 'string';
const boolean: Validator = (v) => typeof v === 'boolean';
const oneOf = (...values: unknown[]): Validator => (v) => values.includes(v);
const nullable = (validate: Validator): Validator => (v) => v === null || validate(v);
const list = (validate: Validator, max: number): Validator => (v) =>
  Array.isArray(v) && v.length <= max && v.every(validate);
function shape(required: Record<string, Validator>, optional: Record<string, Validator> = {}): Validator {
  return (v) => object(v) && Object.entries(required).every(([key, validate]) => validate(v[key])) &&
    Object.entries(v).every(([key, value]) => (required[key] ?? optional[key])?.(value) === true);
}
const address = shape({}, Object.fromEntries(
  ['line1', 'line2', 'locality', 'region', 'postal_code', 'country'].map((key) => [key, nullable(text)]),
));
const availability = shape({ mode: oneOf('unknown', 'flexible', 'weekly') }, {
  time_zone: nullable(text), exception_note: nullable(text), ranges: nullable(list(shape({
    weekday: oneOf(1, 2, 3, 4, 5, 6, 7), start_local: text, end_local: text, end_day_offset: oneOf(0, 1),
  }), 28)),
});
const interests = shape({ selections: list(shape({ interest_id: canonicalId, catalog_version: canonicalVersion }), 20) },
  { other_description: nullable(text) });
const schedule = shape({ mode: oneOf('unknown', 'to_be_discussed', 'specified') }, Object.fromEntries(
  ['requested_start_date', 'starts_at', 'ends_at', 'time_zone', 'note'].map((key) => [key, nullable(text)]),
));
const offer = shape({ negotiable: boolean }, {
  minimum: nullable(text), maximum: nullable(text), currency: nullable(text),
  basis: nullable(oneOf('hour', 'day', 'week', 'month', 'year', 'task')), per_worker: nullable(oneOf(true)), terms: nullable(text),
});
const dates = { created_at: text, updated_at: text };
export function outputReference(outputs: FinalizationOutputs, key: string): OutputReference | null {
  if (!finalizationOutputs(outputs, outputs.kind) || key === 'kind' || !Object.hasOwn(outputs, key)) return null;
  const value: unknown = (outputs as unknown as Record<string, unknown>)[key];
  return object(value) ? value as OutputReference : null;
}
export function restrictedOutput(key: string): boolean {
  return key === 'residence' || key === 'business_address';
}
export function hasAddress(key: string, outputs: FinalizationOutputs): boolean {
  return outputs.kind === 'employer' && (key === 'contact_details' || key === 'worksite');
}
export async function getCanonicalOutput(outputs: FinalizationOutputs, key: string, revealAddress = false): Promise<Result<DraftObject>> {
  const reference = outputReference(outputs, key);
  if (!reference || (revealAddress && !hasAddress(key, outputs))) return { ok: false, failure: 'failed' };
  let path: string, validate: Validator;
  const identity = { version: canonicalVersion };
  if (outputs.kind === 'worker') {
    const parent = outputs.worker.id;
    path = `/workers/${parent}${key === 'worker' ? '' : `/${key}`}`;
    const base = { ...identity, worker_id: oneOf(parent) };
    const schemas: Record<string, Validator> = {
      worker: shape({ ...base, ...dates, full_name: text, contact_id: oneOf(outputs.contact.id),
        residence_id: oneOf(outputs.residence.id), preferences_id: oneOf(outputs.preferences.id) }),
      contact: shape({ ...base, worker_contact_id: oneOf(reference.id), phone: text }),
      residence: shape({ ...base, worker_residence_id: oneOf(reference.id), address }),
      preferences: shape({ ...base, worker_preferences_id: oneOf(reference.id), interests, availability, self_reported: oneOf(true) }),
    };
    validate = schemas[key] ?? (() => false);
  } else {
    const parent = outputs.employer.id;
    const base = { ...identity, employer_id: oneOf(parent) };
    const prefix = `/employers/${parent}`;
    switch (key) {
      case 'employer':
        path = prefix;
        validate = shape({ ...base, ...dates, received_at: text, employer_type: oneOf('business', 'household'),
          display_name: text, lifecycle_status: oneOf('draft'), source_channel: oneOf('staff_entry') });
        break;
      case 'contact':
        path = `${prefix}/contacts/${reference.id}`;
        validate = shape({ ...base, ...dates, employer_contact_id: oneOf(reference.id), full_name: text });
        break;
      case 'contact_details':
        path = `${prefix}/contacts/${outputs.contact.id}/details${revealAddress ? '/address' : ''}`;
        validate = revealAddress
          ? shape({ ...identity, contact_details_id: oneOf(reference.id), address })
          : shape({ ...base, contact_details_id: oneOf(reference.id), employer_contact_id: oneOf(outputs.contact.id), representative_name: text, phone: text });
        break;
      case 'worksite':
        path = `${prefix}/worksites/${reference.id}${revealAddress ? '/address' : ''}`;
        validate = revealAddress ? shape({ ...base, worksite_id: oneOf(reference.id), address })
          : shape({ ...base, worksite_id: oneOf(reference.id), location_verification_status: oneOf('supplied'),
            service_area_status: oneOf('unassigned'), map_area_status: oneOf('pending') });
        break;
      case 'business_address':
        path = `${prefix}/addresses/${reference.id}`;
        validate = shape({ ...base, employer_address_id: oneOf(reference.id), purpose: oneOf('business'), address });
        break;
      case 'request':
        path = `${prefix}/requests/${reference.id}`;
        validate = shape({ ...base, ...dates, received_at: text, staffing_request_id: oneOf(reference.id),
          employer_contact_id: oneOf(outputs.contact.id), worksite_id: oneOf(outputs.worksite.id),
          employer_address_id: oneOf(outputs.business_address?.id ?? null), request_type: oneOf(outputs.business_address ? 'general_labor' : 'household'),
          request_status: oneOf('draft'), source_channel: oneOf('staff_entry'), role_title: text, duties_summary: text,
          worker_count: (v) => typeof v === 'number' && Number.isInteger(v) && v >= 1 && v <= 1000, schedule, offer });
        break;
      default: return { ok: false, failure: 'failed' };
    }
  }
  try {
    const response = await fetch(`/api/staff/v1${path}`, { method: 'GET', headers: { Accept: 'application/json' },
      cache: 'no-store', credentials: 'same-origin', mode: 'same-origin', redirect: 'error', referrerPolicy: 'no-referrer' });
    if (response.status !== 200) {
      await response.body?.cancel();
      return { ok: false, failure: response.status === 403 ? 'forbidden' : 'failed' };
    }
    if (!/^application\/json(?:\s*;.*)?$/i.test(response.headers.get('Content-Type') ?? '')) return { ok: false, failure: 'failed' };
    const value: unknown = await response.json();
    return validate(value) && object(value) && Number(value.version) >= reference.version
      ? { ok: true, value: value as DraftObject } : { ok: false, failure: 'failed' };
  } catch { return { ok: false, failure: 'failed' }; }
}
