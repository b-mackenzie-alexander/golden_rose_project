import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router';
import { beforeEach, expect, it, vi } from 'vitest';
import { AppRoutes } from '../app/App';
import { LanguageProvider } from '../i18n/LanguageProvider';
import { getCanonicalIntake } from '../api/intakeClient';
import { getCanonicalOutput } from '../api/canonicalOutputClient';
import type { FinalizationOutputs } from '../api/intakeCanonicalContracts';
import type { DraftObject, IntakeDetail, Result } from '../api/intakeContracts';
import { runAxe } from '../test/axe';
vi.mock('../api/intakeClient');
vi.mock('../api/canonicalOutputClient', async (importOriginal) => ({
  ...await importOriginal<typeof import('../api/canonicalOutputClient')>(), getCanonicalOutput: vi.fn(),
}));
const id = '11111111-1111-4111-8111-111111111111';
const ref = { id, version: 1, disposition: 'created' as const };
const worker: FinalizationOutputs = { kind: 'worker', worker: ref, contact: ref, residence: ref, preferences: ref };
const employer: FinalizationOutputs = { kind: 'employer', employer: ref, contact: ref, contact_details: ref, worksite: ref, request: ref, business_address: ref };
function detail(outputs: FinalizationOutputs = worker): IntakeDetail {
  return { summary: { intake_id: id, kind: outputs.kind, version: 2, lifecycle: 'finalized', complete: true, missing_fields: [], review_status: 'current', updated_at: '' },
    candidate: {}, resolved: {}, links: {}, content_version: 1, dependency_stale: false, finalization: outputs };
}
function mount(key = 'worker') {
  return render(<LanguageProvider><MemoryRouter initialEntries={[`/staff/intakes/${id}/outputs/${key}`]}><AppRoutes /></MemoryRouter></LanguageProvider>);
}
function deferred() {
  let resolve!: (value: Result<DraftObject>) => void;
  const promise = new Promise<Result<DraftObject>>((r) => { resolve = r; });
  return { promise, resolve };
}
beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(getCanonicalIntake).mockResolvedValue({ ok: true, value: detail() });
  vi.mocked(getCanonicalOutput).mockResolvedValue({ ok: true, value: { version: 1, full_name: 'Fictional current worker' } });
});
it('shows original references separately from current facts and links sibling outputs', async () => {
  vi.mocked(getCanonicalOutput).mockResolvedValue({ ok: true, value: { version: 2, full_name: 'Fictional changed worker' } });
  mount();
  await screen.findByText('Fictional changed worker');
  expect(screen.getByText(/Current facts have changed/)).toBeInTheDocument();
  expect(screen.getByText(/Original finalized reference/)).toHaveTextContent('Version 1');
  expect(screen.getByRole('link', { name: 'Contact' })).toHaveAttribute('href', `/staff/intakes/${id}/outputs/contact`);
  expect(screen.getByRole('link', { name: 'Original intake and history' })).toHaveAttribute('href', `/staff/intakes/${id}`);
  expect(screen.queryByRole('textbox')).not.toBeInTheDocument();
});
it.each(['residence', 'business_address'])('does not fetch restricted %s until explicit reveal and clears on hide', async (key) => {
  vi.mocked(getCanonicalIntake).mockResolvedValue({ ok: true, value: detail(key === 'residence' ? worker : employer) });
  vi.mocked(getCanonicalOutput).mockResolvedValue({ ok: true, value: { version: 1, address: { line1: 'Fictional restricted location' } } });
  mount(key); await screen.findByRole('button', { name: 'Reveal restricted address' });
  expect(getCanonicalOutput).not.toHaveBeenCalled();
  fireEvent.click(screen.getByRole('button', { name: 'Reveal restricted address' }));
  await screen.findByText('Fictional restricted location');
  fireEvent.click(screen.getByRole('button', { name: 'Hide restricted address' }));
  expect(screen.queryByText('Fictional restricted location')).not.toBeInTheDocument();
});
it('keeps ordinary worksite detail separate from address reveal and flags differing versions', async () => {
  vi.mocked(getCanonicalIntake).mockResolvedValue({ ok: true, value: detail(employer) });
  vi.mocked(getCanonicalOutput).mockResolvedValueOnce({ ok: true, value: { version: 1, location_verification_status: 'supplied' } })
    .mockResolvedValueOnce({ ok: true, value: { version: 2, address: { line1: 'Fictional worksite' } } });
  mount('worksite'); await screen.findByText('Supplied, not verified');
  expect(getCanonicalOutput).toHaveBeenCalledTimes(1);
  fireEvent.click(screen.getByRole('button', { name: 'Reveal restricted address' }));
  await screen.findByText('Fictional worksite');
  expect(getCanonicalOutput).toHaveBeenLastCalledWith(employer, 'worksite', true);
  expect(screen.getByText(/Address and detail versions differ/)).toBeInTheDocument();
});
it('suppresses late reveals after hiding and after route changes', async () => {
  const pending = deferred();
  vi.mocked(getCanonicalOutput).mockReturnValueOnce(pending.promise);
  mount('residence'); await screen.findByRole('button', { name: 'Reveal restricted address' });
  fireEvent.click(screen.getByRole('button', { name: 'Reveal restricted address' }));
  fireEvent.click(screen.getByRole('button', { name: 'Hide restricted address' }));
  await act(async () => { pending.resolve({ ok: true, value: { version: 1, address: { line1: 'Late location' } } }); await pending.promise; });
  expect(screen.queryByText('Late location')).not.toBeInTheDocument();
  const second = deferred(); vi.mocked(getCanonicalOutput).mockReturnValueOnce(second.promise);
  fireEvent.click(screen.getByRole('button', { name: 'Reveal restricted address' }));
  fireEvent.click(screen.getByRole('link', { name: 'Contact' }));
  await screen.findByText('Fictional current worker');
  await act(async () => { second.resolve({ ok: true, value: { address: { line1: 'Other late location' } } }); await second.promise; });
  expect(screen.queryByText('Other late location')).not.toBeInTheDocument();
});
it('clears facts before a denied refresh and permits read recovery', async () => {
  mount(); await screen.findByText('Fictional current worker');
  vi.mocked(getCanonicalOutput).mockResolvedValueOnce({ ok: false, failure: 'forbidden' });
  fireEvent.click(screen.getByRole('button', { name: 'Refresh current facts' }));
  await screen.findByRole('alert');
  expect(screen.queryByText('Fictional current worker')).not.toBeInTheDocument();
  fireEvent.click(screen.getByRole('button', { name: 'Refresh current facts' }));
  await screen.findByText('Fictional current worker');
});
it('shows address denial separately without erasing ordinary contact details', async () => {
  vi.mocked(getCanonicalIntake).mockResolvedValue({ ok: true, value: detail(employer) });
  vi.mocked(getCanonicalOutput).mockResolvedValueOnce({ ok: true, value: { version: 1, phone: '+15555550123' } }).mockResolvedValueOnce({ ok: false, failure: 'forbidden' });
  mount('contact_details'); await screen.findByText('+15555550123');
  fireEvent.click(screen.getByRole('button', { name: 'Reveal restricted address' }));
  await screen.findByRole('alert');
  expect(screen.getByText('+15555550123')).toBeInTheDocument();
});
it.each(['request', '__proto__'])('rejects unsupported worker output %s without reading canonical facts', async (key) => {
  mount(key); await screen.findByRole('alert'); expect(getCanonicalOutput).not.toHaveBeenCalled();
});
it('denies output navigation from drafts or unavailable intakes', async () => {
  vi.mocked(getCanonicalIntake).mockResolvedValue({ ok: false, failure: 'forbidden' });
  mount(); await screen.findByRole('alert'); expect(getCanonicalOutput).not.toHaveBeenCalled();
});
it('clears content on pagehide and does not repopulate from a pending read', async () => {
  const pending = deferred(); vi.mocked(getCanonicalOutput).mockReturnValue(pending.promise);
  mount(); await waitFor(() => { expect(getCanonicalOutput).toHaveBeenCalled(); });
  fireEvent(window, new Event('pagehide'));
  await act(async () => { pending.resolve({ ok: true, value: { full_name: 'Late worker' } }); await pending.promise; });
  expect(screen.queryByText('Late worker')).not.toBeInTheDocument();
  expect(screen.queryByText(/Original finalized reference/)).not.toBeInTheDocument();
});
it('renders Spanish current-fact labels and passes automated accessibility checks', async () => {
  const view = mount(); await screen.findByText('Fictional current worker');
  fireEvent.click(screen.getByRole('button', { name: 'Cambiar a español' }));
  expect(screen.getByRole('heading', { name: 'Datos canónicos actuales' })).toBeInTheDocument();
  expect(screen.getByText('Nombre completo')).toBeInTheDocument();
  expect(await runAxe(view.container)).toEqual([]);
});
