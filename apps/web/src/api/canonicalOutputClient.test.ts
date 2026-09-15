import { afterEach, expect, it, vi } from 'vitest';
import { getCanonicalOutput } from './canonicalOutputClient';
import type { FinalizationOutputs } from './intakeCanonicalContracts';
const id = '11111111-1111-4111-8111-111111111111';
const child = '22222222-2222-4222-8222-222222222222';
const ref = { id, version: 1, disposition: 'created' as const };
const outputs: FinalizationOutputs = { kind: 'worker', worker: ref, contact: { ...ref, id: child }, residence: ref, preferences: ref };
afterEach(() => vi.unstubAllGlobals());
it('reads the exact worker child with current version and private transport', async () => {
  const fetcher = vi.fn().mockResolvedValue(new Response(JSON.stringify({ worker_id: id, worker_contact_id: child, version: 2, phone: '+15555550123' }), { headers: { 'Content-Type': 'application/json' } }));
  vi.stubGlobal('fetch', fetcher);
  expect(await getCanonicalOutput(outputs, 'contact')).toMatchObject({ ok: true, value: { version: 2 } });
  expect(fetcher).toHaveBeenCalledWith(`/api/staff/v1/workers/${id}/contact`, expect.objectContaining({ cache: 'no-store', referrerPolicy: 'no-referrer', method: 'GET' }));
});
it.each([{ worker_id: child, worker_contact_id: child, version: 1, phone: '123' },
  { worker_id: id, worker_contact_id: id, version: 1, phone: '123' },
  { worker_id: id, worker_contact_id: child, version: 1, phone: '123', address: {} }])('rejects mismatched and overbroad output responses', async (value) => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(JSON.stringify(value), { headers: { 'Content-Type': 'application/json' } })));
  expect((await getCanonicalOutput(outputs, 'contact')).ok).toBe(false);
});
it('rejects missing or unsupported output routes before fetch', async () => {
  const fetcher = vi.fn(); vi.stubGlobal('fetch', fetcher);
  expect((await getCanonicalOutput(outputs, 'request')).ok).toBe(false);
  expect(fetcher).not.toHaveBeenCalled();
});

