import { useState } from 'react';
import { fireEvent, render, screen, within, waitFor } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { LanguageProvider, useLanguage } from '../i18n/LanguageProvider';
import type { IntakeDetail } from '../api/intakeContracts';
import { initialSection } from './saveState';
import * as discovery from '../api/canonicalDiscovery';
import { IntakeCanonical } from './IntakeCanonical';
const id = '11111111-1111-4111-8111-111111111111';
const detail: IntakeDetail = {
  summary: { intake_id: id, kind: 'worker', version: 3, lifecycle: 'draft', complete: true,
    missing_fields: [], review_status: 'current', updated_at: '' },
  content_version: 1, candidate: {}, resolved: {}, links: {}, dependency_stale: false,
  latest_review: { review_id: id, reviewed_record_version: 2, reviewed_content_version: 1,
    outcome: 'intake_reviewed', actor_id: id, actor_display_name: 'Fictional Staff', occurred_at: '' },
};
function mount(overrides = {}) {
  const change = vi.fn(), save = vi.fn();
  render(<LanguageProvider><IntakeCanonical detail={detail} section={initialSection({})}
    ready locked={false} change={change} save={save} {...overrides} /></LanguageProvider>);
  return { change, save };
}
describe('canonical intake controls', () => {
  it('requires deliberate finalization confirmation bound to the review', () => {
    const { save } = mount();
    expect(screen.getByRole('button', { name: 'Finalize intake' })).toBeDisabled();
    fireEvent.click(screen.getByLabelText(/I confirm/));
    fireEvent.click(screen.getByRole('button', { name: 'Finalize intake' }));
    expect(save).toHaveBeenCalledWith({ operation: 'finalizations', review_id: id });
  });
  it.each([{ ready: false }, { detail: { ...detail, dependency_stale: true } },
    { detail: { ...detail, summary: { ...detail.summary, review_status: 'stale' } } }])(
    'blocks finalization when prerequisites are not current: %j', (overrides) => {
      mount(overrides);
      fireEvent.click(screen.getByLabelText(/I confirm/));
      expect(screen.getByRole('button', { name: 'Finalize intake' })).toBeDisabled();
    });
  it('offers only the original retry while outcome is unknown', () => {
    const { save } = mount({ section: { ...initialSection({}), status: 'unknown',
      command: { key: id, path: `/intakes/${id}/finalizations`, body: {}, generation: 0 } }, locked: true });
    fireEvent.click(screen.getByRole('button', { name: /Retry/ }));
    expect(save).toHaveBeenCalledWith();
    expect(screen.queryByRole('button', { name: 'Finalize intake' })).not.toBeInTheDocument();
  });
});

function SpanishToggle() { const { toggleLanguage } = useLanguage(); return <button onClick={toggleLanguage}>Español</button>; }
it('provides Spanish confirmation and selection controls', () => {
  render(<LanguageProvider><SpanishToggle /><IntakeCanonical detail={detail} section={initialSection({})}
    ready locked={false} change={vi.fn()} save={vi.fn()} /></LanguageProvider>);
  fireEvent.click(screen.getByRole('button', { name: 'Español' }));
  expect(screen.getByRole('button', { name: 'Buscar registros existentes' })).toBeInTheDocument();
  fireEvent.click(screen.getByLabelText(/Confirmo/));
  expect(screen.getByRole('button', { name: 'Finalizar admisión' })).toBeEnabled();
});
it('requires explicit choices for every business child and preserves parent versions', async () => {
  const spy = vi.spyOn(discovery, 'discover').mockResolvedValue({ ok: true, value: {
    items: [{ id, version: 5, label: 'Fictional business', employerType: 'business' }], next_cursor: null } });
  function Stateful() {
    const [section, setSection] = useState(initialSection({}));
    return <IntakeCanonical detail={{ ...detail, summary: { ...detail.summary, kind: 'employer' } }}
      section={section} ready locked={false} change={(value) => { setSection({ ...section, value, status: 'unsaved' }); }} save={vi.fn()} />;
  }
  render(<LanguageProvider><Stateful /></LanguageProvider>);
  fireEvent.change(screen.getByLabelText('Name to search'), { target: { value: 'Fictional' } });
  fireEvent.click(screen.getByRole('button', { name: 'Search existing records' }));
  await screen.findByRole('option', { name: /Fictional business/ });
  fireEvent.change(screen.getByLabelText('Choose explicitly'), { target: { value: id } });
  expect(screen.getByRole('button', { name: 'Save selection' })).toBeDisabled();
  for (const title of ['Contact', 'Worksite', 'Business address']) {
    const group = screen.getByRole('group', { name: title });
    fireEvent.change(within(group).getByLabelText('Choose explicitly'), { target: { value: 'new' } });
  }
  await waitFor(() => { expect(screen.getByRole('button', { name: 'Save selection' })).toBeEnabled(); });
  expect(screen.getAllByText(/Version 5/).length).toBeGreaterThan(0);
  spy.mockRestore();
});
