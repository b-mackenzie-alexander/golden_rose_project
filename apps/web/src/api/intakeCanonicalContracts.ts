import type { IntakeKind } from './intakeContracts';

export type CanonicalReference = { id: string; version: number };
export type OutputReference = CanonicalReference & { disposition: 'created' | 'reused' };
export type LinkEntity =
  | 'worker' | 'worker_contact' | 'worker_residence' | 'worker_preferences'
  | 'employer' | 'employer_contact' | 'employer_contact_details' | 'worksite' | 'employer_address';
export type IntakeLinks = Partial<Record<LinkEntity, CanonicalReference>>;
export type FinalizationOutputs =
  | { kind: 'worker'; worker: OutputReference; contact: OutputReference;
      residence: OutputReference; preferences: OutputReference }
  | { kind: 'employer'; employer: OutputReference; contact: OutputReference;
      contact_details: OutputReference; worksite: OutputReference;
      request: OutputReference; business_address: OutputReference | null };
export type LinkIntakeBody = {
  expected_version: number;
  party: CanonicalReference | null;
  contact?: CanonicalReference | null;
  worksite?: CanonicalReference | null;
  business_address?: CanonicalReference | null;
};
export type FinalizeIntakeBody = { expected_version: number; review_id: string };

const object = (v: unknown): v is Record<string, unknown> =>
  !!v && typeof v === 'object' && !Array.isArray(v);
export const canonicalId = (v: unknown): v is string =>
  typeof v === 'string' &&
  /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/.test(v) &&
  v !== '00000000-0000-0000-0000-000000000000';
export const canonicalVersion = (v: unknown): v is number =>
  typeof v === 'number' && Number.isInteger(v) && v >= 1 && v <= 2147483647;
const keys = (v: Record<string, unknown>, allowed: string[]) =>
  Object.keys(v).every((key) => allowed.includes(key));
export function canonicalReference(v: unknown): v is CanonicalReference {
  return object(v) && keys(v, ['id', 'version']) && canonicalId(v.id) && canonicalVersion(v.version);
}
function outputReference(v: unknown): v is OutputReference {
  return object(v) && keys(v, ['id', 'version', 'disposition']) &&
    canonicalId(v.id) && canonicalVersion(v.version) &&
    (v.disposition === 'reused' || (v.disposition === 'created' && v.version === 1));
}
export function intakeLinks(v: unknown, kind: IntakeKind): v is IntakeLinks {
  if (!object(v) || !Object.values(v).every(canonicalReference)) return false;
  const names = Object.keys(v);
  if (names.length === 0) return true;
  if (kind === 'worker') {
    const required = ['worker', 'worker_contact', 'worker_residence', 'worker_preferences'];
    return names.length === required.length && required.every((name) => names.includes(name));
  }
  return keys(v, ['employer', 'employer_contact', 'employer_contact_details', 'worksite', 'employer_address']) &&
    !!v.employer && (!!v.employer_contact === !!v.employer_contact_details);
}
export function finalizationOutputs(v: unknown, kind: IntakeKind): v is FinalizationOutputs {
  if (!object(v) || v.kind !== kind) return false;
  const names = kind === 'worker'
    ? ['worker', 'contact', 'residence', 'preferences']
    : ['employer', 'contact', 'contact_details', 'worksite', 'request', 'business_address'];
  if (!keys(v, ['kind', ...names])) return false;
  if (!names.every((name) => name === 'business_address' && v[name] === null || outputReference(v[name])))
    return false;
  const disposition = (name: string) => (v[name] as OutputReference).disposition;
  if (kind === 'worker') return names.every((name) => disposition(name) === disposition('worker'));
  return disposition('request') === 'created' && disposition('contact') === disposition('contact_details') &&
    (disposition('employer') === 'reused' || names.every((name) => v[name] === null || disposition(name) === 'created'));
}
export function sameOutputs(a: FinalizationOutputs, b: FinalizationOutputs): boolean {
  if (a.kind !== b.kind) return false;
  return Object.entries(a).every(([name, value]) => {
    const other = (b as unknown as Record<string, unknown>)[name];
    return typeof value === 'string' || value === null ? value === other :
      object(other) && value.id === other.id && value.version === other.version &&
      value.disposition === other.disposition;
  });
}
export function linkBody(v: unknown): v is LinkIntakeBody {
  if (!object(v) || !keys(v, ['expected_version', 'party', 'contact', 'worksite', 'business_address']) ||
    !canonicalVersion(v.expected_version) || v.expected_version === 2147483647 ||
    !(v.party === null || canonicalReference(v.party))) return false;
  return ['contact', 'worksite', 'business_address'].every((name) =>
    v[name] === undefined || v[name] === null || (v.party !== null && canonicalReference(v[name])));
}
export function finalizeBody(v: unknown): v is FinalizeIntakeBody {
  return object(v) && keys(v, ['expected_version', 'review_id']) &&
    canonicalVersion(v.expected_version) && v.expected_version < 2147483647 && canonicalId(v.review_id);
}