const employer: FinalizationOutputs = { kind: 'employer', employer: ref, contact: { ...ref, id: child }, contact_details: ref, worksite: ref, request: ref, business_address: ref };
const dates = { created_at: '2026-09-15T12:00:00Z', updated_at: '2026-09-15T12:00:00Z' };
const address = { line1: 'Fictional address', locality: 'Fictional town', country: 'US' };
const scenarios: { outputs: FinalizationOutputs; key: string; reveal?: boolean; path: string; value: object }[] = [
  { outputs, key: 'worker', path: `/workers/${id}`, value: { worker_id: id, version: 1, full_name: 'Fictional', contact_id: child, residence_id: id, preferences_id: id, ...dates } },
  { outputs, key: 'residence', path: `/workers/${id}/residence`, value: { worker_id: id, worker_residence_id: id, version: 1, address } },
  { outputs, key: 'preferences', path: `/workers/${id}/preferences`, value: { worker_id: id, worker_preferences_id: id, version: 1, self_reported: true,
    interests: { selections: [{ interest_id: id, catalog_version: 1 }], other_description: null },
    availability: { mode: 'weekly', time_zone: 'America/New_York', ranges: [{ weekday: 1, start_local: '09:00', end_local: '12:00', end_day_offset: 0 }] } } },
  { outputs: employer, key: 'employer', path: `/employers/${id}`, value: { employer_id: id, version: 1, employer_type: 'business', display_name: 'Fictional', lifecycle_status: 'draft', source_channel: 'staff_entry', received_at: dates.created_at, ...dates } },
  { outputs: employer, key: 'contact', path: `/employers/${id}/contacts/${child}`, value: { employer_id: id, employer_contact_id: child, version: 1, full_name: 'Fictional contact', ...dates } },
  { outputs: employer, key: 'contact_details', path: `/employers/${id}/contacts/${child}/details`, value: { employer_id: id, employer_contact_id: child, contact_details_id: id, version: 1, phone: '+15555550123' } },
  { outputs: employer, key: 'contact_details', reveal: true, path: `/employers/${id}/contacts/${child}/details/address`, value: { contact_details_id: id, version: 1, address } },
  { outputs: employer, key: 'worksite', path: `/employers/${id}/worksites/${id}`, value: { employer_id: id, worksite_id: id, version: 1, location_verification_status: 'supplied', service_area_status: 'unassigned', map_area_status: 'pending' } },
  { outputs: employer, key: 'worksite', reveal: true, path: `/employers/${id}/worksites/${id}/address`, value: { employer_id: id, worksite_id: id, version: 1, address } },
  { outputs: employer, key: 'business_address', path: `/employers/${id}/addresses/${id}`, value: { employer_id: id, employer_address_id: id, version: 1, purpose: 'business', address } },
  { outputs: employer, key: 'request', path: `/employers/${id}/requests/${id}`, value: { employer_id: id, staffing_request_id: id, employer_contact_id: child, worksite_id: id, employer_address_id: id,
    version: 1, request_type: 'general_labor', request_status: 'draft', source_channel: 'staff_entry', role_title: 'Fictional role', duties_summary: 'Fictional duties', worker_count: 1,
    schedule: { mode: 'to_be_discussed' }, offer: { negotiable: false, minimum: '10', currency: 'USD', basis: 'hour', per_worker: true }, received_at: dates.created_at, ...dates } },
];
it.each(scenarios)('reads only the concrete $key endpoint (address=$reveal)', async ({ outputs: selected, key, reveal, path, value }) => {
  const fetcher = vi.fn().mockResolvedValue(new Response(JSON.stringify(value), { headers: { 'Content-Type': 'application/json' } }));
  vi.stubGlobal('fetch', fetcher);
  expect(await getCanonicalOutput(selected, key, reveal)).toEqual({ ok: true, value });
  expect(fetcher.mock.calls[0]?.[0]).toBe(`/api/staff/v1${path}`);
});
it.each([403, 404, 503])('handles output read denial/failure %s without response disclosure', async (status) => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('private error', { status })));
  expect(await getCanonicalOutput(outputs, 'contact')).toEqual({ ok: false, failure: status === 403 ? 'forbidden' : 'failed' });
});
it('fails closed on HTML, malformed JSON and network failure', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValueOnce(new Response('html')).mockResolvedValueOnce(new Response('{', { headers: { 'Content-Type': 'application/json' } })).mockRejectedValueOnce(new Error('offline')));
  for (let i = 0; i < 3; i++) expect((await getCanonicalOutput(outputs, 'contact')).ok).toBe(false);
});
it('rejects absent address, prototype keys, invalid reveal, old versions and nested unexpected fields', async () => {
  const fetcher = vi.fn(); vi.stubGlobal('fetch', fetcher);
  expect((await getCanonicalOutput({ ...employer, business_address: null }, 'business_address')).ok).toBe(false);
  expect((await getCanonicalOutput(outputs, '__proto__')).ok).toBe(false);
  expect((await getCanonicalOutput(outputs, 'worker', true)).ok).toBe(false);
  expect(fetcher).not.toHaveBeenCalled();
  fetcher.mockResolvedValue(new Response(JSON.stringify({ worker_id: id, worker_contact_id: child, version: 0, phone: '123' }), { headers: { 'Content-Type': 'application/json' } }));
  expect((await getCanonicalOutput(outputs, 'contact')).ok).toBe(false);
  fetcher.mockResolvedValue(new Response(JSON.stringify({ worker_id: id, worker_residence_id: id, version: 1, address: { secret: 'not permitted' } }), { headers: { 'Content-Type': 'application/json' } }));
  expect((await getCanonicalOutput(outputs, 'residence')).ok).toBe(false);
});
