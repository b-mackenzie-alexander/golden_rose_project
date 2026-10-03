import { staffApiFetch } from '../auth/staffAuthSession';
import { canonicalId, canonicalVersion } from './intakeCanonicalContracts';
import type { CanonicalReference } from './intakeCanonicalContracts';
import type { IntakeKind, Page, Result } from './intakeContracts';
export type Choice = CanonicalReference & { label: string; employerType?: 'household' | 'business' };
export type Collection = 'contacts' | 'worksites' | 'addresses';
const object = (v: unknown): v is Record<string, unknown> => !!v && typeof v === 'object' && !Array.isArray(v);
export async function discover(kind: IntakeKind, query: string, cursor?: string,
  parent?: string, collection?: Collection): Promise<Result<Page<Choice>>> {
  if (parent ? !canonicalId(parent) || !collection : query.trim().length < 2 || query.trim().length > 100)
    return { ok: false, failure: 'failed' };
  const path = parent ? `/employers/${parent}/${collection ?? ""}/query`
    : kind === 'worker' ? '/workers/query' : '/employers/search';
  const idKey = parent ? collection === 'contacts' ? 'employer_contact_id'
    : collection === 'worksites' ? 'worksite_id' : 'employer_address_id'
    : kind === 'worker' ? 'worker_id' : 'employer_id';
  const labelKey = parent ? collection === 'contacts' ? 'full_name' : null
    : kind === 'worker' ? 'full_name' : 'display_name';
  const allowed = parent ? collection === 'contacts'
    ? [idKey, 'employer_id', 'full_name', 'version', 'created_at', 'updated_at']
    : [idKey, 'employer_id', 'version', ...(collection === 'addresses' ? ['purpose'] : [])]
    : kind === 'worker' ? [idKey, 'full_name', 'version']
      : [idKey, 'employer_type', 'display_name', 'lifecycle_status', 'version', 'received_at'];
  try {
    const response = await staffApiFetch(`/api/staff/v1${path}`, {
      method: 'POST', headers: { Accept: 'application/json', 'Content-Type': 'application/json' },
      body: JSON.stringify({ page_size: 25, ...(cursor ? { cursor } : {}),
        ...(!parent ? { [kind === 'worker' ? 'name_query' : 'display_name_query']: query.trim() } : {}) }),
      cache: 'no-store', credentials: 'same-origin', mode: 'same-origin', redirect: 'error', referrerPolicy: 'no-referrer',
    });
    if (response.status !== 200) {
      await response.body?.cancel();
      return { ok: false, failure: response.status === 403 ? 'forbidden' : 'failed' };
    }
    if (!/^application\/json(?:\s*;.*)?$/i.test(response.headers.get('Content-Type') ?? ''))
      return { ok: false, failure: 'failed' };
    const value: unknown = await response.json();
    if (!object(value) || !Object.keys(value).every((k) => ['items', 'next_cursor'].includes(k)) ||
      !Array.isArray(value.items) || value.items.length > 25 ||
      !(value.next_cursor === null || typeof value.next_cursor === 'string') ||
      !value.items.every((x) => object(x) && Object.keys(x).every((k) => allowed.includes(k)) &&
        canonicalId(x[idKey]) && canonicalVersion(x.version) &&
        (!parent || x.employer_id === parent) && (!labelKey || typeof x[labelKey] === 'string') &&
        (parent || kind === 'worker' || ['household', 'business'].includes(String(x.employer_type)))))
      return { ok: false, failure: 'failed' };
    return { ok: true, value: { next_cursor: value.next_cursor, items: (value.items as Record<string, unknown>[]).map((x) => ({
      id: x[idKey] as string, version: x.version as number,
      label: labelKey ? x[labelKey] as string : x[idKey] as string,
      ...(!parent && kind === 'employer' ? { employerType: x.employer_type as 'household' | 'business' } : {}),
    })) } };
  } catch { return { ok: false, failure: 'failed' }; }
}
