import { act, fireEvent, render, screen, within, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { IntakeHistory } from './IntakeHistory';
import { LanguageProvider, useLanguage } from '../i18n/LanguageProvider';
import * as api from '../api/intakeClient';
import type { Result, RestrictedHistory } from '../api/intakeContracts';
import { runAxe } from '../test/axe';
vi.mock('../api/intakeClient');
const id = 'bda61d25-4021-4d8a-9f5d-9b77ad6c351f';
const event = {
  event_id: id,
  version: 2,
  content_version: 1,
  event_type: 'intake.follow_up_recorded',
  actor_id: id,
  actor_display_name: 'Fictional recorder',
  occurred_at: '2026-09-14T12:00:00Z',
  owner_staff_id: id,
  next_follow_up_at: '2026-09-15T12:00:00Z',
  outcome: 'no_answer',
};
function LanguageSwitch() {
  const { toggleLanguage } = useLanguage();
  return <button onClick={toggleLanguage}>Language</button>;
}
function mount() {
  return render(
    <LanguageProvider>
      <LanguageSwitch />
      <IntakeHistory id={id} version={2} />
    </LanguageProvider>,
  );
}
beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(api.queryIntakeHistory).mockResolvedValue({
    ok: true,
    value: { items: [event], next_cursor: 'next' },
  });
  vi.mocked(api.getRestrictedHistory).mockResolvedValue({
    ok: true,
    value: {
      event_id: id,
      note: 'Fictional restricted note',
      reviewed_content: {
        kind: 'worker',
        content: { full_name: 'Fictional person', nullable: null },
        addresses: { worker_residence: { line1: 'Fictional street' } },
      },
    },
  });
});
describe('shared intake history', () => {
  it('shows follow-up history without granting private ownership', async () => {
    const view = mount();
    await screen.findByText(/Fictional recorder/);
    expect(screen.queryByText('Fictional restricted note')).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Load restricted history' }));
    await screen.findByText('Fictional restricted note');
    expect(screen.getByText('Fictional street')).toBeInTheDocument();
    expect(await runAxe(view.container)).toEqual([]);
    fireEvent.click(screen.getByRole('button', { name: 'Language' }));
    expect(screen.getByRole('region', { name: 'Historial del registro' })).toBeInTheDocument();
    expect(await runAxe(view.container)).toEqual([]);
    fireEvent.click(screen.getByRole('button', { name: 'Ocultar historial restringido' }));
    expect(screen.queryByText('Fictional restricted note')).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Página siguiente' }));
    await waitFor(() => {
      expect(api.queryIntakeHistory).toHaveBeenLastCalledWith(id, 'next');
    });
  });
  it('clears revealed values before rechecking permission and treats denied as unavailable', async () => {
    mount();
    fireEvent.click(await screen.findByRole('button', { name: 'Load restricted history' }));
    await screen.findByText('Fictional restricted note');
    vi.mocked(api.getRestrictedHistory).mockResolvedValue({ ok: false, failure: 'forbidden' });
    fireEvent.click(screen.getByRole('button', { name: 'Load restricted history' }));
    await screen.findByText('Unavailable. No protected values are shown.');
    expect(screen.queryByText('Fictional street')).not.toBeInTheDocument();
  });
  it('ignores a late protected response after hiding or pagehide and does not steal focus', async () => {
    let resolve!: (value: Result<RestrictedHistory>) => void;
    const pending = new Promise<Result<RestrictedHistory>>((r) => {
      resolve = r;
    });
    vi.mocked(api.getRestrictedHistory).mockReturnValue(pending);
    mount();
    fireEvent.click(await screen.findByRole('button', { name: 'Load restricted history' }));
    fireEvent.click(screen.getByRole('button', { name: 'Hide restricted history' }));
    const button = screen.getByRole('button', { name: 'Language' });
    button.focus();
    await act(async () => {
      resolve({ ok: true, value: { event_id: id, note: 'Late note' } });
      await pending;
    });
    expect(screen.queryByText('Late note')).not.toBeInTheDocument();
    expect(button).toHaveFocus();
    act(() => {
      window.dispatchEvent(new Event('pagehide'));
    });
    expect(screen.queryByText(/Fictional recorder/)).not.toBeInTheDocument();
  });
  it('shows empty and unavailable metadata pages without protected values', async () => {
    vi.mocked(api.queryIntakeHistory).mockResolvedValueOnce({
      ok: true,
      value: { items: [], next_cursor: null },
    });
    const view = mount();
    await screen.findByText('No history yet.');
    view.unmount();
    vi.mocked(api.queryIntakeHistory).mockResolvedValueOnce({ ok: false, failure: 'forbidden' });
    mount();
    await screen.findByText('Unavailable. No protected values are shown.');
  });
  it('reveals absent note without inventing a note and removes values when pagination fails', async () => {
    vi.mocked(api.getRestrictedHistory).mockResolvedValue({ ok: true, value: { event_id: id } });
    mount();
    fireEvent.click(await screen.findByRole('button', { name: 'Load restricted history' }));
    await screen.findByText('No note recorded.');
    vi.mocked(api.queryIntakeHistory).mockResolvedValue({ ok: false, failure: 'failed' });
    fireEvent.click(screen.getByRole('button', { name: 'Next page' }));
    await screen.findByText('Unavailable. No protected values are shown.');
    expect(within(screen.getByRole('region')).queryByText('No note recorded.')).not.toBeInTheDocument();
  });
});
it.each(['needs_follow_up', 'attempt'] as const)(
  'shows localized protected %s context separately from note and snapshot',
  async (action) => {
    vi.mocked(api.getRestrictedHistory).mockResolvedValue({
      ok: true,
      value: {
        event_id: id,
        note: 'Separate fictional note',
        follow_up: {
          action,
          reason_code: 'missing_information',
          reason_text: 'Fictional reason',
          time_zone: 'Etc/UTC',
          ...(action === 'attempt' ? { method: 'phone' as const, outcome: 'no_answer' } : {}),
        },
        reviewed_content: {
          kind: 'worker',
          content: {
            interests: { selections: [{ interest_id: id, catalog_version: 1 }] },
            availability: { mode: 'weekly' },
            offer: { per_worker: true, negotiable: false },
          },
          addresses: {},
        },
      },
    });
    mount();
    fireEvent.click(await screen.findByRole('button', { name: 'Load restricted history' }));
    await screen.findByText('Fictional reason');
    expect(screen.getByText('Separate fictional note')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Language' }));
    expect(screen.getByText('Categoría del motivo')).toBeInTheDocument();
    expect(screen.getByText('Semanal')).toBeInTheDocument();
    if (action === 'attempt') expect(screen.getByText('Método de contacto')).toBeInTheDocument();
    else expect(screen.getByText('Requiere seguimiento')).toBeInTheDocument();
  },
);
