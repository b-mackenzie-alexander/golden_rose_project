import { afterEach, describe, expect, it, vi } from 'vitest';
import { discover } from './canonicalDiscovery';
const id = '11111111-1111-4111-8111-111111111111';
function response(items: unknown[], next_cursor: string | null = null) {
  return new Response(JSON.stringify({ items, next_cursor }), { headers: { 'Content-Type': 'application/json' } });
}
afterEach(() => vi.unstubAllGlobals());
describe('minimized canonical discovery', () => {
  it('queries workers by name with privacy controls and a bound cursor', async () => {
    const fetcher = vi.fn().mockResolvedValue(response([{ worker_id: id, full_name: 'Fictional', version: 2 }], 'next'));
    vi.stubGlobal('fetch', fetcher);
    expect(await discover('worker', ' Fictional ', 'cursor')).toEqual({ ok: true, value: {
      items: [{ id, label: 'Fictional', version: 2 }], next_cursor: 'next' } });
    expect(fetcher).toHaveBeenCalledWith('/api/staff/v1/workers/query', expect.objectContaining({
      cache: 'no-store', referrerPolicy: 'no-referrer', body: JSON.stringify({ page_size: 25, cursor: 'cursor', name_query: 'Fictional' }),
    }));
  });
  it('retains employer type and current version', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(response([{ employer_id: id, display_name: 'Fictional', employer_type: 'business', version: 4 }])));
    expect(await discover('employer', 'Fi')).toMatchObject({ ok: true, value: { items: [{ employerType: 'business', version: 4 }] } });
  });
  it.each(['contacts', 'worksites', 'addresses'] as const)('checks same-parent %s projections', async (collection) => {
    const key = collection === 'contacts' ? 'employer_contact_id' : collection === 'worksites' ? 'worksite_id' : 'employer_address_id';
    const item = { [key]: id, employer_id: id, version: 1, ...(collection === 'contacts' ? { full_name: 'Fictional' } : {}) };
    const fetcher = vi.fn().mockResolvedValueOnce(response([item])).mockResolvedValueOnce(response([{ ...item, employer_id: '22222222-2222-4222-8222-222222222222' }]));
    vi.stubGlobal('fetch', fetcher);
    expect((await discover('employer', '', undefined, id, collection)).ok).toBe(true);
    expect((await discover('employer', '', undefined, id, collection)).ok).toBe(false);
  });
  it.each([{ worker_id: id, full_name: 'Fictional', version: 0 },
    { worker_id: id, full_name: 'Fictional', version: 1, address: { line1: 'Restricted' } }, {}])('rejects malformed or overbroad rows', async (item) => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(response([item])));
    expect((await discover('worker', 'Fi')).ok).toBe(false);
  });
  it('rejects short searches and invalid parents before fetch', async () => {
    const fetcher = vi.fn(); vi.stubGlobal('fetch', fetcher);
    expect((await discover('worker', 'a')).ok).toBe(false);
    expect((await discover('employer', '', undefined, 'invalid', 'contacts')).ok).toBe(false);
    expect(fetcher).not.toHaveBeenCalled();
  });
  it.each([403, 503])('handles denied/unavailable responses: %s', async (status) => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('', { status })));
    expect(await discover('worker', 'Fi')).toEqual({ ok: false, failure: status === 403 ? 'forbidden' : 'failed' });
  });
  it('rejects HTML and network errors', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValueOnce(new Response('html')).mockRejectedValueOnce(new Error('offline')));
    expect((await discover('worker', 'Fi')).ok).toBe(false);
    expect((await discover('worker', 'Fi')).ok).toBe(false);
  });
});
