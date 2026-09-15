import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { useState } from 'react';
import { beforeEach, expect, it, vi } from 'vitest';
import { WorkInterestCatalog, WorkInterestPicker } from './WorkInterests';
import { LanguageProvider, useLanguage } from '../i18n/LanguageProvider';
import * as api from '../api/intakeClient';
import type { DraftObject, CatalogResult, Result } from '../api/intakeContracts';
import { runAxe } from '../test/axe';
vi.mock('../api/intakeClient');
const id = 'bda61d25-4021-4d8a-9f5d-9b77ad6c351f';
const entry = {
  interest_id: id,
  version: 2,
  code: 'fictional',
  label_en: 'Fictional interest',
  label_es: 'Interés ficticio',
  active: true,
};
function LanguageSwitch() {
  const { toggleLanguage } = useLanguage();
  return <button onClick={toggleLanguage}>Language</button>;
}
function Picker() {
  const [value, change] = useState<DraftObject>({
    selections: [{ interest_id: id, catalog_version: 1 }],
  });
  return (
    <>
      <WorkInterestPicker value={value} change={change} />
      <output aria-label="Version">
        {Array.isArray(value.selections) ? value.selections.length : 0}
      </output>
    </>
  );
}
function mount(picker = false) {
  return render(
    <LanguageProvider>
      <LanguageSwitch />
      {picker ? <Picker /> : <WorkInterestCatalog />}
    </LanguageProvider>,
  );
}
beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(api.queryWorkInterests).mockResolvedValue({
    ok: true,
    value: { items: [entry], next_cursor: 'next' },
  });
  vi.mocked(api.saveWorkInterest).mockImplementation((command) =>
    Promise.resolve({
      ok: true,
      value: { command_id: command.key, result_record_version: 2, current: entry },
    }),
  );
});
it('preserves historical catalog versions until explicit reselect and handles retired entries', async () => {
  const view = mount(true);
  await screen.findByLabelText('Common agency position');
  expect(screen.getByText(/Retained selection/)).toHaveTextContent('1');
  fireEvent.change(screen.getByLabelText('Common agency position'), { target: { value: id } });
  fireEvent.click(screen.getByRole('button', { name: 'Add position' }));
  expect(screen.queryByText(/Retained selection/)).not.toBeInTheDocument();
  fireEvent.click(screen.getByRole('button', { name: 'Remove selection' }));
  expect(screen.getByLabelText('Version')).toHaveTextContent('0');
  vi.mocked(api.queryWorkInterests).mockResolvedValue({
    ok: true,
    value: { items: [{ ...entry, active: false }], next_cursor: null },
  });
  fireEvent.click(screen.getByRole('button', { name: 'Next page' }));
  await waitFor(() => {
    expect(screen.getByLabelText('Common agency position')).toBeDisabled();
  });
  fireEvent.click(screen.getByRole('button', { name: 'Language' }));
  expect(screen.getByLabelText('Puesto común de la agencia')).toBeInTheDocument();
  expect(await runAxe(view.container)).toEqual([]);
});
it('removes historical selection explicitly and reports catalog read denial', async () => {
  vi.mocked(api.queryWorkInterests).mockResolvedValue({ ok: false, failure: 'forbidden' });
  mount(true);
  await screen.findByText('Unavailable. No protected values are shown.');
  fireEvent.click(screen.getByRole('button', { name: 'Remove selection' }));
  expect(screen.getByLabelText('Version')).toHaveTextContent('0');
  act(() => {
    window.dispatchEvent(new Event('pagehide'));
  });
});
it('creates and revises bilingual catalog entries using immutable commands and version checks', async () => {
  const view = mount();
  await screen.findByRole('button', { name: 'Revise interest' });
  fireEvent.change(screen.getByLabelText('Immutable code'), { target: { value: 'fictional' } });
  fireEvent.change(screen.getByLabelText('English label'), { target: { value: 'Fictional interest' } });
  fireEvent.change(screen.getByLabelText('Spanish label'), { target: { value: 'Interés ficticio' } });
  fireEvent.click(screen.getByRole('button', { name: 'Save catalog entry' }));
  await waitFor(() => {
    expect(api.saveWorkInterest).toHaveBeenCalledTimes(1);
  });
  expect(vi.mocked(api.saveWorkInterest).mock.calls[0]?.[0].body).toEqual({
    code: 'fictional',
    label_en: 'Fictional interest',
    label_es: 'Interés ficticio',
  });
  fireEvent.click(screen.getByRole('button', { name: 'Revise interest' }));
  fireEvent.click(screen.getByLabelText('Active'));
  fireEvent.change(screen.getByLabelText('Spanish label'), { target: { value: 'Retirado ficticio' } });
  fireEvent.click(screen.getByRole('button', { name: 'Save catalog entry' }));
  await waitFor(() => {
    expect(api.saveWorkInterest).toHaveBeenCalledTimes(2);
  });
  expect(vi.mocked(api.saveWorkInterest).mock.calls[1]?.[0].body).toEqual({
    expected_version: 2,
    label_en: 'Fictional interest',
    label_es: 'Retirado ficticio',
    active: false,
  });
  fireEvent.click(screen.getByRole('button', { name: 'Language' }));
  expect(screen.getByRole('button', { name: 'Guardar entrada del catálogo' })).toBeInTheDocument();
  expect(await runAxe(view.container)).toEqual([]);
  fireEvent.click(screen.getByRole('button', { name: 'Crear interés' }));
  expect(screen.getByLabelText('Código inmutable')).toHaveValue('');
});
it('retries an unknown catalog command exactly and preserves later edits', async () => {
  vi.mocked(api.saveWorkInterest).mockResolvedValueOnce({ ok: false, failure: 'unknown' });
  mount();
  await screen.findByRole('button', { name: 'Revise interest' });
  fireEvent.click(screen.getByRole('button', { name: 'Revise interest' }));
  fireEvent.change(screen.getByLabelText('English label'), { target: { value: 'Original' } });
  fireEvent.click(screen.getByRole('button', { name: 'Save catalog entry' }));
  await screen.findByRole('button', { name: 'Retry original save' });
  fireEvent.change(screen.getByLabelText('English label'), { target: { value: 'Later' } });
  fireEvent.click(screen.getByRole('button', { name: 'Retry original save' }));
  await waitFor(() => {
    expect(api.saveWorkInterest).toHaveBeenCalledTimes(2);
  });
  expect(vi.mocked(api.saveWorkInterest).mock.calls[0]?.[0]).toBe(
    vi.mocked(api.saveWorkInterest).mock.calls[1]?.[0],
  );
  expect(screen.getByLabelText('English label')).toHaveValue('Later');
});
it.each(['forbidden', 'conflict', 'failed'] as const)(
  'handles catalog %s without claiming a save',
  async (failure) => {
    vi.mocked(api.saveWorkInterest).mockResolvedValue({ ok: false, failure });
    mount();
    await screen.findByRole('button', { name: 'Revise interest' });
    fireEvent.click(screen.getByRole('button', { name: 'Revise interest' }));
    fireEvent.click(screen.getByRole('button', { name: 'Save catalog entry' }));
    await waitFor(() => {
      expect(api.saveWorkInterest).toHaveBeenCalled();
    });
    if (failure === 'forbidden') await screen.findByText('Unavailable. No protected values are shown.');
    else if (failure === 'conflict')
      expect(await screen.findByRole('button', { name: 'Save catalog entry' })).toBeDisabled();
    else await screen.findByText('Not saved. Check the entered values and try again.');
  },
);
it('blocks a newer catalog replay baseline, handles pagination failure, and clears pagehide buffers', async () => {
  vi.mocked(api.saveWorkInterest).mockResolvedValue({
    ok: true,
    value: { command_id: id, result_record_version: 1, current: entry },
  });
  mount();
  await screen.findByRole('button', { name: 'Revise interest' });
  fireEvent.click(screen.getByRole('button', { name: 'Revise interest' }));
  fireEvent.click(screen.getByRole('button', { name: 'Save catalog entry' }));
  await waitFor(() => {
    expect(screen.getByRole('button', { name: 'Save catalog entry' })).toBeDisabled();
  });
  vi.mocked(api.queryWorkInterests).mockResolvedValue({ ok: false, failure: 'failed' });
  fireEvent.click(screen.getByRole('button', { name: 'Next page' }));
  await screen.findByText('Unavailable. No protected values are shown.');
  act(() => {
    window.dispatchEvent(new Event('pagehide'));
  });
  expect(screen.getByLabelText('English label')).toHaveValue('');
});
it('discards pending catalog success after unmount', async () => {
  let resolve!: (value: Result<CatalogResult>) => void;
  const pending = new Promise<Result<CatalogResult>>((r) => {
    resolve = r;
  });
  vi.mocked(api.saveWorkInterest).mockReturnValue(pending);
  const view = mount();
  await screen.findByRole('button', { name: 'Revise interest' });
  fireEvent.click(screen.getByRole('button', { name: 'Save catalog entry' }));
  view.unmount();
  await act(async () => {
    resolve({ ok: true, value: { command_id: id, result_record_version: 2, current: entry } });
    await pending;
  });
});
it('retains unknown command when a catalog response identifies another entry', async () => {
  vi.mocked(api.saveWorkInterest).mockResolvedValue({
    ok: true,
    value: {
      command_id: id,
      result_record_version: 2,
      current: { ...entry, interest_id: 'f76bf415-6b21-4fbd-9639-28b9b3374411' },
    },
  });
  mount();
  await screen.findByRole('button', { name: 'Revise interest' });
  fireEvent.click(screen.getByRole('button', { name: 'Revise interest' }));
  fireEvent.click(screen.getByRole('button', { name: 'Save catalog entry' }));
  await screen.findByRole('button', { name: 'Retry original save' });
  expect(screen.getByRole('button', { name: 'Create interest' })).toBeDisabled();
});
it('retains loaded active selection metadata across catalog pages', async () => {
  mount(true);
  await screen.findByLabelText('Common agency position');
  fireEvent.change(screen.getByLabelText('Common agency position'), { target: { value: id } });
  fireEvent.click(screen.getByRole('button', { name: 'Add position' }));
  vi.mocked(api.queryWorkInterests).mockResolvedValue({
    ok: true,
    value: {
      items: [
        { ...entry, interest_id: 'f76bf415-6b21-4fbd-9639-28b9b3374411', label_en: 'Second interest' },
      ],
      next_cursor: null,
    },
  });
  fireEvent.click(screen.getByRole('button', { name: 'Next page' }));
  await screen.findByRole('option', { name: 'Second interest' });
  expect(screen.getAllByText(/Fictional interest/).length).toBeGreaterThan(0);
  expect(screen.queryByText(/choose a current active catalog version/)).not.toBeInTheDocument();
});
it('distinguishes a saved unqueried catalog selection from a confirmed stale entry', async () => {
  vi.mocked(api.queryWorkInterests).mockResolvedValueOnce({
    ok: true,
    value: { items: [], next_cursor: 'next' },
  });
  mount(true);
  await screen.findByRole('button', { name: 'Next page' });
  expect(screen.getByText(/Current catalog entry not loaded/)).toBeInTheDocument();
  expect(screen.queryByText(/choose a current active catalog version/)).not.toBeInTheDocument();
  vi.mocked(api.queryWorkInterests).mockResolvedValue({
    ok: true,
    value: { items: [entry], next_cursor: null },
  });
  fireEvent.click(screen.getByRole('button', { name: 'Next page' }));
  await screen.findByRole('option', { name: 'Fictional interest' });
  expect(screen.getByText(/choose a current active catalog version/)).toBeInTheDocument();
});
